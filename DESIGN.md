# AgentLoopGuard Design System

**Aesthetic stance**: Dark-mode developer tool — deep navy/charcoal background, monospace accents, electric green/cyan highlights. Feels like a sophisticated terminal UI meets a modern SaaS page. Clean, technical, trustworthy.

**Type**:
- Heading: Inter, 700 weight. h1=3rem, h2=2rem, h3=1.5rem
- Body: Inter, 400 weight, 1.6 line-height, max-width 720px
- Mono: JetBrains Mono — for code snippets and the terminal animation

**Color**:
- Surface: #0a0e1a — deep navy background
- Surface alt: #141829 — cards, raised areas
- Text: #e2e8f0 primary / #94a3b8 muted
- Accent: #22d3ee — electric cyan, used sparingly
- Success: #34d399 / Warning: #fbbf24 / Danger: #f87171

**Spacing**:
- Base unit: 8px
- Section vertical rhythm: 80px
- Card padding: 32px

**Motion**:
- Default transition: 200ms ease-out
- Animate: hover states, the terminal demo, section fade-ins on scroll
- Don't animate: text, layout shifts, anything distracting

**What this system rejects**:
- No gradients on backgrounds
- No glassmorphism or blur effects
- No rounded bubbly buttons — sharp corners, 4px radius max
- No light mode (this is a dev tool, dark only)
- No hero images or stock photos — code and terminal UI only
