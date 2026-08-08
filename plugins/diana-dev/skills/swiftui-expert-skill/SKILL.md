---
name: swiftui-expert-skill
description: Use for SwiftUI review, refactoring, or implementation work that depends on correct state, modern APIs, performance, navigation, animation, or Liquid Glass boundaries.
---

# SwiftUI Expert

Choose the path first: review existing code, improve existing code, or implement a new feature.

Working rules:
1. Inspect the current target, platform floor, state model, and view structure before proposing patterns.
2. For state and data flow, start with [references/state-management.md](./references/state-management.md); for view shape, use [references/view-structure.md](./references/view-structure.md).
3. Prefer modern APIs and replacements from [references/modern-apis.md](./references/modern-apis.md), while keeping availability fallbacks explicit.
4. Keep view bodies pure, identities stable, and hot paths lean; use the performance, list, layout, and scroll references when relevant.
5. Use the animation references for transitions or timing-sensitive motion, and adopt Liquid Glass only when the user explicitly asks for it.
6. Do not impose a specific app architecture; separate business logic only as far as the existing code and testability require.
7. Before presenting, verify the changed code path, availability handling, and the relevant SwiftUI references for the exact API family involved.

Direct references:
- [references/performance-patterns.md](./references/performance-patterns.md)
- [references/list-patterns.md](./references/list-patterns.md)
- [references/layout-best-practices.md](./references/layout-best-practices.md)
- [references/sheet-navigation-patterns.md](./references/sheet-navigation-patterns.md)
- [references/scroll-patterns.md](./references/scroll-patterns.md)
- [references/text-formatting.md](./references/text-formatting.md)
- [references/animation-basics.md](./references/animation-basics.md)
- [references/animation-transitions.md](./references/animation-transitions.md)
- [references/animation-advanced.md](./references/animation-advanced.md)
- [references/image-optimization.md](./references/image-optimization.md)
- [references/liquid-glass.md](./references/liquid-glass.md)
