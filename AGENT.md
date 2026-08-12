# Chat ↔ App data contract

This file is for the **chat tutor** (Claude). The rule: *the database is the source
of truth for study state; the tutor never asserts progress from memory.*

## Where
- DB file: `~/Documents/cfa-l2-tracker/cfa.db` (SQLite).
- Schema + helpers: `db.py`. Curriculum reference: `curriculum.py`.

## At the start of a study-status conversation
Read current state before making claims about coverage, weak areas, or what's due:
```bash
cd ~/Documents/cfa-l2-tracker && python3 -c "
import db, datetime as dt
m = db.get_modules_df()
print('Done:', int((m.status=='Done').sum()), '/ 42 readings')
print(m[m.status!='Not Started'][['id','topic','name','status','confidence']].to_string(index=False))
print('--- reviews due ---'); print(db.review_queue().to_string(index=False))
c = db.los_counts(); print('LOS ticked:', int(c.n_done.sum()), '/', int(c.n_los.sum()))
"
```

## When something happens in chat, write it (don't just remember)
Use the same helpers the app uses so both stay in sync:
- Finished reading a module → `db.update_module(id, status='Done', date_completed=dt.date(...))`
  (this auto-arms the +3/+14/+45 reviews).
- Ran a drill with the tutor → `db.log_study(date, topic, 'Practice', minutes=..., num_q=..., num_correct=..., predicted=..., source='Claude', notes=...)`.
- Cleared a review → `db.update_module(id, r1_done=True)` (or r2/r3) **and** log a Review row.
- Mock scored → `db.add_mock(date, source, score_pct, minutes_used, weak_topics, action_items)`.
- Justin says he can now do what a LOS asks → `db.set_los_done(los_id, True)`.

## Official Learning Outcome Statements
The `los` table holds the 382 official CFA Institute 2027 LOS, attached to the reading
that covers each one (`db.los_for_reading(reading_id)`, `db.los_counts()`). Reference
text comes from `los_2027.py`; `done` is Justin's own "I can do this unaided" tick.

Use them as the **authority on what the exam asks** — quiz against the LOS verb, not
your own sense of the topic ("calculate" and "describe" are different asks). Grouped by
`lm` (the official learning module), which is finer-grained than our readings in two
places: reading 1 is four LMs, reading 41 is one per Standard I-VII.

LOS ticks are advisory — they do NOT complete a reading or arm reviews, so don't infer
coverage from them alone. `submodules.status` remains the record of content covered.

## The per-reading study loop
Five fixed steps per reading, on `modules`: `mm_video`, `cfa_read`, `mm_q`,
`formula_done` (booleans) plus `cfa_q_done` / `cfa_q_total` (Justin types the total for
each reading himself). Read them through `db.study_loop_state(row)`, which coerces a
row and reports `done`/`total` — CFA questions count as cleared once a total is entered
and done has reached it. Write with `db.update_module(id, mm_video=True, ...)`; so
"watched the MM video for Time-Series" is `db.update_module(2, mm_video=True)`.

NULL means not-done (the columns were added additively to an existing DB), so go through
`study_loop_state` rather than testing a raw column. These ticks are **advisory**: they
do not complete a reading or arm reviews — `submodules.status` still does that.

The loop encodes one job per resource: **MM = teacher · CFA = authority + Qs ·
Schweser = review/formulas**. Useful in conversation — if he's stuck on a reading, ask
which steps are still open rather than guessing what he's tried.

## Confirm before writing
Mutating rows is a side effect — echo back what you're about to record ("Logging:
Equity practice, 18/25, ~15 min") and write on a clear yes, so the shared record
stays trustworthy.

## Reading ids
`modules.id` == reading order 1–42 (Quant 1–4, Econ 5–6, FSA 7–12, Corp Issuers 13–16,
Equity 17–22, FI 23–27, Derivatives 28–29, Alt 30–33, PM 34–39, Ethics 40–42). Look up
by name if unsure: `db.get_modules_df()`.

Below each reading sit its 255 items in `submodules` — the Schweser X.Y modules plus a
Key Concepts and a Module Quiz row each. That's the tier day-to-day check-off happens
on; reading status rolls up from it.
