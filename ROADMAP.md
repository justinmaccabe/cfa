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

## Per-reading study-loop checklist — DONE (Aug 12, 2026)
"Give each resource one job," made trackable **at the reading level**, shown in the
`section_dialog` modal ABOVE the items table — rendered as a numbered vertical sequence
**in the order Justin runs it** (his call, Aug 12), so the modal is the instruction sheet
and he doesn't have to hold the order in his head:
1. ☐ **MM video** — first exposure, MM builds the mental model
2. ◇ **Schweser read** — *not a tick*: this is the items table below, one row per module.
   The step shows `n/m modules at Practice Complete` and says to set each row's **Status**.
3. ☐ **CFA blue boxes / skim** — the authority, catches what MM compressed
4. ☐ **MM Qs** — drill
5. ☐ **CFA Qs** — **done / total** on one line (he TYPES the total per reading — manual
   entry by choice, no CFAI parsing)
6. ☐ **Formula sheet / QuickSheet** — the formula pass
(Spaced reviews stay in the existing system — NOT part of this checklist, and the caption
says so: the formula pass is not the review.)

**Why step 2 is in the list without being a tick:** he asked "when I complete 1.1, what do
I tick?" and the first cut had no visible answer — the per-module record was the items
table's Status column, three feet down the modal with nothing connecting them. Listing the
Schweser read in its own position, with live item progress and a pointer, closes that gap
without duplicating the record. Deliberately NOT built: per-item loop columns (an MM-video
tick on 1.1, 1.2, …). `submodules.status` already tracks per-module read→practice progress,
so five more columns × 255 rows would triple-track the same thing. Revisit only if he wants
per-module MM video counts specifically.

**As built:** the six additive columns landed on `modules` exactly as planned (`mm_video`,
`cfa_read`, `mm_q`, `formula_done` BOOL + `cfa_q_done`, `cfa_q_total` INT), added **nullable**
via `_migrate` — a pure metadata change on SQLite *and* Postgres, so no wipe and safe on Neon
after the push. NULL reads as not-done, which is also how "haven't counted the Qs yet" is
stored. Writes reuse `db.update_module`, unchanged.
- `curr.STUDY_LOOP_STEPS` is the ordered display spec — `(key, kind, label, help)` where kind
  is `flag` (a boolean column), `items` (the derived Schweser-read pointer) or `count` (the
  CFA-Q pair). `STUDY_LOOP_FLAGS` derives the four booleans from it, so the loop's order lives
  in exactly one place. `db.study_loop_state(row)` is the one reader, used by both the modal
  and the Curriculum pips, so the two can't drift. CFA Qs have no tick of their own — the step
  clears when a total is entered and done reaches it (overshoot counts; a total of 0 doesn't).
- The tick count stays **n/5**: the Schweser read is excluded on purpose, because
  double-counting it would let a full loop claim a reading was covered when the items say
  otherwise. The header shows both — `n/5 ticked · Schweser modules n/m`.
- **Deviation from the original build note (which asked for a save):** no Save button — each
  control persists itself through an `on_change` callback, because `st.rerun()` inside this
  dialog fragment would slam the modal shut on every tick (the same constraint the LOS
  checklist hit). The `n/5 done` counter re-reads the row each fragment run, so it stays in
  step with what's actually stored rather than with what's on screen.
- Resource-role caption is in place, and the nice-to-have shipped: a five-dot study-loop pip on
  every Curriculum row (`○○○○○` → `●●●●●`, with a `n/5 steps` tooltip).
- Advisory by design, like the LOS ticks: `submodules.status` still completes a reading and
  arms its reviews. Spaced reviews stayed out of the checklist, as specified.
- Verified against a copy of the live DB: 42 readings / 255 items / 382 LOS intact, no reading
  status or review clock touched. Not built: rolling the loop into pace/analytics.

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
