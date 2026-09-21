# Authentication & Identity Architecture

This document describes the high-level security architecture, data flows, and design principles governing **User Registration**, **Authentication (Sign-In)**, and **Password Recovery** within Finnie AI.

---

## 🏛️ 1. Core Security Principles

Finnie AI follows defense-in-depth principles aligned with fintech industry standards (NIST SP 800-63B, OWASP ASVS, and FINRA data protection guidelines):

1. **Zero Plaintext Credentials**:
   - Plaintext passwords and one-time verification codes are never stored, logged, or cached in plaintext anywhere in the system.
   - All credentials are transformed using salted, computationally hard one-way cryptographic hash functions (`bcrypt`).
2. **Session-Scoped Token Storage**:
   - Auth tokens are scoped to active browser tabs using browser `sessionStorage`.
   - Closing a browser tab terminates access; opening a new tab requires re-authentication, preventing unauthorized access on shared devices.
3. **Stateless JWT with Instant Revocation**:
   - Authentication tokens are digitally signed JSON Web Tokens (JWT).
   - Each user profile carries an internal `token_version`. Incrementing this version revokes all existing sessions across all devices simultaneously without requiring a stateful server-side session table.
4. **Strict Multi-Tenant Isolation**:
   - User identity is derived exclusively from the verified JWT cryptographically validated on the server.
   - Client requests cannot spoof or inject arbitrary user IDs; every database query is strictly scoped to `effective_id = current_user.id`.
5. **Enumeration Resistance**:
   - All public endpoints (login, forgot-password) return consistent responses and status codes regardless of whether an email address is registered, blocking account harvesting attacks.

---

## 📝 2. User Registration Design

```text
[ Client (Browser) ]                          [ FastAPI Backend ]               [ Database (SQL) ]
        │                                              │                                │
        │─── 1. POST /auth/register ──────────────────►│                                │
        │    (Full Name, Email, Password)              │─── 2. Normalize email ────────►│ (Check duplicate)
        │                                              │                                │
        │                                              │─── 3. Salt & Hash Password ───►│ (Bcrypt)
        │                                              │                                │
        │                                              │─── 4. Commit User Record ─────►│ INSERT INTO users
        │                                              │                                │
        │                                              │─── 5. Issue JWT Access Token ──│
        │◄── 6. 200 OK (Token + User Profile) ─────────│                                │
        │                                                                               │
[ Save token to sessionStorage ]                                                        │
[ Open authenticated Dashboard ]                                                        │
```

### Key Registration Invariants
- **Email Normalization**: Emails are stripped of leading/trailing whitespace and normalized to lowercase before validation and storage.
- **Immediate Auto-Login**: Upon successful creation, the backend generates an initial JWT session token, eliminating redundant login steps for first-time users.
- **Tenant Anchor Creation**: A UUID primary key is generated upon registration and acts as the relational anchor for all portfolio holdings, financial goals, and chat interactions.

---

## 🔑 3. User Sign-In & Session Lifecycle

```text
[ Client (Browser) ]                          [ FastAPI Backend ]               [ Database (SQL) ]
        │                                              │                                │
        │─── 1. POST /auth/login ─────────────────────►│                                │
        │    (Email, Password)                         │─── 2. Query User by Email ────►│ SELECT FROM users
        │                                              │                                │
        │                                              │─── 3. Verify Hash (Bcrypt) ────│
        │                                              │                                │
        │                                              │─── 4. Check token_version ─────│
        │                                              │                                │
        │                                              │─── 5. Issue Signed JWT ────────│
        │◄── 6. 200 OK (Token + User Profile) ─────────│                                │
```

### Session Protection & Termination Flow
1. **Login Gate Mode**: Unauthenticated users are presented with a focused, backdrop-blurred authentication gate that completely hides private views.
2. **Explicit Sign Out**: Clicking "Sign Out" purges all active session keys from client storage and transitions to an exit confirmation screen (*"See you soon! 👋"*), confirming that financial data is securely protected.
3. **Session Rehydration**: On active page reloads within the same tab, the frontend validates the session token against `/auth/me` to refresh the user profile.

---

## 🔒 4. Password Recovery & Security Audit Design

The password recovery mechanism uses a **6-digit cryptographic One-Time Passcode (OTP)** paired with an **immutable security audit trail**.

```text
                                  PASSWORD RECOVERY LIFECYCLE
                                  
[ STEP 1: REQUEST CODE ]
User enters email ──► POST /auth/forgot-password ──► Check rate limit (max 3/15m)
                                                 ──► Generate 6-digit CSPRNG OTP
                                                 ──► Store salted hash in password_reset_audits
                                                 ──► Capture request_ip & requested_at
                                                 ──► Generic HTTP 200 (No email leakage)

                                           │
                                           ▼
[ STEP 2: VERIFY & RESET ]
User enters:
• 6-digit code
• New password (min. 8 chars) ──► POST /auth/reset-password
                                                 │
                                                 ├── Exceeded 15m TTL? ──► HTTP 400 (Expired)
                                                 ├── Incorrect code?   ──► Increment attempts (max 3)
                                                 ├── Same as old pass? ──► HTTP 400 (Cannot reuse)
                                                 │
                                                 ▼
                                           [ SUCCESS ]
                                           • Hash new password
                                           • Increment user.token_version (Revokes old sessions)
                                           • Mark audit status = "COMPLETED"
                                           • Capture completed_at, completed_ip, user_agent
                                           • Prompt user to log in with new credentials
```

### Forensic & Security Telemetry
The `password_reset_audits` entity records comprehensive forensics for account monitoring:

| Audit Dimension | Purpose |
| :--- | :--- |
| **Origin Telemetry (`request_ip`, `request_location`)** | Records where the reset request originated. |
| **Completion Telemetry (`completed_ip`, `completed_location`)** | Records where the password was finalized (flags geographic anomalies). |
| **Attempt Tracking (`attempts`)** | Captures incorrect guess counts; automatically locks the code after 3 consecutive failures. |
| **Status State Machine (`status`)** | Implements transitions: `PENDING` ➔ `COMPLETED` / `EXPIRED` / `FAILED`. |
| **Session Invalidation (`token_version`)** | Ensures that any device holding an active session is immediately logged out upon password reset. |

---

## 🛡️ 5. Non-Functional & Operational Guarantees

- **Dual-Environment Dispatch**:
  - In local development and automated testing suites, codes are emitted to application dev logs to maintain 100% offline autonomy.
  - In cloud/production environments, codes are dispatched via secure email transport.
- **Fail-Fast Defense**: Invalid or brute-force attempts are terminated at the API gateway layer before any expensive database or cryptographic operations are processed.
- **Zero Cross-Contamination**: Password reset telemetry is physically partitioned from primary account profile tables, allowing clean retention policies and audit compliance.
