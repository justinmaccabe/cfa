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
print('Done:', int((m.status=='Done').sum()), '/ 45')
print(m[m.status!='Not Started'][['id','topic','name','status','confidence']].to_string(index=False))
print('--- reviews due ---'); print(db.review_queue().to_string(index=False))
"
```

## When something happens in chat, write it (don't just remember)
Use the same helpers the app uses so both stay in sync:
- Finished reading a module → `db.update_module(id, status='Done', date_completed=dt.date(...))`
  (this auto-arms the +3/+14/+45 reviews).
- Ran a drill with the tutor → `db.log_study(date, topic, 'Practice', minutes=..., num_q=..., num_correct=..., predicted=..., source='Claude', notes=...)`.
- Cleared a review → `db.update_module(id, r1_done=True)` (or r2/r3) **and** log a Review row.
- Mock scored → `db.add_mock(date, source, score_pct, minutes_used, weak_topics, action_items)`.

## Confirm before writing
Mutating rows is a side effect — echo back what you're about to record ("Logging:
Equity practice, 18/25, ~15 min") and write on a clear yes, so the shared record
stays trustworthy.

## Module ids
`modules.id` == curriculum order 1–45 (Quant 1–7, Econ 8–9, FSA 10–15,
Corp Issuers 16–19, Equity 20–25, FI 26–30, Derivatives 31–32, Alt 33–36,
PM 37–42, Ethics 43–45). Look up by name if unsure: `db.get_modules_df()`.
