"""Database layer for the CFA Level II tracker.

Same shape as the mpmg-tracker: SQLAlchemy Core, Postgres when DATABASE_URL is
set, otherwise a local SQLite file (cfa.db). This module is the single source of
truth for the schema, and it is deliberately the thing BOTH the Streamlit app and
the chat tutor read/write. That is the whole point of the design: "what have I
covered, how did I score" is a fact on disk, not something the tutor remembers and
could get wrong. See AGENT.md for the read/write contract.
"""
import os
import time
import datetime as dt

import pandas as pd
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Float, Date,
    Boolean, Text, LargeBinary, select, func, inspect, text,
)
from sqlalchemy.exc import OperationalError

import curriculum as curr

READINGS_SEED_OK = True   # sentinel for app.py's stale-module reload guard


def _database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        try:  # running inside Streamlit with a secret configured
            import streamlit as st
            url = st.secrets.get("DATABASE_URL")
        except Exception:
            url = None
    if not url:
        here = os.path.dirname(os.path.abspath(__file__))
        return f"sqlite:///{os.path.join(here, 'cfa.db')}"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


engine = create_engine(_database_url(), future=True)
metadata = MetaData()

# The 45 learning modules. Status/confidence/completion are what YOU maintain;
# everything else is seeded reference data from curriculum.py.
modules = Table(
    "modules", metadata,
    Column("id", Integer, primary_key=True),      # = curriculum order (1..45)
    Column("topic", String, nullable=False),
    Column("name", String, nullable=False),
    Column("book", Integer),                        # Schweser book 1-5
    Column("reading", Integer),                     # Schweser reading number
    Column("study_order", Integer),                 # our planned topic sequence
    Column("status", String, nullable=False, default="Not Started"),  # Not Started/In Progress/Done
    Column("confidence", Integer),                  # 1-5, your call after study
    Column("date_completed", Date),                 # drives the review schedule
    Column("r1_done", Boolean, nullable=False, default=False),
    Column("r2_done", Boolean, nullable=False, default=False),
    Column("r3_done", Boolean, nullable=False, default=False),
    Column("notes", Text),
)

# Every study event: reading, a practice set, a review pass. num_q/num_correct are
# optional (a pure reading session leaves them null); when present they feed the
# accuracy + calibration analytics. `predicted` is your pre-drill gut-feel % — the
# calibration view compares it against what you actually scored.
study_log = Table(
    "study_log", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("date", Date, nullable=False),
    Column("topic", String, nullable=False),
    Column("module_id", Integer),                   # optional FK -> modules.id
    Column("activity", String, nullable=False),     # Read / Practice / Review / Class / Other
    Column("minutes", Float, nullable=False, default=0.0),
    Column("num_q", Integer),                        # questions attempted (if any)
    Column("num_correct", Integer),                  # questions right (if any)
    Column("predicted", Integer),                    # your predicted % before grading
    Column("source", String),                        # Claude / CFAI QBank / Schweser / ...
    Column("notes", Text),
)

# Full-length timed mocks get their own table because they carry a remediation
# workflow (weak topics -> action items -> reviewed?), not just a score.
mocks = Table(
    "mocks", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("date", Date, nullable=False),
    Column("source", String),                        # CFAI Mock A, etc.
    Column("score_pct", Float),
    Column("minutes_used", Integer),
    Column("weak_topics", Text),
    Column("action_items", Text),
    Column("reviewed", Boolean, nullable=False, default=False),
)

# Free-form key/value config (exam date, weekly-hours target, ...). Value is TEXT
# so it can hold dates and strings, not just numbers.
settings = Table(
    "settings", metadata,
    Column("key", String, primary_key=True),
    Column("value", Text),
)

# Binary blobs. Kept in the DB (not the git repo) so they travel to every device
# via Postgres and never get committed. Resources = your licensed reading materials
# (personal cross-device access, password-gated in the app). notes_doc = your living
# Word doc, versioned so an accidental bad upload never loses your work.
resources = Table(
    "resources", metadata,
    Column("name", String, primary_key=True),
    Column("data", LargeBinary),
    Column("size", Integer),
    Column("updated_at", String),
)

notes_doc = Table(
    "notes_doc", metadata,
    Column("version", Integer, primary_key=True, autoincrement=True),
    Column("filename", String),
    Column("data", LargeBinary),
    Column("uploaded_at", String),
)

# The granular tier: 171 Schweser study sub-modules, each belonging to a section
# (modules.id). This is where day-to-day checking-off and spaced reviews happen;
# section status/completion is rolled up from here (see _rollup_section).
submodules = Table(
    "submodules", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("section_id", Integer, nullable=False),   # -> modules.id
    Column("code", String),                          # Schweser "2.1" etc.
    Column("name", String, nullable=False),
    Column("status", String, nullable=False, default="Not Started"),
    Column("confidence", Integer),
    Column("date_completed", Date),
    Column("r1_done", Boolean, nullable=False, default=False),
    Column("r2_done", Boolean, nullable=False, default=False),
    Column("r3_done", Boolean, nullable=False, default=False),
    Column("notes", Text),
)

# Manual / logistics tasks that live on the agenda and can be ticked off (they
# aren't sub-readings). Seeded with the pre-game checklist.
checklist = Table(
    "checklist", metadata,
    Column("key", String, primary_key=True),
    Column("label", String, nullable=False),
    Column("note", String),
    Column("sort", Integer),
    Column("done", Boolean, nullable=False, default=False),
    Column("done_date", Date),
)

SEED_CHECKLIST = [
    ("materials", "Materials unlock — Aug 12, 2026", "get ready to start", 1),
    ("register", "Set an early-registration reminder", "deadline ~Oct 14 · saves $350", 2),
    ("calc", "Calculator ready (BA II Plus)", "dust it off / replace if flaky", 3),
    ("freeze", "Freeze the tracker build before Aug 12", "then it's a study tool", 4),
]

SEED_SETTINGS = {
    "exam_date": "2027-05-18",          # placeholder until CFAI publishes May 2027 dates
    "pregame_start": "2026-07-20",      # start of the pre-game runway segment
    "materials_date": "2026-08-12",     # registration + curriculum/QBank/mocks unlock
    "consolidation_start": "2027-02-03",  # content ends, full-curriculum buffer begins
    "mock_start": "2027-03-03",         # full-length timed mocks begin
    "taper_start": "2027-05-12",        # final light-review taper
    "weekly_hours_target": "12",
    "candidate_name": "Justin Maccabe",
    "notes_url": "",                    # paste a Google Doc link in the Notes tab
}


def init_db(seed: bool = True):
    """Create tables / seed, retrying so a cold (sleeping) Postgres wakes instead
    of crashing the app on the first query."""
    for attempt in range(3):
        try:
            return _init_db(seed)
        except OperationalError:
            if attempt == 2:
                raise
            time.sleep(2)


def _migrate():
    """Additive migrations for DBs created before a column existed. Cheap to run
    every boot; only ALTERs when something is genuinely missing."""
    cols = {c["name"] for c in inspect(engine).get_columns("modules")}
    with engine.begin() as conn:
        if "study_order" not in cols:
            conn.execute(text("ALTER TABLE modules ADD COLUMN study_order INTEGER"))


def _init_db(seed: bool = True):
    metadata.create_all(engine)
    if inspect(engine).has_table("modules"):
        _migrate()
    if not seed:
        return
    with engine.begin() as conn:
        if conn.execute(select(func.count()).select_from(modules)).scalar() == 0:
            conn.execute(modules.insert(), [
                dict(id=i + 1, topic=t, name=title, book=bk, reading=rd,
                     study_order=curr.STUDY_ORDER.get(t, 50),
                     status="Not Started", r1_done=False, r2_done=False, r3_done=False)
                for i, (t, title, bk, rd) in enumerate(curr.READINGS)
            ])
        if conn.execute(select(func.count()).select_from(submodules)).scalar() == 0:
            rid = {rd: i + 1 for i, (_t, _ti, _bk, rd) in enumerate(curr.READINGS)}
            conn.execute(submodules.insert(), [
                dict(section_id=rid[r], code=c, name=n, status="Not Started",
                     r1_done=False, r2_done=False, r3_done=False)
                for (r, c, n) in curr.ITEMS])
        if conn.execute(select(func.count()).select_from(checklist)).scalar() == 0:
            conn.execute(checklist.insert(), [
                dict(key=k, label=l, note=n, sort=s, done=False)
                for (k, l, n, s) in SEED_CHECKLIST])
        if conn.execute(select(func.count()).select_from(settings)).scalar() == 0:
            conn.execute(settings.insert(), [
                dict(key=k, value=v) for k, v in SEED_SETTINGS.items()])


# ---- read helpers -------------------------------------------------
def get_modules_df() -> pd.DataFrame:
    return pd.read_sql(select(modules).order_by(modules.c.id), engine)


def get_study_log_df() -> pd.DataFrame:
    return pd.read_sql(select(study_log).order_by(study_log.c.date), engine)


def get_mocks_df() -> pd.DataFrame:
    return pd.read_sql(select(mocks).order_by(mocks.c.date), engine)


def get_settings() -> dict:
    df = pd.read_sql(select(settings), engine)
    return dict(zip(df["key"], df["value"])) if not df.empty else dict(SEED_SETTINGS)


# ---- write helpers ------------------------------------------------
def update_module(module_id: int, **fields):
    """Patch any subset of a module's mutable columns. When date_completed is set
    and status wasn't passed, mark it Done as a convenience."""
    if "date_completed" in fields and fields["date_completed"] and "status" not in fields:
        fields["status"] = "Done"
    with engine.begin() as conn:
        conn.execute(modules.update().where(modules.c.id == int(module_id))
                     .values(**fields))


def get_submodules_df() -> pd.DataFrame:
    """All 171 sub-modules, joined to their section's topic + name."""
    df = pd.read_sql(select(submodules).order_by(submodules.c.id), engine)
    secs = (get_modules_df()[["id", "topic", "name", "study_order", "book"]]
            .rename(columns={"id": "section_id", "name": "section_name"}))
    return df.merge(secs, on="section_id", how="left")


def submodules_for_section(section_id: int) -> pd.DataFrame:
    return pd.read_sql(select(submodules).where(submodules.c.section_id == int(section_id))
                       .order_by(submodules.c.id), engine)


def _rollup_section(section_id: int):
    """Recompute a section's status/date_completed from its sub-modules. All done =>
    Done (completed = latest sub date); any progress => In Progress; else Not Started.
    Keeps the modules table — which the Calendar, pace bars and agenda read — honest."""
    sub = pd.read_sql(select(submodules.c.status)
                      .where(submodules.c.section_id == int(section_id)), engine)
    n = len(sub)
    done = int(sub["status"].isin(curr.ITEM_COMPLETE).sum())
    started = int((sub["status"] != "Not Started").sum())
    status = "Done" if (n and done == n) else ("In Progress" if started else "Not Started")
    with engine.begin() as conn:
        cur = conn.execute(select(modules.c.date_completed)
                           .where(modules.c.id == int(section_id))).scalar()
        # reading completes -> stamp date (arms reading-level reviews); backtrack clears it
        dc = dt.date.today() if (status == "Done" and cur is None) else (None if status != "Done" else cur)
        conn.execute(modules.update().where(modules.c.id == int(section_id))
                     .values(status=status, date_completed=dc))


def update_submodule(sub_id: int, **fields):
    with engine.begin() as conn:
        conn.execute(submodules.update().where(submodules.c.id == int(sub_id)).values(**fields))
        sec = conn.execute(select(submodules.c.section_id)
                           .where(submodules.c.id == int(sub_id))).scalar()
    _rollup_section(sec)   # rolls the reading's status + review clock up from its items


def log_study(date, topic, activity, minutes=0.0, module_id=None, num_q=None,
              num_correct=None, predicted=None, source=None, notes=None):
    with engine.begin() as conn:
        conn.execute(study_log.insert().values(
            date=date, topic=topic, activity=activity, minutes=float(minutes or 0),
            module_id=module_id, num_q=num_q, num_correct=num_correct,
            predicted=predicted, source=source, notes=notes))


def delete_study(row_id: int):
    with engine.begin() as conn:
        conn.execute(study_log.delete().where(study_log.c.id == int(row_id)))


def add_mock(date, source, score_pct, minutes_used=None, weak_topics=None,
             action_items=None, reviewed=False):
    with engine.begin() as conn:
        conn.execute(mocks.insert().values(
            date=date, source=source, score_pct=float(score_pct),
            minutes_used=minutes_used, weak_topics=weak_topics,
            action_items=action_items, reviewed=reviewed))


def update_mock(mock_id: int, **fields):
    with engine.begin() as conn:
        conn.execute(mocks.update().where(mocks.c.id == int(mock_id)).values(**fields))


def set_setting(key, value):
    with engine.begin() as conn:
        conn.execute(settings.delete().where(settings.c.key == key))
        conn.execute(settings.insert().values(key=key, value=str(value)))


# ---- derived: the spaced-review queue -----------------------------
def review_queue(as_of: dt.date = None) -> pd.DataFrame:
    """Every not-yet-done review due on/before `as_of`, at the SUB-MODULE level —
    computed from each completed sub-module's date_completed + REVIEW_LAGS. One row
    per outstanding review (sub_id, topic, section, module, which review, due, overdue)."""
    as_of = as_of or dt.date.today()
    m = get_modules_df()                       # reviews are at the READING level now
    done = m[m["date_completed"].notna()]
    rows = []
    for _, r in done.iterrows():
        base = pd.to_datetime(r["date_completed"]).date()
        for n, lag in enumerate(curr.REVIEW_LAGS, start=1):
            if bool(r[f"r{n}_done"]):
                continue
            due = base + dt.timedelta(days=lag)
            if due <= as_of:
                rows.append(dict(reading_id=int(r["id"]), topic=r["topic"],
                                 module=r["name"], review=f"R{n}",
                                 due=due, days_overdue=(as_of - due).days))
    out = pd.DataFrame(rows)
    return out.sort_values("due") if not out.empty else out


# ---- binary blobs: resources + living notes doc -------------------
def list_resources() -> pd.DataFrame:
    """Metadata only (no blob data) so listing is cheap even with big PDFs."""
    return pd.read_sql(select(resources.c.name, resources.c.size,
                              resources.c.updated_at).order_by(resources.c.name), engine)


def get_resource(name: str):
    with engine.begin() as conn:
        row = conn.execute(select(resources.c.data)
                           .where(resources.c.name == name)).first()
    return row[0] if row else None


def upsert_resource(name: str, data: bytes, updated_at: str):
    with engine.begin() as conn:
        conn.execute(resources.delete().where(resources.c.name == name))
        conn.execute(resources.insert().values(
            name=name, data=data, size=len(data), updated_at=updated_at))


def delete_resource(name: str):
    with engine.begin() as conn:
        conn.execute(resources.delete().where(resources.c.name == name))


def notes_versions() -> pd.DataFrame:
    return pd.read_sql(select(notes_doc.c.version, notes_doc.c.filename,
                              notes_doc.c.uploaded_at).order_by(notes_doc.c.version.desc()),
                       engine)


def get_notes(version: int = None):
    """Return (filename, data) for the given version, or the latest if None."""
    q = select(notes_doc.c.filename, notes_doc.c.data)
    q = (q.where(notes_doc.c.version == version) if version is not None
         else q.order_by(notes_doc.c.version.desc()).limit(1))
    with engine.begin() as conn:
        row = conn.execute(q).first()
    return (row[0], row[1]) if row else (None, None)


def add_notes(filename: str, data: bytes, uploaded_at: str):
    with engine.begin() as conn:
        conn.execute(notes_doc.insert().values(
            filename=filename, data=data, uploaded_at=uploaded_at))


def delete_notes_version(version: int):
    with engine.begin() as conn:
        conn.execute(notes_doc.delete().where(notes_doc.c.version == int(version)))


def get_checklist() -> pd.DataFrame:
    return pd.read_sql(select(checklist).order_by(checklist.c.sort), engine)


def set_checklist_done(key: str, done: bool, done_date=None):
    with engine.begin() as conn:
        conn.execute(checklist.update().where(checklist.c.key == key)
                     .values(done=bool(done), done_date=done_date))
