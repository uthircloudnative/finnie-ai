# UX & Glass-Finance Design System Standards — Finnie AI

This document establishes the UI/UX design philosophy, accessibility requirements, and component state patterns for Finnie AI.

---

## 1. The "Glass-Finance" Aesthetic

Finnie AI delivers an institutional-grade, dark-mode financial experience combining cyber-financial precision with clean glassmorphism.

### Core Visual Principles:
1. **Curated Color Palette**:
   - Primary Brand Accent: Electric Cyan (`#00f3ff` / `var(--accent-cyan)`).
   - Card Surfaces: Deep charcoal frosted glass (`rgba(15, 23, 42, 0.65)`) with a subtle 1px border (`rgba(255, 255, 255, 0.08)`).
   - Semantic Status Badges:
     - 🟢 **Success / On Track**: `rgba(34, 197, 94, 0.15)` bg with `#4ade80` text.
     - 🟡 **Warning / Caution**: `rgba(234, 179, 8, 0.15)` bg with `#facc15` text.
     - 🔴 **Danger / At Risk**: `rgba(239, 68, 68, 0.15)` bg with `#f87171` text.
2. **Typography**:
   - Modern monospace and geometric sans-serif fonts from Google Fonts (Space Grotesk, Inter, Outfit).
   - Bold numerical metrics with clear units (`$`, `%`, `x`).
3. **No Unstyled Content**: Never show unformatted raw JSON, raw markdown tags (`###`, `**`), or raw database IDs to users.

---

## 2. Component State Patterns

Every analytical view, card, and interactive widget MUST handle the full component lifecycle:

### A. Loading States
- Long-running LLM workflows (Chat, Goal Generation, Portfolio Analysis) MUST display visual feedback:
  - Pulsing agent orb or glowing `ThinkingIndicator`.
  - Button text transitioning to an active state (e.g. `🧠 Calculating 10,000 Scenarios...`).
  - Skeleton cards or shimmer effects for data loading.

### B. Empty States
- When a user has zero holdings or has not yet configured a goal:
  - Never render an empty white/black void.
  - Display an illustrative icon (`📈`, `💼`, `🎯`).
  - Include friendly, explanatory copy and a direct Call-To-Action (CTA) button guiding the user to take action.

### C. Error & Fallback States
- If external financial APIs (yfinance, Alpha Vantage) fail or rate-limit:
  - Do NOT crash the entire page or show a generic 500 alert.
  - Display an interactive retry button on the affected card (e.g., `"📊 Get Diversification Score"` on the diversification tile).

---

## 3. Accessibility Standards (WCAG 2.1 AA)
1. **Contrast**: Ensure text color against dark glass backgrounds meets a minimum 4.5:1 contrast ratio.
2. **Focus Rings**: All interactive inputs, buttons, and country tabs must have visible, non-obscured focus indicators (`box-shadow: 0 0 12px rgba(0, 243, 255, 0.2)`).
3. **Semantic HTML**: Use proper `<button>`, `<input>`, `<nav>`, `<aside>`, `<main>` elements instead of clickable `<div>` wrappers.
4. **ARIA & Screen Readers**: Use `aria-live="polite"` for dynamic calculation updates and accessible labels on icon-only buttons.
