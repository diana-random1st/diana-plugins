---
name: triz
description: "TRIZ inventive problem solving — turn a stuck problem into a contradiction and resolve it without compromise. Three modes: technical, product/business, general."
triggers: ["triz", "триз", "изобретательская задача", "contradiction", "противоречие", "ideal final result", "ИКР", "inventive principles", "can't have both"]
user-invocable: true
---

# TRIZ — Theory of Inventive Problem Solving

TRIZ replaces trial-and-error with a directed search: most hard problems hide a **contradiction**, and a small set of **inventive principles** resolve contradictions *without* a trade-off. The goal is the **Ideal Final Result (IFR)** — the function happens by itself, with no added cost or harm.

Use this when a problem feels like "pick your poison" — every solution sacrifices something. If there is no trade-off and no contradiction, you don't need TRIZ; just solve it.

## Mode selection (pick one, state it)

| Mode | When | Extra tools |
|------|------|-------------|
| **general** (default) | Any stuck problem, mixed/non-engineering | IFR + principles by analogy, light |
| **technical** | Physical/engineering/system, perf, hardware, low-level | + physical contradictions, separation, substance-field, laws of system evolution |
| **product** | Feature trade-offs, UX, business, GTM | + business-adapted principles, resources = users/data/channels |

Read the matching section in [references/modes.md](references/modes.md) before working a non-general problem.

## Core workflow (all modes)

1. **Frame the system & problem.** Name the system, its main useful function, and the symptom. State the problem from the user's point of view, not the current solution's.
2. **Surface the contradiction.** Write it explicitly as one of:
   - *Technical*: "When we improve **A**, it worsens **B**." (e.g. improve strength → worsens weight)
   - *Physical*: "Element X must be **P** and **not-P** at the same time." (e.g. hot and cold)
3. **State the IFR.** "The useful function is delivered, the harm is gone, with no new cost." Use it as the target — solutions are ranked by how close they get.
4. **Mine resources.** List what already exists, unused, in the system and its surroundings — substances, fields, space, time, information, byproducts. The best solution uses a free resource.
5. **Get candidate principles.**
   - Technical contradiction → map A and B to the 39 parameters and read the cell in the contradiction matrix (https://www.triz40.com/aff_Matrix_TRIZ.php) → 3–4 principle numbers; meanings at https://www.triz40.com/aff_Principles_TRIZ.php.
   - Physical contradiction → apply **separation** (in time / in space / on condition / between system and parts) — see modes.md.
6. **Generate ≥3 concrete solution directions** by reading each suggested principle against the problem. Keep them genuinely distinct.
7. **Rank by ideality** = (sum of benefits) / (cost + harm). Prefer the direction that removes the contradiction over the one that balances it.
8. **Falsify the top pick.** Derive one testable prediction and check it (prototype, calc, experiment, or argument). If it fails the contradiction is mis-framed — return to step 2.

## FPF integration

This maps onto the ADI cycle: framing the contradiction = **Abduction**, principles generate competing hypotheses, step 8's prediction = **Deduction**, the test = **Induction**. Don't skip the falsification step — a principle that "sounds right" is [SPECULATIVE] until tested.

## Output shape

Report: **System → Contradiction (typed) → IFR → Resources → Principles applied → ≥3 directions → Chosen + why (ideality) → Falsification test.** Tag claims [OBSERVED]/[INFERRED]/[SPECULATIVE].

## Reference

- Per-mode steps and worked examples: [references/modes.md](references/modes.md)
- 40 principles: https://www.triz40.com/aff_Principles_TRIZ.php · 39×39 matrix: https://www.triz40.com/aff_Matrix_TRIZ.php
