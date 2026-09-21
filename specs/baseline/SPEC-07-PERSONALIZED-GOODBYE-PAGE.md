# Feature Spec: SPEC-07 — Goodbye Confirmation Page & Session Termination Flow

> **Status**: 🟢 **VERIFIED BASELINE**  
> **Author**: Antigravity AI  
> **Scope**: Frontend Auth Layer (`AuthContext`, `GoodbyeScreen`, `AuthModal`, `App.tsx`)  
> **Target Release**: v0.2.1  
> **Verification Date**: 2026-09-20  

---

## 1. 🎯 Business Objective & Domain Rules

### Problem Statement
When a user clicks "Sign Out", immediately popping up a raw credential form is jarring and provides no positive visual confirmation that their session was successfully terminated. Users need reassuring confirmation that their financial information and portfolio data are stored securely, paired with a simple, friendly exit experience.

### Domain Rules & Invariants
1. **Positive Session Termination**: Upon clicking "Sign Out", render a dedicated, elegant Goodbye confirmation view instead of immediately popping up the credential input form.
2. **Friendly & Generic Reassurance**:
   - Heading: *"See you soon! 👋"*
   - Body: *"You have successfully signed out. Your financial information and portfolio data are stored securely."*
   - Security Status Badge: *"🔒 Session ended securely · All data protected"*
3. **Session Purge Guarantee**: All `sessionStorage` tokens and `localStorage` keys are wiped before the Goodbye screen is displayed.
4. **Single Primary Action**: A single, prominent **`[ 🔑 Log In ]`** button that opens the Login modal when clicked.
5. **Shared Computer Security Tip**: Reassure users with a clean note: *"💡 Security Tip: Close your browser tab if you are on a shared computer"*.
6. **Fresh Tab / Browser Independence**: If a user opens a brand-new browser tab or window, they are presented with the standard login gate.

---

## 2. 🎨 Visual Design & Layout

```text
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                            ( 👤 )                           │  <-- Frosted Cyan Avatar
│                                                             │
│                      See you soon! 👋                       │  <-- Friendly Greeting
│                                                             │
│     You have successfully signed out. Your financial        │  <-- Secure Reassurance
│       information and portfolio data are stored securely.   │
│                                                             │
│     ┌─────────────────────────────────────────────────┐     │
│     │ 🔒 Session ended securely · All data protected  │     │  <-- Security Badge
│     └─────────────────────────────────────────────────┘     │
│                                                             │
│                       [ 🔑 Log In ]                         │  <-- Single Primary CTA
│                                                             │
│       💡 Security Tip: Close your browser tab if you        │
│                 are on a shared computer                    │
│                                                             │
│        🔒 256-Bit TLS · Not Financial Advice ($NFA)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 🔌 Technical Architecture & State Management

### A. Component Structure
```text
frontend/src/
├── components/
│   └── Auth/
│       ├── GoodbyeScreen.tsx       <-- [NEW] Friendly farewell screen
│       ├── GoodbyeScreen.css       <-- [NEW] Glass-Finance styling & ambient cyan glow
│       └── AuthModal.tsx           <-- Standard login modal
├── context/
│   └── AuthContext.tsx             <-- Track isSignedOut state on logout()
└── App.tsx                         <-- Render GoodbyeScreen when isSignedOut is true
```

### B. State Transitions & Lifecycle
1. When user clicks "Sign Out":
   - `logout()` in `AuthContext` purges `sessionStorage` and `localStorage`.
   - Sets `isSignedOut = true`.
   - `isAuthenticated` becomes `false`.
2. In `App.tsx`:
   - If `!isAuthenticated && isSignedOut`:
     - Render `<GoodbyeScreen onLogin={() => { setIsSignedOut(false); setIsAuthModalOpen(true); }} />`.
   - If user clicks **`[ 🔑 Log In ]`**:
     - `setIsSignedOut(false)` and open `AuthModal`.
3. In a fresh tab or page refresh:
   - `isSignedOut` defaults to `false`.
   - If unauthenticated, renders standard `AuthModal` login gate.

---

## 4. ✅ Acceptance Criteria & Verification Record

- [x] **AC-1 (Goodbye Screen Display)**: Clicking "Sign Out" in the sidebar footer renders the `GoodbyeScreen` with the friendly message *"See you soon! 👋"*.
- [x] **AC-2 (Secure Reassurance Copy)**: Displays *"You have successfully signed out. Your financial information and portfolio data are stored securely."* and *"🔒 Session ended securely · All data protected"*.
- [x] **AC-3 (Single Log In Button)**: Renders a single primary **`[ 🔑 Log In ]`** button; no secondary "sign in as another user" button.
- [x] **AC-4 (Log In Transition)**: Clicking **`[ 🔑 Log In ]`** smoothly opens the `AuthModal` login form.
- [x] **AC-5 (Token Purge Invariant)**: When `GoodbyeScreen` is displayed, both `sessionStorage` and `localStorage` contain 0 auth tokens.
- [x] **AC-6 (Automated Test Suite)**: Verified via automated integration tests in `frontend/src/components/Auth/__tests__/GoodbyeScreenFlow.test.tsx` and passed the full 3-step Sequential Verification Pipeline (`uv run python -m unittest` ➔ `npm test` ➔ `npm run build`).
