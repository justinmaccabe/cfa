# CFA Level II — Study Tracker

A small Streamlit companion to the chat tutor. It holds the **durable record** of
the prep: what's covered, how confident you are, what's due for spaced review, how
practice sets and mocks are trending. Built on the same stack as `mpmg-tracker`
(Streamlit + SQLAlchemy Core, SQLite locally / Postgres when deployed).

**Why it exists:** over ~9 months of study, "what have I actually covered?" can't
live only in a chat window. It lives here, on disk, so the tutor reads facts
instead of guessing — and nothing gets lost between sessions.

## Run it
```bash
cd ~/Documents/cfa-l2-tracker
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
First run creates `cfa.db` and seeds the 45 modules from `curriculum.py`.

## Tabs
- **Overview** — countdown, modules complete, hours this week, reviews due, progress
  by topic (coloured by your Level I signal).
- **Curriculum** — the 45 modules; edit status / confidence / completion date / notes.
  Setting a completion date auto-schedules the +3 / +14 / +45-day reviews.
- **Reviews** — the spaced-review queue; mark reviews done.
- **Drill Log** — log any study session or practice set (with a *predicted %* for calibration).
- **Mocks** — full-length mock scores over time + remediation notes.
- **Analytics** — topic-mastery accuracy, confidence-vs-actual calibration, weekly hours.

## Files
| File | Role |
|---|---|
| `app.py` | Streamlit UI |
| `db.py` | schema + seed + read/write helpers + the review-queue logic |
| `curriculum.py` | the 45 modules, topic weights, planned study order, L1 signal |
| `AGENT.md` | how the chat tutor reads/writes this DB (the shared-brain contract) |

## Scope guardrail
Build/polish this **before Aug 12, 2026** (materials-unlock). After that it's a
study tool, not a project — tool-building is the sneakiest form of exam
procrastination. The xlsx planner remains the schedule authority; this tracks
progress and performance.
# cfa
