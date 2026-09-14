# Frontend & React Standards — Finnie AI

This document defines the mandatory code organization, state management, and type safety standards for the React 19 / TypeScript frontend.

---

## 1. Architecture & Separation of Concerns

Finnie AI enforces a strict separation between **business/API logic** and **presentational UI**:

```text
frontend/src/
├── components/   # Pure presentational components (receives props, renders JSX)
├── context/      # Session-wide context providers (AuthContext)
├── hooks/        # Custom hooks owning all data fetching, caching, mutations
└── config.ts     # Centralized API URLs and endpoint definitions
```

### Rules:
1. **No Network Calls in Components**: UI components (`Dashboard.tsx`, `GoalPlanner.tsx`, `PortfolioAnalyst.tsx`) MUST NEVER invoke `fetch()` directly. All HTTP requests, authentication headers, error states, and retry logic must live in dedicated custom hooks (`usePortfolio.ts`, `useGoalStrategist.ts`, etc.).
2. **Centralized Configuration**:
   - Hardcoded URLs like `'http://localhost:8000'` are strictly prohibited across components and hooks.
   - Always import `API_BASE` or `API_ENDPOINTS` from `src/config.ts`:
     ```typescript
     import { API_BASE } from '../config'
     ```
3. **Session Caching**:
   - When users switch between views or country tabs (e.g. `US` vs `India` in Portfolio Analyst), data should be cached in `useRef` or state maps to avoid redundant API trips.

---

## 2. TypeScript & Type Safety
- **Strict Typing**: Never use `any` for API response payloads. Define explicit TypeScript interfaces for all data structures:
  ```typescript
  export interface Holding {
    ticker: string
    shares: number
    country: string
    exchange: string
    added_date: string
  }
  ```
- **Zero Build Errors**: `npm run build` (`tsc -b && vite build`) must pass with **0 errors and 0 warnings** before any PR or commit.

---

## 3. Styling & Design Token Consistency
- **Design Tokens**: All styles must consume CSS custom properties defined in `src/styles/tokens.css`:
  - Accent: `var(--accent-cyan)` (`#00f3ff`)
  - Backgrounds: `var(--bg-card)`, `var(--glass-bg)`, `var(--glass-border)`
  - Typography: `var(--font-main)`, `var(--font-heading)`
  - Text Colors: `var(--text-bright)`, `var(--text-muted)`, `var(--text-dim)`
- **No Random Hex Codes**: Never insert arbitrary hex colors in component CSS files when design tokens or semantic color classes are available.
- **Glassmorphic Surface Pattern**:
  ```css
  .glass-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(12px);
    border-radius: var(--radius-card);
  }
  ```

---

## 4. Markdown & Rich Content Presentation
- LLM generated reports (such as from Goal Strategist or Portfolio Analyst) MUST NOT be rendered as raw newline-split paragraphs (`<p key={i}>{line}</p>`).
- Always render structured LLM text through dedicated presentation renderers (like `RoadmapRenderer.tsx`) supporting headers (`h3`, `h4`), status chips, list items, bold metrics, and compliance callouts.

---

## 5. Indentation, Formatting & Syntax Conventions
- **Indentation**:
  - STRICT **2 spaces per indentation level** across all `.ts`, `.tsx`, `.css`, and `.json` files. NEVER use tab characters (`\t`).
  - JSX attribute wrapping: when wrapping multiple props, each prop must sit on its own line with a 2-space indent.
- **Semicolons & Quotes**:
  - **No trailing semicolons** (follow standard Vite/ESLint modern conventions used in this codebase).
  - Use **single quotes** (`'...'`) for string literals and imports; use backticks (`` `...` ``) for template strings with variables.
  - Double quotes (`"..."`) only for JSX attributes (e.g. `className="glass-card"`).
- **Naming Conventions**:
  - **Components**: `PascalCase.tsx` (e.g., `GoalPlanner.tsx`, `RoadmapRenderer.tsx`).
  - **Custom Hooks**: `camelCase.ts` prefixed with `use` (e.g., `usePortfolio.ts`, `useGoalStrategist.ts`).
  - **Stylesheets**: Co-located `PascalCase.css` matching component name (e.g., `GoalPlanner.css`).
  - **Interfaces / Types**: `PascalCase` (e.g., `UserProfile`, `GoalConfig`).
  - **Functions & Variables**: `camelCase` (e.g., `fetchHoldings`, `isLoading`).
  - **Constants / Lookup Maps**: `UPPER_SNAKE_CASE` (e.g., `COUNTRY_META`, `API_ENDPOINTS`).
- **Import Ordering & Grouping** (separated by single blank line):
  1. React & core framework (`react`, `react-dom`)
  2. Third-party packages (`recharts`)
  3. Shared config, contexts, and hooks (`../config`, `../context/...`, `../hooks/...`)
  4. Child UI components (`./SubComponent`)
  5. Component stylesheets (`./Component.css`)

---

## 6. Lifecycle: How to Structure New Frontend Functionality
When introducing ANY new view, widget, or client functionality, follow this 6-step order:

```text
1. Endpoint (config.ts) ──> 2. Types (hook or model) ──> 3. Custom Hook (src/hooks/)
                                                                  │
6. Verification (npm build) <── 5. App / Nav (App.tsx) <─── 4. UI Component (src/components/)
```

1. **Step 1: Endpoint Registration (`src/config.ts`)**:
   - Add new route constant to `API_ENDPOINTS` in `src/config.ts`.
2. **Step 2: TypeScript Contract Definition**:
   - Define exact interfaces for backend request and response payloads. Avoid `any`.
3. **Step 3: Custom Hook Creation (`src/hooks/use<Feature>.ts`)**:
   - Encapsulate data fetching, `getAuthHeaders()`, `isLoading`, `error`, and refetch triggers.
   - Implement session-level caching (via `useRef` or state maps) if data doesn't change frequently.
4. **Step 4: Presentational Component (`src/components/<Feature>/<Feature>.tsx` + `.css`)**:
   - Create dedicated folder in `src/components/`.
   - Build component accepting hook data; consume CSS tokens (`tokens.css`).
   - Implement the complete state trinity: **Loading Skeleton**, **Empty State CTA**, and **Error Retry**.
5. **Step 5: Shell & Navigation Wiring (`src/App.tsx` & `src/components/Sidebar/Sidebar.tsx`)**:
   - Add active tab view state in `App.tsx`.
   - Add navigation icon and label in `Sidebar.tsx`.
6. **Step 6: Production Build Verification**:
   - Execute `npm run build` (`tsc -b && vite build`) inside `frontend/`.
   - Must complete with **0 errors and 0 warnings**.
7. **Step 7: Documentation Sync Gate (Human-in-the-Loop)**:
   - When Step 6 passes cleanly, present the completed view to the developer and propose updating UI documentation and feature guides (`README.md`, `docs/UI_DESIGN.md`, `docs/PROGRESS_LOG.md`).
   - NEVER update documentation without explicit developer approval.


