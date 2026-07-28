# Roadmap — parked ideas & upcoming work

Living backlog for the CFA L2 tracker. Not started yet — revisit on request.

## Enhancement backlog (Justin liked all of these — revisit later)
1. **AI drill / vignette engine** *(biggest lever)* — generate real L2-style item-sets
   from the actual Schweser text for the current reading, grade them, and auto-log
   the score to the Drill Log → Analytics. Turns the tracker into a *trainer*.
2. **Weak-spot focus on Today** — a "your L1 soft spots" nudge (Quant, Equity) that
   steers effort using the `L1_SIGNAL` we already store.
3. **Performance heatmap** — a 42-reading grid tinted by Perf %, strengths/holes at a glance.
4. **Study streak + weekly-hours ring** — lightweight motivation vs the 12h/wk target.
5. **Dark-mode toggle** + **curriculum search box** (jump to any reading fast).

Suggested order when we resume: quick morale wins (#2, #4) first, then the drill
engine (#1) as a focused build, then #3/#5 polish.

## CFAI materials integration (when access opens ~Aug 12, 2026)
Justin gets the official **CFAI curriculum + QBank + mock exams** on Aug 12 and wants
to weave them into the study plan. To do then:
- Log **CFAI QBank** practice sessions into the Drill Log (`source = "CFAI QBank"`) so
  they feed the accuracy/calibration analytics.
- Route **CFAI mock exams** into the Mocks tab (scores, weak topics, remediation).
- Reconcile the **official CFAI LOS/readings** against our Schweser-derived structure —
  add or adjust readings/items if CFAI's differ.
- Re-tune pacing once the real QBank/mock cadence is known.
