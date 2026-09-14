# Baseline Spec: SPEC-01 — Multi-Tenancy & User Authentication

> **Status**: 🟢 **VERIFIED & IN PRODUCTION**  
> **Scope**: Backend Auth Core, Tenant Isolation & Frontend Session

---

## 1. 🎯 Business Objective & Domain Rules
- **Problem**: Multi-user financial assistance requires absolute data privacy. Users must only access their own portfolios, goals, and chat histories without any cross-tenant data leakage.
- **Stateless Cloud Scaling**: Architecture adheres to 12-Factor principles; tokens must be cryptographically verified independently across distributed cloud workers (e.g. Azure App Service replicas) without server-side session stores.
- **Tenant Derivation Rule**: NEVER accept client-supplied `user_id` query parameters or JSON body fields for authorization. Always derive tenant identity from the decoded JWT Bearer token (`effective_id = current_user.id`).

---

## 2. 🔌 Technical Contracts & Endpoints

### A. Authentication Endpoints
- `POST /auth/register`: Takes `email`, `password`, `full_name`, `base_currency` ➔ Returns `access_token`, `token_type: "bearer"`, and `UserProfile`.
- `POST /auth/login`: Takes `email`, `password` ➔ Returns `access_token` and `UserProfile`.
- `GET /auth/me`: Requires `Authorization: Bearer <token>` ➔ Returns authenticated `UserProfile`.

### B. Security Implementation
- **JWT Signing**: HMAC-SHA256 via `python-jose` with environment secret `JWT_SECRET_KEY` (30-day token expiration).
- **Password Hashing**: Direct `bcrypt` hashing with salt (compatible with Python 3.13 without `passlib` version deprecation issues).
- **FastAPI Dependency**: `get_current_user` injected across `/portfolio`, `/dashboard`, `/chat`, `/portfolio/analysis`, `/market/news`, and `/goals`.

### C. Database Model (`backend/src/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"
    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name       = Column(String, nullable=False)
    base_currency   = Column(String, default="USD")
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

### D. Composite Database Constraints (`backend/src/models/portfolio.py`)
```python
__table_args__ = (
    UniqueConstraint("user_id", "ticker", "exchange", name="uq_user_ticker_exchange"),
)
```

---

## 3. 🖥️ Frontend Session Architecture
- **Context**: `AuthContext.tsx` stores `{ user, token, isAuthenticated, login, register, logout, getAuthHeaders }`.
- **Persistence**: Persists token in browser `localStorage`.
- **Header Injection**: All custom hooks (`usePortfolio`, `useCountryPortfolio`, `useDashboard`, `useGoalStrategist`, `useMarketInsights`, `useChat`) attach `Authorization: Bearer <token>` headers via `getAuthHeaders()`.
- **UI**: Sleek glassmorphic `AuthModal.tsx` supporting Sign In, Registration, and 1-Click Demo Login (`demo@finnie.ai`).

---

## 4. ✅ Verified Acceptance Criteria (Regression Baseline)
- [x] **AC-1**: Registering a user hashes the password with bcrypt (raw password never stored).
- [x] **AC-2**: User A and User B can both hold `AAPL` without primary key collisions or cross-user visibility.
- [x] **AC-3**: Requesting `/portfolio` without a Bearer token returns `401 Unauthorized`.
- [x] **AC-4**: Ingesting duplicate tickers in `POST /portfolio/save` consolidates quantities in memory without violating `uq_user_ticker_exchange`.
- [x] **AC-5**: Offline unit tests in `test_unit.py` (`test_password_hash_and_verify`, `test_jwt_create_and_decode`, `test_jwt_invalid_token`, `test_holding_unique_constraint`) pass cleanly.
