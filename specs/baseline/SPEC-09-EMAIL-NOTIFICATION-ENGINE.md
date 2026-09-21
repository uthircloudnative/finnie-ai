# Feature Spec: SPEC-09 — Reusable Email Notification Engine & Mailgun Dispatch Architecture

> **Status**: 🟢 **PROD-VERIFIED**  
> **Author**: Antigravity AI  
> **Scope**: Backend Core (`backend/src/utils/`, `backend/src/templates/`, `backend/main.py`, `backend/tests/`)  
> **Target Release**: v0.2.3  

---

## 1. 🎯 Business Objective & Domain Rules

### Problem Statement
Finnie AI requires a robust, extensible, and professional notification engine to deliver transactional emails to users. The initial critical use case is the delivery of One-Time Verification Codes (OTPs) for password recovery ([SPEC-08](file:///Users/prajosh/Development/finnie-ai/specs/baseline/SPEC-08-FORGOT-PASSWORD-FLOW.md)). The system must also be designed as a general-purpose email utility supporting future notifications (e.g., account registration welcomes, portfolio rebalancing alerts, security anomalies, and market digest reports) without rewriting transport logic.

### Domain Rules & Security Invariants
1. **Zero Exposure of Sensitive Credentials (Non-Negotiable)**:
   - Real API keys, subscription identifiers, domain hashes, and private personal emails MUST NEVER be committed to Git, hardcoded in source files, or logged in cleartext.
   - All credentials MUST be loaded strictly via runtime environment variables (`MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `MAILGUN_BASE_URL`, `MAILGUN_FROM_EMAIL`) originating from git-ignored `.env` files.
   - Runtime logs must mask recipient email addresses (e.g., `in***@finnie.ai`) and never log secret API keys or raw authorization headers.
2. **Provider-Agnostic Abstraction**:
   - The application core must interact with an abstract interface (`BaseEmailProvider`).
   - The concrete `MailgunEmailProvider` communicates via Mailgun's REST API using HTTP Basic Authentication (`api` : `MAILGUN_API_KEY`).
   - A `ConsoleEmailProvider` acts as an automatic fallback when Mailgun credentials are missing, in offline testing, or when sandbox domain restrictions reject delivery.
3. **Non-Blocking Fault Tolerance**:
   - Email dispatch failure (e.g., Mailgun API timeout, DNS failure, or 400 Sandbox unauthorized recipient error) MUST NOT crash the calling API request or reveal server internals.
   - Errors are captured, logged defensively, and gracefully handled.
4. **Professional Dark/Glass Visual Branding & Email Client Compatibility**:
   - Transactional emails must reflect Finnie AI's sleek fintech design system (deep navy `#0b0f19`, cyan accent `#00f5ff`, subtle border `#1e293b`, clear typography).
   - Inlined CSS styles to ensure flawless rendering across major email clients (Gmail, Apple Mail, Outlook, iOS Mail, Android).
   - Every email must contain a plain-text fallback counterpart for accessibility and spam score optimization.
5. **Regulatory & Security Footers**:
   - Mandatory inclusion of:
     - Clear expiration warnings (e.g., "This code expires in 15 minutes").
     - Security notice: "If you did not request this verification code, please ignore this email. Your account remains secure."
     - Compliance disclaimer: "Finnie AI · Automated Notification · Not Financial Advice ($NFA)."

---

## 2. 🔌 Technical Contracts & Architecture

### A. Modular Component Architecture

```text
backend/src/utils/
├── email_service.py         # Factory, BaseEmailProvider, MailgunEmailProvider, ConsoleEmailProvider
└── templates/
    └── email/
        ├── otp_reset.html   # High-impact 6-digit OTP code block with security telemetry
        └── otp_reset.txt    # Plain-text OTP template
```

### B. Provider Interface & Contracts

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class EmailMessage:
    """Encapsulates outgoing email parameters."""
    to_email: str
    subject: str
    html_body: str
    text_body: str
    from_email: Optional[str] = None
    tags: Optional[list[str]] = None

class BaseEmailProvider(ABC):
    """Abstract interface for all notification dispatch transports."""
    @abstractmethod
    def send_email(self, message: EmailMessage) -> bool:
        pass

class MailgunEmailProvider(BaseEmailProvider):
    """Dispatches emails via Mailgun REST API (POST /v3/{domain}/messages)."""
    def __init__(self, api_key: str, domain: str, base_url: str = "https://api.mailgun.net", from_email: str = ""):
        self.api_key = api_key
        self.domain = domain
        self.base_url = base_url.rstrip("/")
        self.from_email = from_email or f"Finnie AI Security <postmaster@{domain}>"

    def send_email(self, message: EmailMessage) -> bool:
        ...

class ConsoleEmailProvider(BaseEmailProvider):
    """Development and offline testing provider that logs to stdout."""
    def send_email(self, message: EmailMessage) -> bool:
        ...
```

### C. Reusable Factory API

```python
class EmailService:
    """Singleton/utility facade invoked by business endpoints."""
    
    @classmethod
    def get_provider(cls) -> BaseEmailProvider:
        # Returns MailgunEmailProvider if MAILGUN_API_KEY and MAILGUN_DOMAIN exist,
        # else gracefully returns ConsoleEmailProvider.
        ...

    @classmethod
    def send_otp_reset_email(
        cls,
        to_email: str,
        otp_code: str,
        expiry_minutes: int = 15,
        location: str = "Unknown",
        user_name: Optional[str] = None
    ) -> bool:
        """Standard high-level helper for OTP password recovery."""
        ...
        
    @classmethod
    def send_custom_email(
        cls,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> bool:
        """Generic extensible helper for any future email notification."""
        ...
```

### D. Environment Configuration (`backend/.env`)

```bash
# ── Email Notification Engine (SPEC-09) ────────────────────────────────
MAILGUN_API_KEY="key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
MAILGUN_DOMAIN="sandboxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.mailgun.org"
MAILGUN_BASE_URL="https://api.mailgun.net"
MAILGUN_FROM_EMAIL="Finnie AI Security <postmaster@sandboxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.mailgun.org>"
```

---

## 3. 🎨 Professional Email Template Design

### A. Visual Tokens & Structure
- **Container**: Max width 560px, center-aligned, background `#0b0f19`, border `1px solid #1e293b`, radius `16px`.
- **Branding Badge**: Cyan accent badge (`#00f5ff`) with `"🤖 FINNIE AI SECURITY"`.
- **Hero Title**: Pure white `#ffffff`, 22px bold: `"Password Reset Verification Code"`.
- **Salutation**: `"Hello Investor,"` or personalized name if available.
- **OTP Presentation Box**:
  - Background: `rgba(0, 245, 255, 0.04)` with border `1px solid rgba(0, 245, 255, 0.25)`.
  - Font: Monospaced 34px bold, letter-spacing `8px`, centered, color `#00f5ff`.
  - Expiry notice: Subtitle badge `#94a3b8`: `"Valid for 15 minutes · One-time use only"`.
- **Security Telemetry Block**:
  - Displays: `"Request Origin: {request_location}"`.
  - Advisory: `"If you did not request this password reset, please change your credentials immediately or contact support."`
- **Compliance Footer**:
  - `"🔒 256-Bit TLS Encryption · Not Financial Advice ($NFA)"`.
  - Copyright and automated dispatch notice.

### B. Plain-Text Fallback
Formatted clean ASCII layout ensuring identical information accessibility on legacy text clients and terminal-based email readers.

---

## 4. 🛡️ Edge Cases, Failure Modes & Resilience

| Edge Case ID | Scenario | System Behavior |
| :--- | :--- | :--- |
| **EC-1** | **Missing Mailgun Keys** | If `MAILGUN_API_KEY` or `MAILGUN_DOMAIN` is not set, `EmailService` automatically falls back to `ConsoleEmailProvider` with zero errors. |
| **EC-2** | **Sandbox Recipient Rejection (HTTP 400)** | Recipient is not in Mailgun's Authorized Recipients list. Mailgun returns HTTP 400. Log masked warning to console, fall back to console OTP display, and return generic success to avoid leaking delivery failure to attacker. |
| **EC-3** | **Mailgun API Timeout / 5xx Outage** | Network timeout occurs (>5s). Catch exception, log warning, and allow the API endpoint to succeed without crashing. |
| **EC-4** | **Special Characters / Injection in Name/Email** | Sanitize and escape all dynamic template variables to prevent email header injection (`\r\n`) or HTML injection. |
| **EC-5** | **Offline Test Suite Execution** | Unit tests mock the Mailgun HTTP transport so `test_unit.py` passes 100% offline without reaching external Mailgun endpoints or consuming API quotas. |

---

## 5. ✅ Acceptance Criteria & Test Plan

### A. Automated Unit Tests (`backend/tests/test_unit.py`)
- [x] **AC-1 (Provider Initialization)**: `EmailService.get_provider()` selects `MailgunEmailProvider` when credentials exist and `ConsoleEmailProvider` when absent.
- [x] **AC-2 (Mailgun HTTP Dispatch)**: Mocked Mailgun API call sends correct Basic Auth header, form fields (`from`, `to`, `subject`, `text`, `html`), and succeeds on HTTP 200.
- [x] **AC-3 (Sandbox Rejection Resilience)**: When Mailgun returns HTTP 400 (Unauthorized recipient), provider captures error cleanly, logs masked warning, and does not crash.
- [x] **AC-4 (Template Placeholder Rendering)**: Email templates correctly interpolate `otp_code`, `expiry_minutes`, `location`, and recipient without unescaped tags.
- [x] **AC-5 (Privacy & Masking)**: Masking utility converts `investor@finnie.ai` to `in***@finnie.ai` in all logs. Zero secrets or raw API keys appear in test outputs or codebase.
- [x] **AC-6 (Endpoint Integration)**: `POST /auth/forgot-password` dispatches email through `EmailService` and records audit entry.

### B. Sequential Verification Pipeline
- [x] **AC-7**: Passes Step 1 (`uv run python -m unittest discover -s tests`) — 29/29 tests passed (100%).
- [x] **AC-8**: Passes Step 2 (`npm test`) — 7 suites / 20 tests passed (100%).
- [x] **AC-9**: Passes Step 3 (`npm run build`) with 0 errors and 0 warnings.

