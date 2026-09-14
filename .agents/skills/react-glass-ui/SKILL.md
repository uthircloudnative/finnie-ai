---
name: react-glass-ui
description: Guides building, refactoring, and polishing modern React 19 + TypeScript interfaces using the Glass-Finance design system. Use when creating UI components, custom hooks, data visualizations, or styling dashboards.
---

# React 19 & Glass-Finance UI Playbook

This skill outlines the patterns and standards for developing the user interface in Finnie AI.

---

## 1. The Custom Hook Architecture Pattern

Every page or major widget in Finnie AI has a dedicated custom hook that acts as the single controller for data fetching, caching, and state management.

### Hook Template (`src/hooks/useExample.ts`):
```typescript
import { useState, useCallback, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { API_BASE } from '../config'

export function useExample() {
  const { getAuthHeaders } = useAuth()
  const [data, setData] = useState<ExampleData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/example`, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        }
      })
      if (!res.ok) throw new Error(`HTTP error ${res.status}`)
      const json = await res.json()
      setData(json)
    } catch (err: any) {
      setError(err.message || 'Failed to load data')
    } finally {
      setIsLoading(false)
    }
  }, [getAuthHeaders])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}
```

---

## 2. Presentational Component Standards

1. **Keep Components Pure**: UI components receive data, loading state, and handlers through props or hook return objects.
2. **Handle Empty & Error States**:
   ```tsx
   if (isLoading) return <LoadingSkeleton />
   if (error) return <RetryCard onRetry={refetch} message={error} />
   if (!data || data.length === 0) return <EmptyCard message="No holdings found" />
   ```
3. **Structured Markdown Presentation**:
   When rendering AI responses containing lists or bold text, use the `<RoadmapRenderer markdown={content} />` component rather than raw `<p>` tags.

---

## 3. Glass-Finance Design Tokens

Always style components using the design tokens defined in `src/styles/tokens.css`:

| Token | Value | Purpose |
|---|---|---|
| `var(--accent-cyan)` | `#00f3ff` | Primary action buttons, active tab indicators, key metric highlights |
| `var(--glass-bg)` | `rgba(15, 23, 42, 0.65)` | Frosted glass card backgrounds |
| `var(--glass-border)` | `rgba(255, 255, 255, 0.08)` | Subtle border defining card bounds |
| `var(--text-bright)` | `#f8fafc` | Primary titles and high-contrast numerical metrics |
| `var(--text-muted)` | `#94a3b8` | Explanatory body text and labels |
| `var(--text-dim)` | `#64748b` | Sub-labels and metadata hints |

---

## 4. Indentation, Formatting & Syntax Standards

All frontend code must follow these strict syntactic rules:
- **Indentation**: STRICT **2 spaces** per indentation level. NEVER use tab characters (`\t`).
- **Quotes**: Single quotes (`'...'`) for string literals; backticks (`` `...` ``) for template strings; double quotes (`"..."`) for JSX attributes.
- **Semicolons**: **Omit semicolons** consistently across all `.ts` and `.tsx` files.
- **Naming Conventions**:
  - Components: `PascalCase.tsx`
  - Hooks: `useCamelCase.ts`
  - Stylesheets: Co-located `PascalCase.css`
  - Interfaces: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Import Organization**:
  ```typescript
  // 1. React & framework
  import { useState, useEffect, useCallback } from 'react'
  // 2. Third-party packages
  import { AreaChart, Area } from 'recharts'
  // 3. Centralized config & context
  import { API_BASE } from '../config'
  import { useAuth } from '../context/AuthContext'
  // 4. Local hooks & child components
  import { usePortfolio } from '../hooks/usePortfolio'
  import RoadmapRenderer from './RoadmapRenderer'
  // 5. Co-located styles
  import './MyComponent.css'
  ```

---

## 5. Lifecycle: How to Structure New Frontend Functionality

When introducing ANY new view, tab, or analytical dashboard, follow this 6-step lifecycle:

```text
1. Endpoint (config.ts) ──> 2. TypeScript Types ──> 3. Custom Hook (src/hooks/)
                                                            │
6. npm run build <── 5. Wire App/Sidebar <── 4. Presentational Component (src/components/)
```

1. **Step 1: Endpoint Registration (`src/config.ts`)**:
   Add the route constant into `API_ENDPOINTS` in `src/config.ts`.
2. **Step 2: TypeScript Interfaces**:
   Define strict request/response interfaces. Never use `any`.
3. **Step 3: Custom Hook (`src/hooks/use<Feature>.ts`)**:
   Implement fetching with `getAuthHeaders()`, `isLoading`, `error`, `refetch`, and session-level caching (`useRef` or state maps).
4. **Step 4: Presentational Component (`src/components/<Feature>/`)**:
   Create `<Feature>.tsx` and `<Feature>.css` consuming design tokens from `tokens.css`.
   Handle all three mandatory UI states:
   - **Loading**: Skeleton placeholder or pulsing `ThinkingIndicator`.
   - **Empty**: Informative card with illustrative icon and actionable CTA.
   - **Error / Degraded**: Interactive retry button (`onRetry`).
5. **Step 5: Shell & Navigation Wiring**:
   Register tab view in `src/App.tsx` and add icon + navigation item in `src/components/Sidebar/Sidebar.tsx`.
6. **Step 6: Build Verification**:
   Verify with `npm run build` (must pass with 0 errors).

---

## 6. Verification Recipe

After making frontend changes:
1. Run the TypeScript build:
   ```bash
   cd frontend
   npm run build
   ```
2. Verify **0 errors and 0 warnings**.

