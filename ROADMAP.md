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

## Official 2027 LOS integration — DONE (Aug 11, 2026)
The **official CFA Institute 2027 Level II topic outline**
(`~/Downloads/2027-cfa_l2_topic_outline.pdf`, 30pp) is now in the app: **10 topic areas,
51 learning modules, 382 LOS**, every one attached to the reading that covers it.
- `extract_los.py` parses the PDF → generated `los_2027.py`; the `los` table (db.py) holds
  the text plus a per-LOS `done` tick; the reading modal shows a 🎯 Learning Outcomes
  checklist grouped by official learning module, with the command verb bolded.
- Ticks are **advisory** — they don't complete a reading or arm reviews. `submodules.status`
  is still the record of content covered.
- Structure reconciled 42/42 readings, zero unmatched LMs. **Two** readings take more than
  one official LM, not one: Quant *Multiple Regression* is 4 LMs (as noted before) **and
  Ethics reading 41 is 7** — the 2027 outline splits *Guidance for Standards* into one LM
  per Standard I–VII, against our single reading with items 41.1–41.10. Standard I's two
  LOS are worded differently; II–VII repeat the same pair verbatim. All 14 are shown,
  grouped by Standard, rather than deduped.
- Label differences, aliased in `extract_los.py`, no action needed: CFAI's *Corporate
  Finance / Equities / Portfolio Construction* = our *Corporate Issuers / Equity
  Investments / Portfolio Management*; CFAI spells ESG out in full.
- When the 2028 outline lands: re-run `extract_los.py` and bump `db.LOS_VERSION`. The
  extractor asserts the expected 51-LM / 382-LOS / 4-and-7-fold shape and fails loudly if
  CFAI restructures. Note that a `LOS_VERSION` bump replaces the statements and clears ticks.
- Not built (natural follow-on): LOS coverage on the Curriculum rows, so gaps show without
  opening each reading.

## CFAI materials integration (when access opens ~Aug 12, 2026)
Justin gets the official **CFAI curriculum + QBank + mock exams** on Aug 12 and wants
to weave them into the study plan. To do then:
- Log **CFAI QBank** practice sessions into the Drill Log (`source = "CFAI QBank"`) so
  they feed the accuracy/calibration analytics.
- Route **CFAI mock exams** into the Mocks tab (scores, weak topics, remediation).
- Reconcile the **official CFAI LOS/readings** against our Schweser-derived structure —
  ~~add or adjust readings/items if CFAI's differ~~ done from the topic outline above; all
  42 readings matched, so no restructure is needed. What's still open is the other
  direction: whether to split Ethics reading 41 into the seven official per-Standard LMs
  now that the LOS make that structure visible.
- Re-tune pacing once the real QBank/mock cadence is known.
