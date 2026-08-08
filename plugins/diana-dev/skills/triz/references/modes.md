# TRIZ — Modes & Worked Examples

The core 8-step workflow in SKILL.md is the same in every mode. Each mode adds tools and changes what "resource" and "parameter" mean.

---

## General mode (default)

For any stuck problem, including non-engineering ones. Skip the formal matrix.

- Step 5 substitution: instead of the 39×39 matrix, scan the 40 principles (principles.md) and pick the 3–4 that map by analogy. Lean on the "most-frequently-used" shortlist first.
- Keep the contradiction and IFR steps — they do most of the work even without the matrix.
- Resources = anything already present and unused: time, space, existing data, people, side-effects, idle capacity.

**Example — notification overload (product-ish but framed generally):**
- System: app notifications. Function: inform user of partner activity.
- Contradiction (technical): improve *informativeness* (send more) → worsens *ease of operation / annoyance* (notification fatigue).
- IFR: the user is informed exactly when it matters, with zero unwanted interruptions.
- Resources: user's own behavior signals, time-of-day, app-open events.
- Principles: #15 Dynamics (adapt frequency to context), #19 Periodic action (batch into digests), #23 Feedback (let user reactions tune volume), #2 Taking out (extract only the rare urgent class — e.g. SOS — and let only it interrupt).
- Direction chosen: #2 + #15 — interrupt only on the urgent class, batch the rest, adapt cadence to engagement. Removes the contradiction instead of balancing "more vs fewer".
- Falsify: predict digest+urgent-split lowers mute-rate without lowering open-rate; test on a cohort.

---

## Technical mode

For physical, engineering, performance, hardware, or low-level system problems. Adds three tools.

### Physical contradiction + separation principles
When one element must have opposite states ("must be P and not-P"), don't compromise — **separate** the requirement:
- **in Time** — P at one moment, not-P at another (e.g. landing gear: present on takeoff, retracted in flight).
- **in Space** — P in one region, not-P in another (e.g. bike chain: rigid along length, flexible across links).
- **on Condition** — P under condition C, not-P otherwise (e.g. one-way valve, temperature-triggered).
- **between System & parts** — P at the whole-system level, not-P at the component level (e.g. bike chain rigid as a loop, each link free).

### Substance-Field (Su-Field) analysis
Model the problem as two substances + a field acting between them. Incomplete or harmful interaction → standard fixes: add a missing substance/field, introduce a modified or third substance, switch the field type (mechanical → thermal → electric → magnetic). Use when "what acts on what, and how" is unclear.

### Laws (trends) of technical-system evolution
Use to predict the *next* design generation, not just fix today's bug: increasing ideality; uneven development of parts (one part lags → that's the next bottleneck); transition to the super-system; increasing dynamism/controllability; transition from macro to micro level; increasing substance-field involvement. Ask "which law is this system not yet following?"

**Example — heat sink (classic technical):**
- Contradiction (technical): improve *cooling* (parameter 17 temperature) → worsens *weight/volume* (1/7) as the sink grows.
- Physical reframe: the surface must be *large* (for dissipation) and *small* (for volume) at once → separate in **space/scale**: micro-level surface.
- Principles from matrix (17 vs 7): #14 spheroidality, #29 pneumatics/hydraulics, #35 parameter change, #31 porous materials.
- Direction: #31 + micro-level law — porous/finned micro-structure or liquid (#29) loop; huge surface, small bulk. Contradiction dissolved.
- Falsify: predict thermal resistance drops at equal volume; bench-test or simulate.

---

## Product / business mode

For feature trade-offs, UX, pricing, growth, ops. The 40 principles have business analogues; the contradiction is between business attributes, not engineering ones.

- Common business parameters to trade between: revenue vs. retention, acquisition cost vs. quality, speed-to-market vs. completeness, simplicity vs. power, personalization vs. privacy, free vs. paid value.
- Resources here = users, their data/behavior, existing channels, partners, content, brand, unused capacity, timing.
- Business reading of key principles: #1 Segmentation → tiered plans / micro-segments; #3 Local quality → personalization; #5 Merging → bundling; #6 Universality → one feature serving many jobs; #13 The other way round → invert the funnel / let users come to you; #25 Self-service → user-generated content, self-serve onboarding; #2 Taking out → unbundle the one valued feature; #10 Preliminary action → pre-onboarding, defaults; #22 Blessing in disguise → turn a constraint into the pitch.

**Example — freemium conversion vs. free-tier value:**
- Contradiction: improve *conversion to paid* (gate more) → worsens *free-tier adoption / virality* (gate kills growth).
- IFR: free users grow the base virally AND the paid feature sells itself, with no hard wall.
- Resources: the partner/social graph (this is a couples app — value is inherently 2-sided), usage moments.
- Principles: #2 Taking out (gate only the one feature that needs hardware/cost — e.g. bracelet — keep messaging free), #13 The other way round (let the paying partner unlock for both), #10 Preliminary action (give premium trial at the high-intent moment, not at signup).
- Direction: #2 + #13 — phone messaging free for reach; bracelet/premium gated; one partner's purchase benefits the pair. Growth and monetization stop fighting.
- Falsify: predict free-tier MAU and paid-conversion both rise vs. a hard paywall; A/B test.

---

## When NOT to use TRIZ

No contradiction, no trade-off → it's a normal task, just do it. TRIZ earns its overhead only when "every option sacrifices something" — that's the signal a contradiction is hiding underneath.
