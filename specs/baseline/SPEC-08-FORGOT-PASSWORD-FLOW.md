# Feature Spec: SPEC-08 — Password Reset via One-Time Verification Code (OTP) & Security Audit Trail

> **Status**: 🟢 **PROD-VERIFIED**  
> **Author**: Antigravity AI  
> **Scope**: Full-Stack (`backend/src/models/`, `backend/main.py`, `frontend/src/components/Auth/`, `frontend/src/context/`)  
> **Target Release**: v0.2.2  

---

## 1. 🎯 Business Objective & Domain Rules

### Problem Statement
Users who forget their credentials currently have no recovery path and are permanently locked out of their financial portfolios, goal trajectories, and chat histories. Finnie AI requires a secure, non-intrusive password recovery flow that complies with fintech security standards (NIST SP 800-63B, SOC 2, FINRA) without requiring external OAuth dependencies or forcing users to leave the application window.

### Domain Rules & Security Invariants
1. **Enumeration-Resistant Generic Response**:
   - Requesting a password reset for an unregistered email address MUST return the exact same generic success message: `"If an account is associated with this email, a verification code has been sent."`
   - Response time and status code (HTTP 200) must be uniform to prevent timing-based email harvesting.
2. **Cryptographic OTP Generation**:
   - Verification codes MUST be exactly 6 decimal digits (`100000` to `999999`) generated via a cryptographically secure pseudo-random number generator (`secrets.randbelow(900000) + 100000`).
   - Plaintext OTPs MUST NEVER be stored in the database. The database stores a salted one-way hash (`bcrypt`).
3. **Time-To-Live (TTL)**:
   - Reset codes expire strictly **15 minutes** after issuance (`requested_at + timedelta(minutes=15)`).
4. **Single-Use Invariant**:
   - An OTP can be redeemed exactly once. Upon successful password reset, `status = "COMPLETED"` and `completed_at = now` are committed immediately.
5. **Superseeded Code Invalidation**:
   - Requesting a new code for an account automatically marks any prior pending codes for that user as `status = "FAILED"`.
6. **Brute-Force & Attempt Capping**:
   - Each OTP allows a maximum of **3 failed verification attempts**. On the 3rd consecutive failure, the code is invalidated (`status = "FAILED"`), forcing the user to request a new code.
7. **Rate Limiting**:
   - A single email address can request at most **3 reset codes per 15-minute window** to prevent spamming and resource exhaustion.
8. **Dual-Origin Telemetry & Account Takeover (ATO) Detection**:
   - The system records both `request_ip` / `request_location` (where the OTP was generated) and `completed_ip` / `completed_location` (where the password was changed) to identify geographic anomalies.
9. **Active Session Revocation (`token_version`)**:
   - Each user maintains an integer `token_version`. Resetting the password increments `user.token_version += 1`, immediately invalidating all existing JWT sessions across all devices.
10. **Password Quality & Non-Recycling**:
    - New passwords must be at least **8 characters** long and cannot match the user's current password.
11. **Dual-Environment Dispatch Architecture**:
    - **Local / Dev / Test**: When no external email provider is configured, the backend logs the code to stdout:
      `[AUTH] 📧 Verification code for <email>: <OTP>`
    - **Cloud / Production**: Dispatches via SMTP/SendGrid/SES when environment variables are supplied.

---

## 2. 🔌 Technical Contracts & Architecture

### A. Database Schema

#### 1. Updated `User` Model (`backend/src/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"

    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name       = Column(String, nullable=False)
    base_currency   = Column(String, default="USD")
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    token_version   = Column(Integer, default=1, nullable=False)

    reset_audits    = relationship(
        "PasswordResetAudit", 
        back_populates="user", 
        cascade="all, delete-orphan",
        order_by="desc(PasswordResetAudit.requested_at)"
    )
```

#### 2. New `PasswordResetAudit` Model (`backend/src/models/password_reset.py`)
```python
class PasswordResetAudit(Base):
    __tablename__ = "password_reset_audits"

    id                 = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id            = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ── Security & Verification ──────────────────────────────────────────
    code_hash          = Column(String, nullable=False)
    status             = Column(String, default="PENDING", nullable=False)  # PENDING, COMPLETED, EXPIRED, FAILED
    attempts           = Column(Integer, default=0, nullable=False)
    
    # ── Precise UTC Timestamps ───────────────────────────────────────────
    requested_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at         = Column(DateTime(timezone=True), nullable=False)
    completed_at       = Column(DateTime(timezone=True), nullable=True)
    
    # ── Forensic Telemetry (Origin vs Completion) ────────────────────────
    request_ip         = Column(String, nullable=True)
    request_location   = Column(String, nullable=True)
    completed_ip       = Column(String, nullable=True)
    completed_location = Column(String, nullable=True)
    user_agent         = Column(String, nullable=True)
    
    user               = relationship("User", back_populates="reset_audits")
```

### B. REST API Endpoints

#### 1. `POST /auth/forgot-password`
- **Request Body**:
  ```python
  class ForgotPasswordRequest(BaseModel):
      email: EmailStr
  ```
- **Response Payload (HTTP 200)**:
  ```python
  class ForgotPasswordResponse(BaseModel):
      message: str = "If an account is associated with this email, a verification code has been sent."
      expires_in_minutes: int = 15
  ```
- **Rate Limit**: Max 3 requests per 15 minutes per email (returns `429 Too Many Requests`).

#### 2. `POST /auth/reset-password`
- **Request Body**:
  ```python
  class ResetPasswordRequest(BaseModel):
      email: EmailStr
      code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
      new_password: str = Field(..., min_length=8)
  ```
- **Response Payload (HTTP 200)**:
  ```python
  class ResetPasswordResponse(BaseModel):
      message: str = "Password has been successfully reset. Please sign in with your new password."
  ```
- **Errors**:
  - `400 Bad Request`: Code invalid, code expired, code already used, max attempts reached, or new password matches current password.
  - `422 Unprocessable Entity`: Password too short (<8 chars) or malformed 6-digit code.

---

## 3. 🖥️ Frontend Presentation & State Machine

### A. State Machine in `AuthModal.tsx`
```typescript
type AuthMode = 'login' | 'register' | 'forgot'
type ForgotStep = 'request_code' | 'verify_and_reset' | 'success'
```

### B. Sub-Views & Interaction Design
1. **`request_code`**: Email input + `"Send Verification Code"` + `"← Back to Sign In"`.
2. **`verify_and_reset`**:
   - 6-digit tracked OTP input.
   - New password + Confirm password inputs.
   - 60-second cooldown on `"Resend Code"`.
   - Client-side validation: Mismatched passwords and <8 chars blocked before API call.
3. **`success`**:
   - Green success badge: `"Password Reset Complete! 🎉"`.
   - Primary CTA: **`[ 🔑 Proceed to Sign In ]`** transitions smoothly back to `mode: 'login'` with email pre-filled.

---

## 4. 🛡️ Comprehensive Edge Cases & Failure Modes

| # | Edge Case | Trigger / Condition | Expected Defensive Behavior |
| :--- | :--- | :--- | :--- |
| **EC-1** | **Unregistered Email** | Attacker inputs `unknown@domain.com` | Return generic HTTP 200. Do NOT create DB record. Zero indication that email does not exist. |
| **EC-2** | **Expired OTP** | User submits code >15 minutes after generation | Return HTTP 400: `"Verification code has expired. Please request a new one."` Mark `status = "EXPIRED"`. |
| **EC-3** | **Wrong OTP (<3 attempts)** | User mistypes 1 digit | Increment `attempts`. Return HTTP 400 with remaining attempts count. |
| **EC-4** | **Brute-Force Lockout (3rd fail)** | User/bot fails 3 times | Mark `status = "FAILED"`. Block further attempts on that code. Return HTTP 400: `"Too many failed attempts. Code has been invalidated."` |
| **EC-5** | **Replay / Double Spend** | Submitting an already completed code | Query checks `status == "PENDING"`. Return HTTP 400: `"Code already used."` |
| **EC-6** | **Request Spamming** | >3 requests in 15 minutes | Return HTTP 429: `"Too many requests. Please wait before requesting another code."` |
| **EC-7** | **New Code Overwrite** | User requests code B while code A is pending | Code A marked `status = "FAILED"`. Only Code B is active. |
| **EC-8** | **Same Password Reuse** | User inputs their current password | Return HTTP 400: `"New password cannot be the same as your current password."` |
| **EC-9** | **Client Password Mismatch** | New Password != Confirm Password | Blocked client-side before network call: `"Passwords do not match."` |
| **EC-10** | **Session Zombie Invalidation** | User had active JWT on compromised device | `user.token_version += 1`. All previous JWTs immediately fail verification. |
| **EC-11** | **SQLite Timezone Comparison** | SQLite loads naive UTC datetime | Defensive normalizer attaches `timezone.utc` if missing before comparison. |
| **EC-12** | **Frontend Resend Spam** | User rapidly clicks "Resend Code" | 60-second client-side timer disables button with countdown. |
| **EC-13** | **Table Initialization** | Cold start of application | `PasswordResetAudit` imported into `init_db()` in `database.py`. |

---

## 5. ✅ Acceptance Criteria & Test Plan

### A. Backend Unit Tests (`backend/tests/test_unit.py`)
- [x] **AC-1 (Request Code Success)**: `POST /auth/forgot-password` with registered email creates hashed record in `password_reset_audits` with 15m expiry, records `request_ip`, and returns generic HTTP 200.
- [x] **AC-2 (Enumeration Defense)**: `POST /auth/forgot-password` with non-existent email returns HTTP 200 and creates 0 records.
- [x] **AC-3 (Reset Password Success)**: `POST /auth/reset-password` with valid OTP updates user's `hashed_password`, increments `token_version`, sets `status = "COMPLETED"`, records `completed_at` and `completed_ip`, and returns HTTP 200.
- [x] **AC-4 (Token Version Revocation)**: Previous JWT issued with `token_version = 1` is rejected after password reset increments version to `2`.
- [x] **AC-5 (Expired Code Rejection)**: Code created >15 minutes ago returns HTTP 400.
- [x] **AC-6 (Attempt Capping)**: 3 consecutive invalid code submissions mark code `status = "FAILED"` and lock it out.
- [x] **AC-7 (Same Password Rejection)**: Submitting current password returns HTTP 400.
- [x] **AC-8 (Rate Limiting)**: >3 requests for the same email within 15 minutes return HTTP 429.

### B. Frontend Integration Tests (`frontend/src/components/Auth/__tests__/AuthFlow.test.tsx`)
- [x] **AC-9 (UI Navigation)**: Clicking "Forgot password?" in Sign In view switches modal to `request_code` step.
- [x] **AC-10 (Email Step Transition)**: Submitting valid email transitions UI to `verify_and_reset` step.
- [x] **AC-11 (Client Password Validation)**: Displays error if new passwords do not match or are <8 characters without calling backend.
- [x] **AC-12 (Cooldown Timer)**: Resend button shows countdown and remains disabled for 60 seconds after request.
- [x] **AC-13 (Success Step Transition)**: Successful reset transitions to `success` step with "Proceed to Sign In" CTA.
- [x] **AC-14 (Back to Sign In)**: Clicking "← Back to Sign In" at any stage restores standard Login form.

### C. Sequential Verification Pipeline
- [x] **AC-15**: Passes Step 1 (`uv run python -m unittest discover -s tests`) — 22/22 tests passed (100%).
- [x] **AC-16**: Passes Step 2 (`npm test`) — 7 suites / 20 tests passed (100%).
- [x] **AC-17**: Passes Step 3 (`npm run build`) with 0 errors and 0 warnings.

