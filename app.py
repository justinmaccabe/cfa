"""CFA Level II study tracker — the durable, shared record behind the chat tutor.

Run locally:   streamlit run app.py        (uses local SQLite cfa.db, no setup)
Deployed:      set DATABASE_URL secret      (uses Postgres so data persists)

Design note: this app and the chat tutor read/write the SAME database. The app is
where you look; the DB is what the tutor trusts. Neither invents your progress.

Layout: left-sidebar nav (brand + countdown), and a front "Today" page built
around a dated agenda + an exam-runway timeline — deliberately its own identity,
not a portfolio dashboard.
"""
import calendar
import datetime as dt
import glob
import hashlib
import os
import re
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import curriculum as curr
import db

st.set_page_config(page_title="CFA Level II — Study Tracker",
                   page_icon="◆", layout="wide", initial_sidebar_state="expanded")
db.init_db()

# ----------------------------------------------------------------- palette
PRIMARY = "#335765"   # dark slate blue — headers, rules, structure
TEAL    = "#74A8A4"   # muted teal — positive / strength accent
LBLUE   = "#B6D9E0"   # light blue — soft fills
MIST    = "#DBE2DC"   # pale grey-green — soft background
BROWN   = "#7F543D"   # warm brown — weak / attention accent
INK     = "#262E32"   # near-black body text
MUTE    = "#5B6B72"   # muted label grey
TAPER   = "#5E7E86"   # slate-teal — readable runway segment
SERIF   = "'Times New Roman', Georgia, serif"
POS, NEG = TEAL, BROWN
SIGNAL_COLOR = {"below": BROWN, "at": PRIMARY, "above": TEAL}

st.markdown(f"""
<style>
html, body, [class*="css"], .stApp, [data-testid="stSidebar"], h1, h2, h3, h4, h5,
p, div, span, .stMarkdown, [data-testid="stMetricValue"], [data-testid="stMetricLabel"],
[data-testid="stMetricDelta"], button, input, select, textarea, label {{
    font-family: {SERIF} !important;
}}
span[data-testid="stIconMaterial"], [class*="material-symbols"], .material-icons {{
    font-family: "Material Symbols Rounded" !important;
}}
[data-testid="stMetricValue"], [data-testid="stMetricDelta"],
[data-testid="stDataFrame"], .stDataFrame, table {{
    font-variant-numeric: tabular-nums lining-nums !important;
    font-feature-settings: "tnum" 1, "lnum" 1 !important;
}}
.stApp {{ background:#F5F7F6; }}
.block-container {{ padding-top: 2.2rem; }}
#MainMenu, footer {{ visibility: hidden; }}

/* --- sidebar brand ------------------------------------------------ */
[data-testid="stSidebar"] {{ background:{PRIMARY}; }}
[data-testid="stSidebar"] * {{ color:#EAF0EE !important; }}
.side-mark {{ font-family:{SERIF}; font-style:italic; font-size:2.6rem; font-weight:700;
    color:#FFFFFF !important; line-height:1; letter-spacing:.02em; }}
.side-kick {{ color:{LBLUE} !important; letter-spacing:.34em; text-transform:uppercase;
    font-size:.66rem; margin-top:.2rem; }}
.side-count {{ margin:.9rem 0 .2rem; font-size:2rem; color:#FFFFFF !important; font-weight:700; }}
.side-count small {{ font-size:.8rem; color:{LBLUE} !important; font-weight:400; letter-spacing:.06em; }}
.side-phase {{ display:inline-block; margin-top:.5rem; padding:.18rem .6rem; border-radius:20px;
    background:rgba(255,255,255,.14); color:#FFFFFF !important; font-size:.72rem;
    letter-spacing:.1em; text-transform:uppercase; }}
[data-testid="stSidebar"] hr {{ border-color:rgba(255,255,255,.2); }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ font-size:1.02rem !important; padding:.12rem 0; }}

/* --- headings & rules -------------------------------------------- */
h2, h3 {{ color:{INK}; border-left:3px solid {PRIMARY}; padding-left:.55rem; }}
.page-eyebrow {{ color:{TEAL}; letter-spacing:.34em; text-transform:uppercase; font-size:.72rem; }}
.page-title {{ font-size:2.1rem; font-weight:700; color:{INK}; margin:.1rem 0 .1rem; letter-spacing:.02em; }}
.page-rule {{ border:none; border-top:1px solid rgba(51,87,101,.28); margin:.3rem 0 1.2rem; }}

/* --- the agenda card (signature) --------------------------------- */
.agenda {{ background:#FFFFFF; border:1px solid rgba(51,87,101,.18); border-left:5px solid {PRIMARY};
    border-radius:12px; padding:1.1rem 1.4rem 1.2rem; box-shadow:0 2px 10px rgba(51,87,101,.07); }}
.agenda-date {{ font-size:1.5rem; font-weight:700; color:{PRIMARY}; letter-spacing:.01em; }}
.agenda-tag {{ float:right; font-style:italic; color:{MUTE}; font-size:.95rem; }}
.agenda-item {{ display:flex; align-items:baseline; gap:.6rem; padding:.42rem 0;
    border-top:1px dotted rgba(51,87,101,.16); font-size:1.05rem; color:{INK}; }}
.agenda-item:first-of-type {{ border-top:none; }}
.dot {{ flex:0 0 auto; width:9px; height:9px; border-radius:50%; transform:translateY(1px); }}
.agenda-item .meta {{ margin-left:auto; color:{MUTE}; font-size:.86rem; font-style:italic; white-space:nowrap; }}
.agenda-empty {{ color:{MUTE}; font-style:italic; padding:.4rem 0; }}

/* --- the exam runway (signature) --------------------------------- */
.runway {{ position:relative; display:flex; height:36px; border-radius:8px; overflow:hidden;
    border:1px solid rgba(51,87,101,.25); margin:.1rem 0 .1rem; }}
.rw-seg {{ display:flex; align-items:center; justify-content:center; min-width:0; }}
.rw-seg span {{ font-size:.68rem; color:#FFFFFF; letter-spacing:.09em; text-transform:uppercase;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; padding:0 6px;
    text-shadow:0 1px 1px rgba(0,0,0,.18); }}
.rw-marker {{ position:absolute; top:-3px; bottom:-3px; width:2px; background:{INK}; z-index:3; }}
.rw-marker::after {{ content:'TODAY'; position:absolute; top:-15px; left:50%; transform:translateX(-50%);
    font-size:.58rem; letter-spacing:.12em; color:{INK}; background:#F5F7F6; padding:0 3px; }}
.rw-ends {{ display:flex; justify-content:space-between; color:{MUTE}; font-size:.75rem;
    font-style:italic; margin-top:.5rem; }}

[data-testid="stMetric"] {{ background:#FFFFFF; border:1px solid rgba(51,87,101,.18);
    border-radius:10px; padding:14px 18px; box-shadow:0 1px 2px rgba(51,87,101,.06); }}
[data-testid="stMetricLabel"] {{ color:{MUTE} !important; text-transform:uppercase;
    letter-spacing:.12em; font-size:.72rem !important; min-height:2.1em; }}
[data-testid="stMetricValue"] {{ font-size:1.6rem !important; color:{INK}; }}

/* --- calendar grid ------------------------------------------------ */
.cal {{ width:100%; border-collapse:collapse; table-layout:fixed; margin-top:.5rem; }}
.cal th {{ color:{MUTE}; font-size:.68rem; text-transform:uppercase; letter-spacing:.12em;
    padding:.3rem 0; text-align:center; font-weight:700; }}
.cal td {{ border:1px solid rgba(51,87,101,.14); vertical-align:top; height:98px;
    padding:4px 5px; background:#FFFFFF; overflow:hidden; }}
.cal td.out {{ background:#EDF1F0; }}
.cal td.past {{ background:#F3F5F4; }}
.cal td.today {{ background:#EAF2F1; box-shadow:inset 0 0 0 2px {PRIMARY}; }}
.cal .dnum {{ font-size:.78rem; color:{INK}; font-weight:700; }}
.cal td.out .dnum {{ color:#AEB7B5; }}
.cal .chip {{ display:block; font-size:.62rem; line-height:1.4; border-radius:4px;
    padding:1px 5px; margin-top:3px; color:#FFFFFF; white-space:nowrap; overflow:hidden;
    text-overflow:ellipsis; }}
.chip.study {{ background:{PRIMARY}; }}
.chip.review {{ background:{BROWN}; }}
.chip.mile {{ background:{TEAL}; }}
.chip.mock {{ background:{TAPER}; }}
.chip.exam {{ background:{BROWN}; font-weight:700; letter-spacing:.04em; }}
.chip.more {{ background:transparent !important; color:{MUTE}; font-style:italic; }}

/* --- curriculum section table --- */
.cur-topic {{ margin:1.15rem 0 .3rem; padding-left:.5rem; border-left:4px solid {PRIMARY};
    font-size:.72rem; letter-spacing:.16em; text-transform:uppercase; color:{PRIMARY}; font-weight:700; }}
.cur-bk {{ display:inline-block; font-size:.62rem; letter-spacing:.05em; color:{MUTE};
    border:1px solid rgba(51,87,101,.3); border-radius:4px; padding:1px 5px; }}
.cbar {{ display:inline-block; width:65%; height:8px; background:rgba(51,87,101,.12);
    border-radius:5px; overflow:hidden; vertical-align:middle; }}
.cbar-fill {{ display:block; height:100%; background:{TEAL}; }}
.cbar-txt {{ font-size:.72rem; color:{MUTE}; margin-left:.45rem; vertical-align:middle; }}

/* --- resource cards --- */
.rescard {{ border:1px solid rgba(51,87,101,.2); border-left:4px solid {PRIMARY};
    border-radius:10px 10px 0 0; background:#FFFFFF; padding:.7rem .9rem .55rem;
    box-shadow:0 1px 2px rgba(51,87,101,.06); }}
.rescard .rc-name {{ color:{INK}; font-weight:700; font-size:1.02rem; }}
.rescard .rc-meta {{ color:{MUTE}; font-size:.8rem; letter-spacing:.04em; }}
</style>
""", unsafe_allow_html=True)


def _plotly(fig, h=320):
    fig.update_layout(
        template="plotly_white", height=h, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Times New Roman, Georgia, serif", color=INK),
        legend=dict(orientation="h", y=-0.15))
    return fig


# ----------------------------------------------------------------- data + dates
settings = db.get_settings()
today = dt.date.today()


def _d(key, default):
    return pd.to_datetime(settings.get(key, default)).date()


exam_date = _d("exam_date", "2027-05-18")
materials_date = _d("materials_date", "2026-08-12")
consolidation_start = _d("consolidation_start", "2027-02-03")
mock_start = _d("mock_start", "2027-03-03")
taper_start = _d("taper_start", "2027-05-12")
weekly_target = float(settings.get("weekly_hours_target", 12) or 12)
days_to_exam = (exam_date - today).days

# The runway phases (Foundation onward); pre-game is the lead-in before materials.
PHASES = [
    ("Foundation",    materials_date,      consolidation_start, PRIMARY),
    ("Consolidation", consolidation_start, mock_start,          TEAL),
    ("Mocks",         mock_start,          taper_start,         BROWN),
    ("Taper",         taper_start,         exam_date,           TAPER),
]


def current_phase():
    if today < materials_date:
        return "Pre-game"
    for name, s, e, _c in PHASES:
        if s <= today < e:
            return name
    return "Exam week" if today <= exam_date else "Done"


phase = current_phase()


def expected_progress(as_of=None):
    """Where each topic *should* be by `as_of`, and the overall elapsed fraction of
    the content window. Model: lay the non-parallel topics end-to-end across the
    content window (materials_date -> consolidation_start), each occupying a slice
    sized by its CFA weight, in our STUDY_ORDER. A topic's expected % is how far
    'today' has moved through its own slice. Ethics (parallel, order 99) is spread
    linearly across the whole window. Mirrors the xlsx planner's paced dates."""
    as_of = as_of or today
    span = max((consolidation_start - materials_date).days, 1)
    ef = min(max((as_of - materials_date).days, 0), span) / span
    seq = sorted([t for t in curr.TOPICS if curr.STUDY_ORDER.get(t, 50) < 90],
                 key=lambda t: curr.STUDY_ORDER[t])
    w = {t: sum(curr.TOPIC_WEIGHTS[t]) / 2 for t in seq}
    tot = sum(w.values()) or 1
    exp, c = {}, 0.0
    for t in seq:
        s, e = c, c + w[t] / tot
        exp[t] = 0.0 if ef <= s else (1.0 if ef >= e else (ef - s) / (e - s))
        c = e
    for t in curr.TOPICS:            # parallel topics (Ethics) track the window linearly
        exp.setdefault(t, ef)
    return exp, ef


mods = db.get_modules_df()
log = db.get_study_log_df()
mocks_df = db.get_mocks_df()
queue = db.review_queue(today)


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(f"""
    <div class="side-mark">CFA <span style="color:{LBLUE}">II</span></div>
    <div class="side-kick">Level II &middot; May 2027</div>
    <div class="side-count">{max(days_to_exam,0)}<small> days to exam</small></div>
    <span class="side-phase">{phase} phase</span>
    <hr>
    """, unsafe_allow_html=True)
    page = st.radio("Go to", ["Today", "Calendar", "Curriculum", "Reviews",
                              "Drill Log", "Mocks", "Analytics", "Notes", "Resources"],
                    label_visibility="collapsed")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption(f"{settings.get('candidate_name','')}  ·  target {weekly_target:.0f} h/wk")


def page_header(eyebrow, title):
    st.markdown(f'<div class="page-eyebrow">{eyebrow}</div>'
                f'<div class="page-title">{title}</div><hr class="page-rule">',
                unsafe_allow_html=True)


# ================================================================= TODAY
def todays_agenda():
    """Priority-ordered list of (color, text, meta) for the day."""
    items = []
    if phase == "Pre-game":
        n = (materials_date - today).days
        items.append((MUTE, f"Pre-game — official materials unlock in {n} days "
                            f"({materials_date:%b %d}).", "logistics"))
        items.append((PRIMARY, "Set an early-registration reminder — save $350 if you "
                              "register by ~Oct 14.", "logistics"))
        items.append((TEAL, "Calculator ready (BA II Plus); freeze the tracker before Aug 12.",
                     "logistics"))
        first = mods.sort_values(["study_order", "id"]).iloc[0]
        items.append((PRIMARY, f"First up when content starts: {first['name']}",
                     f"Quant · Book {int(first['book'])}"))
        return items
    # reviews first — spaced retrieval is the highest-leverage thing on any given day
    if not queue.empty:
        for _, r in queue.iterrows():
            when = "overdue" if r["days_overdue"] > 0 else "due today"
            items.append((BROWN, f"Review ({r['review']}): {r['module']}",
                         f"{r['topic']} · {when}"))
    # continue what's open
    inprog = mods[mods["status"] == "In Progress"]
    for _, r in inprog.iterrows():
        items.append((TEAL, f"Continue: {r['name']}", f"{r['topic']} · Book {int(r['book'])}"))
    # otherwise, point at the next module in our study order
    if inprog.empty:
        nxt = mods[mods["status"] == "Not Started"].sort_values(["study_order", "id"])
        if not nxt.empty:
            r = nxt.iloc[0]
            items.append((PRIMARY, f"Start next: {r['name']}",
                         f"{r['topic']} · Book {int(r['book'])}"))
    return items


def runway_html():
    total = max((exam_date - materials_date).days, 1)
    segs = ""
    for name, s, e, color in PHASES:
        w = max((e - s).days, 0) / total * 100
        segs += f'<div class="rw-seg" style="width:{w:.2f}%;background:{color}"><span>{name}</span></div>'
    frac = (today - materials_date).days / total
    frac = min(max(frac, 0), 1)
    marker = f'<div class="rw-marker" style="left:{frac*100:.2f}%"></div>' if today >= materials_date else ""
    return (f'<div class="runway">{segs}{marker}</div>'
            f'<div class="rw-ends"><span>Materials · {materials_date:%b %d, %Y}</span>'
            f'<span>Exam · {exam_date:%b %d, %Y}</span></div>')


def page_today():
    page_header("Daily brief", f"{today:%A}, {today:%B %-d}")

    agenda = todays_agenda()
    rows = ""
    for color, text, meta in agenda:
        rows += (f'<div class="agenda-item"><span class="dot" style="background:{color}"></span>'
                 f'<span>{text}</span><span class="meta">{meta}</span></div>')
    if not rows:
        rows = '<div class="agenda-empty">Nothing queued — log a session or set a module in progress.</div>'
    st.markdown(f"""
    <div class="agenda">
      <div><span class="agenda-date">On the agenda</span>
      <span class="agenda-tag">{phase} phase</span></div>
      {rows}
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.markdown("##### Exam runway")
    st.markdown(runway_html(), unsafe_allow_html=True)

    st.write("")
    done = int((mods["status"] == "Done").sum())
    in_prog = int((mods["status"] == "In Progress").sum())
    week_start = today - dt.timedelta(days=today.weekday())
    hrs_week = 0.0
    if not log.empty:
        lg = log.copy(); lg["date"] = pd.to_datetime(lg["date"]).dt.date
        hrs_week = lg[lg["date"] >= week_start]["minutes"].sum() / 60
    overdue = 0 if queue.empty else int((queue["days_overdue"] > 0).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Modules complete", f"{done} / 45", f"{done/45*100:.0f}%")
    c2.metric("In progress", in_prog)
    c3.metric("Hours this week", f"{hrs_week:.1f}", f"target {weekly_target:.0f}")
    c4.metric("Reviews due", 0 if queue.empty else len(queue),
              f"{overdue} overdue" if overdue else "on track", delta_color="inverse")

    st.subheader("Pace by topic")
    exp, ef = expected_progress()
    rows = []
    for t in curr.TOPICS:
        sub = mods[mods["topic"] == t]
        pct = (sub["status"] == "Done").mean() * 100 if len(sub) else 0
        lo, hi = curr.TOPIC_WEIGHTS[t]
        rows.append(dict(Topic=t, Done=pct, Expected=exp[t] * 100, Weight=(lo + hi) / 2,
                         Signal=curr.L1_SIGNAL.get(t, "at"), Order=curr.STUDY_ORDER.get(t, 50)))
    prog = pd.DataFrame(rows).sort_values("Order")
    fig = px.bar(prog, x="Done", y="Topic", orientation="h", color="Signal",
                 color_discrete_map=SIGNAL_COLOR, category_orders={"Topic": list(prog["Topic"])},
                 labels={"Done": "% complete"}, hover_data={"Weight": ":.0f"})
    fig.add_trace(go.Scatter(x=prog["Expected"], y=prog["Topic"], mode="markers",
                             marker=dict(symbol="diamond-tall", size=12, color=INK,
                                         line=dict(color="#FFFFFF", width=1)),
                             name="required by today",
                             hovertemplate="should be %{x:.0f}% by today<extra></extra>"))
    fig.update_xaxes(range=[0, 100])
    st.plotly_chart(_plotly(fig, 400), use_container_width=True)

    nmods = mods.groupby("topic")["id"].count().to_dict()
    exp_mods = sum(exp[t] * nmods.get(t, 0) for t in curr.TOPICS)
    done_mods = int((mods["status"] == "Done").sum())
    gap = done_mods - exp_mods
    if ef <= 0:
        verdict = "content phase hasn't started — nothing required yet"
    elif gap >= -0.5:
        verdict = f"on or ahead of pace (+{gap:.1f} modules)"
    else:
        verdict = f":red[{-gap:.1f} modules behind pace]"
    st.caption(f"**◆ = required progress by today** (paced from your plan). "
               f"Completed **{done_mods}** of 45; pace expects ~**{exp_mods:.1f}** → {verdict}.  \n"
               "Bar colour = Level I signal: brown below · slate at · teal above the candidate average.")


# ================================================================= CURRICULUM
@st.dialog("Sub-readings", width="large")
def section_dialog(sec_id, sec_name, topic):
    st.markdown(f"<span class='page-eyebrow'>{topic}</span><br><b>{sec_name}</b>",
                unsafe_allow_html=True)
    subs = db.submodules_for_section(sec_id)
    show = subs[["id", "code", "name", "status", "confidence", "date_completed",
                 "r1_done", "r2_done", "r3_done", "notes"]].copy()
    show["date_completed"] = pd.to_datetime(show["date_completed"]).dt.date
    edited = st.data_editor(
        show, width="stretch", hide_index=True, key=f"subed_{sec_id}",
        column_config={
            "id": None,
            "code": st.column_config.TextColumn("#", disabled=True, width="small"),
            "name": st.column_config.TextColumn("Sub-reading", disabled=True, width="large"),
            "status": st.column_config.SelectboxColumn(
                "Status", options=["Not Started", "In Progress", "Done"], width="small"),
            "confidence": st.column_config.NumberColumn("Conf", min_value=1, max_value=5, step=1, width="small"),
            "date_completed": st.column_config.DateColumn("Completed", width="small"),
            "r1_done": st.column_config.CheckboxColumn("R1", width="small"),
            "r2_done": st.column_config.CheckboxColumn("R2", width="small"),
            "r3_done": st.column_config.CheckboxColumn("R3", width="small"),
            "notes": st.column_config.TextColumn("Notes", width="medium"),
        })
    st.caption("Completing a sub-reading arms its +3 / +14 / +45-day reviews (Reviews tab); "
               "R1–R3 tick them off. Section progress rolls up automatically.")
    if st.button("Save", type="primary", key=f"savesub_{sec_id}"):
        orig, n = show.set_index("id"), 0
        for _, r in edited.iterrows():
            o, ch = orig.loc[r["id"]], {}
            for col in ["status", "confidence", "date_completed", "notes",
                        "r1_done", "r2_done", "r3_done"]:
                new, old = r[col], o[col]
                if pd.isna(new) and pd.isna(old):
                    continue
                if new != old:
                    ch[col] = (None if pd.isna(new)
                               else bool(new) if col.startswith("r") else new)
            if ch:
                db.update_submodule(int(r["id"]), **ch)
                n += 1
        st.success(f"Saved {n} change(s).")
        st.rerun()


def _bar(done, tot):
    pct = int(done / tot * 100) if tot else 0
    return (f"<div class='cbar'><div class='cbar-fill' style='width:{pct}%'></div></div>"
            f"<span class='cbar-txt'>{done}/{tot}</span>")


def page_curriculum():
    page_header("The map", "Curriculum · 45 sections → 171 sub-readings")
    st.caption("Each row is a section. **Open** it to check off its Schweser sub-readings — "
               "section progress, the calendar and the pace bars all roll up from what you do there.")
    subs_all = db.get_submodules_df()
    cur_topic = None
    for _, s in mods.sort_values(["study_order", "id"]).iterrows():
        if s["topic"] != cur_topic:
            cur_topic = s["topic"]
            sig = curr.L1_SIGNAL.get(cur_topic, "at")
            st.markdown(f"<div class='cur-topic' style='border-color:{SIGNAL_COLOR[sig]}'>"
                        f"{cur_topic}</div>", unsafe_allow_html=True)
        sub = subs_all[subs_all["section_id"] == s["id"]]
        done, tot = int((sub["status"] == "Done").sum()), len(sub)
        c = st.columns([0.7, 6, 2, 1.3], vertical_alignment="center")
        c[0].markdown(f"<span class='cur-bk'>Bk {int(s['book'])}</span>", unsafe_allow_html=True)
        c[1].markdown(f"**{s['name']}**")
        c[2].markdown(_bar(done, tot), unsafe_allow_html=True)
        if c[3].button("Open ▸", key=f"open_{s['id']}", width="stretch"):
            section_dialog(int(s["id"]), s["name"], s["topic"])


# ================================================================= REVIEWS
def page_reviews():
    page_header("Spaced retrieval", "Review queue")
    st.caption("Reviews = practice questions from memory, then check — not a re-read. "
               "Tracked per sub-reading; mark done as you clear them.")
    full_q = db.review_queue(today + dt.timedelta(days=7))
    if full_q.empty:
        st.write("Nothing scheduled yet — complete a sub-reading (Curriculum → open a section) "
                 "to start the clock.")
        return
    for _, r in full_q.iterrows():
        tag = (f":red[{r['days_overdue']}d overdue]" if r["days_overdue"] > 0
               else (":orange[due today]" if r["days_overdue"] == 0
                     else f":gray[in {-r['days_overdue']}d]"))
        cols = st.columns([5, 1.4, 1.4, 1.2], vertical_alignment="center")
        cols[0].write(f"**{r['module']}**  \n:gray[{r['topic']} · {r['section']} · {r['review']}]")
        cols[1].write(f"{r['due']:%b %d}")
        cols[2].write(tag)
        if cols[3].button("Done", key=f"rev_{r['sub_id']}_{r['review']}"):
            db.update_submodule(int(r["sub_id"]), **{f"{r['review'].lower()}_done": True})
            db.log_study(today, r["topic"], "Review", source="review-queue",
                         notes=f"{r['module']} {r['review']} complete")
            st.rerun()


# ================================================================= DRILL LOG
def page_drill():
    page_header("Practice", "Drill log")
    with st.form("drill_form", clear_on_submit=True):
        c = st.columns(4)
        d_date = c[0].date_input("Date", today)
        d_topic = c[1].selectbox("Topic", curr.TOPICS)
        d_act = c[2].selectbox("Activity", ["Practice", "Read", "Review", "Class", "Other"])
        d_min = c[3].number_input("Minutes", min_value=0, value=30, step=5)
        c2 = st.columns(4)
        d_predict = c2[0].number_input("Predicted % (gut feel)", 0, 100, 60, 5,
                                       help="Your guess BEFORE grading — powers the calibration chart")
        d_nq = c2[1].number_input("Questions", min_value=0, value=0, step=1)
        d_nc = c2[2].number_input("Correct", min_value=0, value=0, step=1)
        d_src = c2[3].selectbox("Source", ["Claude", "CFAI QBank", "Schweser", "Mock", "Other"])
        d_notes = st.text_input("Notes", "")
        if st.form_submit_button("Log it", type="primary"):
            db.log_study(d_date, d_topic, d_act, minutes=d_min,
                         num_q=d_nq or None, num_correct=d_nc or None,
                         predicted=d_predict, source=d_src, notes=d_notes or None)
            st.success("Logged.")
            st.rerun()

    st.subheader("Recent sessions")
    if log.empty:
        st.write("No sessions logged yet.")
        return
    disp = log.copy()
    disp["date"] = pd.to_datetime(disp["date"]).dt.date
    disp["acc %"] = (disp["num_correct"] / disp["num_q"] * 100).round(0)
    st.dataframe(disp[["date", "topic", "activity", "minutes", "num_q", "num_correct",
                       "acc %", "predicted", "source", "notes"]].sort_values("date", ascending=False),
                 width="stretch", hide_index=True, height=300)


# ================================================================= MOCKS
def page_mocks():
    page_header("Under exam conditions", "Mock exams")
    with st.form("mock_form", clear_on_submit=True):
        c = st.columns(4)
        m_date = c[0].date_input("Date", today, key="m_date")
        m_src = c[1].text_input("Source", "CFAI Mock A")
        m_score = c[2].number_input("Score %", 0.0, 100.0, 65.0, 0.5)
        m_time = c[3].number_input("Minutes used", 0, 300, 132)
        m_weak = st.text_input("Weakest topics", "")
        m_action = st.text_input("Action items", "")
        if st.form_submit_button("Add mock", type="primary"):
            db.add_mock(m_date, m_src, m_score, m_time, m_weak or None, m_action or None)
            st.success("Mock added.")
            st.rerun()

    if mocks_df.empty:
        return
    md = mocks_df.copy()
    md["date"] = pd.to_datetime(md["date"]).dt.date
    fig = px.line(md, x="date", y="score_pct", markers=True,
                  labels={"score_pct": "Score %", "date": ""})
    fig.update_traces(line_color=PRIMARY)
    fig.add_hline(y=70, line_dash="dot", line_color=TEAL, annotation_text="70% comfort line")
    st.plotly_chart(_plotly(fig), use_container_width=True)
    st.dataframe(md[["date", "source", "score_pct", "minutes_used",
                     "weak_topics", "action_items", "reviewed"]],
                 width="stretch", hide_index=True)


# ================================================================= ANALYTICS
def page_analytics():
    page_header("Where the points are", "Analytics")
    graded = log[log["num_q"].notna() & (log["num_q"] > 0)].copy() if not log.empty else pd.DataFrame()

    st.subheader("Topic mastery")
    if graded.empty:
        st.write("Log some graded practice sets and this fills in — accuracy by topic, "
                 "plus whether your confidence matches reality.")
    else:
        graded["acc"] = graded["num_correct"] / graded["num_q"] * 100
        by_t = (graded.groupby("topic")
                .apply(lambda g: pd.Series({
                    "accuracy": (g["num_correct"].sum() / g["num_q"].sum() * 100),
                    "questions": int(g["num_q"].sum())}))
                .reset_index())
        by_t["signal"] = by_t["topic"].map(curr.L1_SIGNAL)
        fig = px.bar(by_t.sort_values("accuracy"), x="accuracy", y="topic", orientation="h",
                     color="signal", color_discrete_map=SIGNAL_COLOR,
                     hover_data={"questions": True}, labels={"accuracy": "Accuracy %"})
        fig.add_vline(x=70, line_dash="dot", line_color=PRIMARY)
        fig.update_xaxes(range=[0, 100])
        st.plotly_chart(_plotly(fig, 380), use_container_width=True)

        st.subheader("Confidence calibration")
        st.caption("Above the line = you underestimate yourself; below = overconfident. "
                   "For a re-taker, the overconfident topics are where points quietly leak.")
        cal = graded[graded["predicted"].notna()].copy()
        if cal.empty:
            st.write("Add a *predicted %* when you log a set to unlock this.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines",
                                     line=dict(dash="dot", color=TEAL), name="perfect calibration"))
            fig.add_trace(go.Scatter(x=cal["predicted"], y=cal["acc"], mode="markers",
                                     marker=dict(size=11, color=PRIMARY), text=cal["topic"],
                                     name="your sets",
                                     hovertemplate="%{text}<br>predicted %{x}%<br>actual %{y:.0f}%"))
            fig.update_layout(xaxis_title="Predicted %", yaxis_title="Actual %")
            fig.update_xaxes(range=[0, 100]); fig.update_yaxes(range=[0, 100])
            st.plotly_chart(_plotly(fig), use_container_width=True)

    st.subheader("Study hours by week")
    if log.empty:
        st.write("No hours logged yet.")
        return
    h = log.copy()
    h["date"] = pd.to_datetime(h["date"])
    h["week"] = h["date"].dt.to_period("W").dt.start_time
    wk = h.groupby("week")["minutes"].sum().reset_index()
    wk["hours"] = wk["minutes"] / 60
    fig = px.bar(wk, x="week", y="hours", labels={"hours": "Hours", "week": ""})
    fig.update_traces(marker_color=PRIMARY)
    fig.add_hline(y=weekly_target, line_dash="dot", line_color=TEAL,
                  annotation_text=f"{weekly_target:.0f} h target")
    st.plotly_chart(_plotly(fig), use_container_width=True)


# ================================================================= CALENDAR
ABBR = {"Quantitative Methods": "QM", "Economics": "ECON",
        "Financial Statement Analysis": "FSA", "Corporate Issuers": "CI",
        "Equity Investments": "EQ", "Fixed Income": "FI", "Derivatives": "DER",
        "Alternative Investments": "ALT", "Portfolio Management": "PM", "Ethics": "ETH"}


def build_events():
    """date -> [(kind, text)] for everything scheduled between materials and exam:
    weight-paced module study-days (same model as the runway/pace bars), spaced
    reviews off completions, phase milestones, and suggested mock slots."""
    ev = {}

    def add(d, kind, text):
        ev.setdefault(d, []).append((kind, text))

    add(materials_date, "mile", "Materials unlock")
    add(dt.date(2026, 10, 14), "mile", "Early-reg deadline")
    add(consolidation_start, "mile", "Consolidation buffer")
    add(mock_start, "mile", "Mocks begin")
    add(taper_start, "mile", "Taper begins")
    add(exam_date, "exam", "EXAM DAY")

    span = max((consolidation_start - materials_date).days, 1)
    n_by_topic = mods.groupby("topic")["id"].count().to_dict()
    seq = mods[mods["study_order"] < 90].sort_values(["study_order", "id"])
    wts = [(sum(curr.TOPIC_WEIGHTS[r["topic"]]) / 2) / n_by_topic[r["topic"]]
           for _, r in seq.iterrows()]
    total = sum(wts) or 1
    cum = 0.0
    for (_, r), wt in zip(seq.iterrows(), wts):
        d = materials_date + dt.timedelta(days=round(cum / total * span))
        add(d, "study", f"{ABBR[r['topic']]} · {r['name']}")
        cum += wt
    for i, (_, r) in enumerate(mods[mods["study_order"] >= 90].sort_values("id").iterrows()):
        frac = [0.30, 0.60, 0.90][i] if i < 3 else 0.9
        add(materials_date + dt.timedelta(days=round(frac * span)),
            "study", f"ETH · {r['name']}")

    # (spaced reviews are tracked at the sub-module level on the Reviews tab, not
    # here — the calendar deliberately stays at the coarser section level.)
    d = mock_start
    while d < taper_start:
        add(d, "mock", "Suggested mock")
        d += dt.timedelta(days=14)
    return ev


def month_html(year, month, ev):
    cal = calendar.Calendar(firstweekday=0)
    out = ['<table class="cal"><thead><tr>']
    out += [f"<th>{w}</th>" for w in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]
    out.append("</tr></thead><tbody>")
    for week in cal.monthdatescalendar(year, month):
        out.append("<tr>")
        for d in week:
            cls = []
            if d.month != month:
                cls.append("out")
            elif d == today:
                cls.append("today")
            elif d < today:
                cls.append("past")
            items = ev.get(d, [])
            chips = "".join(f'<span class="chip {k}">{t}</span>' for k, t in items[:3])
            if len(items) > 3:
                chips += f'<span class="chip more">+{len(items) - 3} more</span>'
            out.append(f'<td class="{" ".join(cls)}"><span class="dnum">{d.day}</span>{chips}</td>')
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def page_calendar():
    page_header("The plan, day by day", "Calendar")
    ev = build_events()
    months, y, m = [], today.year, today.month
    while (y, m) <= (exam_date.year, exam_date.month):
        months.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    labels = [dt.date(yy, mm, 1).strftime("%B %Y") for (yy, mm) in months]
    sel = st.selectbox("Month", range(len(months)), format_func=lambda k: labels[k])
    st.markdown(
        f'<div style="margin:.1rem 0;font-size:.75rem;color:{MUTE}">'
        f'<span class="chip study" style="display:inline-block">study</span> '
        f'<span class="chip review" style="display:inline-block">review</span> '
        f'<span class="chip mock" style="display:inline-block">mock</span> '
        f'<span class="chip mile" style="display:inline-block">milestone</span></div>',
        unsafe_allow_html=True)
    yy, mm = months[sel]
    st.markdown(month_html(yy, mm, ev), unsafe_allow_html=True)

    rows = sorted((d, k, t) for d, its in ev.items() for (k, t) in its
                  if d.year == yy and d.month == mm)
    if rows:
        st.markdown("##### This month, in order")
        for d, k, t in rows:
            st.markdown(f"- **{d:%a %b %-d}** · :gray[{k}] — {t}")


# ================================================================= access gate
def require_unlock():
    """Password gate for materials + notes. The SHA-256 hash lives in the DB, so the
    password is set once and syncs across devices; no plaintext is ever stored."""
    h = settings.get("resources_pw_sha256") or ""
    if not h:
        st.info("Set a password to protect your materials — only you'll know it. "
                "It syncs across your devices and can be changed later.")
        p = st.text_input("Create a password", type="password", key="pw_set")
        if st.button("Set password", type="primary") and p:
            db.set_setting("resources_pw_sha256", hashlib.sha256(p.encode()).hexdigest())
            st.session_state.unlocked = True
            st.rerun()
        return False
    if st.session_state.get("unlocked"):
        return True
    p = st.text_input("Password", type="password", key="pw_in")
    if st.button("Unlock", type="primary"):
        if hashlib.sha256(p.encode()).hexdigest() == h:
            st.session_state.unlocked = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# ================================================================= NOTES (living Word doc)
def _starter_docx() -> bytes:
    from docx import Document
    doc = Document()
    doc.add_heading("CFA Level II — Study Notes", 0)
    doc.add_paragraph("Living notes: download → edit in Word → upload to override. "
                      "The app keeps every version.")
    last = None
    for _, r in mods.sort_values(["study_order", "id"]).iterrows():
        if r["topic"] != last:
            doc.add_heading(r["topic"], level=1)
            last = r["topic"]
        doc.add_heading(r["name"], level=2)
        doc.add_paragraph("")
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def page_notes():
    page_header("Cross-device workspace", "Notes")
    if not require_unlock():
        return
    fname, data = db.get_notes()
    st.caption("Your living notes doc. **Download** it, edit in Word, then **upload** to "
               "override — every session builds on the last, on any computer. Past versions "
               "are kept as a safety net.")
    c1, c2 = st.columns([1, 1])
    if data:
        c1.download_button(f"⬇  Download current · {fname}", data=data, file_name=fname,
                           mime=DOCX_MIME, width="stretch")
    else:
        if c1.button("Generate starter doc", type="primary", width="stretch"):
            db.add_notes("CFA-L2-Notes.docx", _starter_docx(),
                         dt.datetime.now().isoformat(timespec="minutes"))
            st.success("Starter doc created — download it below.")
            st.rerun()
    up = st.file_uploader("Upload a new version (overrides current)", type=["docx"])
    if up is not None and c2.button("Save as current version", type="primary", width="stretch"):
        db.add_notes(up.name, up.getvalue(), dt.datetime.now().isoformat(timespec="minutes"))
        st.success("Saved — this is now your current version.")
        st.rerun()

    vers = db.notes_versions()
    if not vers.empty:
        st.markdown("<hr class='page-rule'>", unsafe_allow_html=True)
        st.markdown("##### Version history")
        for _, v in vers.iterrows():
            cols = st.columns([3, 2, 1.5])
            cols[0].write(f"**v{int(v['version'])}** · {v['filename']}")
            cols[1].write(f":gray[{str(v['uploaded_at']).replace('T', ' ')}]")
            _, vdata = db.get_notes(int(v["version"]))
            cols[2].download_button("Download", data=vdata, file_name=v["filename"],
                                    key=f"nv_{v['version']}", mime=DOCX_MIME)


# ================================================================= RESOURCES
# Files live in the DB (not the git repo), so they travel to every device via
# Postgres and stay behind your password. Personal cross-device access only.
RESOURCES_DIR = os.environ.get("CFA_RESOURCES_DIR", os.path.expanduser("~/Desktop/CFA"))
RESOURCE_EXTS = (".pdf", ".xlsx", ".xlsm", ".csv", ".png", ".jpg", ".jpeg")
_MIMES = {".pdf": "application/pdf",
          ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def _res_kind(name):
    """(group label, sort key, icon) for a resource, so the grid reads tidily."""
    n = name.lower()
    if n.endswith((".png", ".jpg", ".jpeg")):
        return ("Level I result", 3, "🎯")
    if n.endswith((".xlsx", ".xlsm", ".csv")):
        return ("Study planner", 2, "📊")
    if "quicksheet" in n:
        return ("Quicksheet", 1, "⚡")
    return ("Reading material", 0, "📕")


def page_resources():
    page_header("Reference", "Resources")
    if not require_unlock():
        return
    st.caption("Your materials, stored in the app database so they follow you to every device "
               "you deploy to — behind your password, for your personal use only.")
    have = db.list_resources()
    if not have.empty:
        have = have.assign(_sort=[_res_kind(n)[1] for n in have["name"]]) \
                   .sort_values(["_sort", "name"]).reset_index(drop=True)
        rows = list(have.iterrows())
        for i in range(0, len(rows), 2):
            cols = st.columns(2)
            for col, (_, r) in zip(cols, rows[i:i + 2]):
                grp, _s, icon = _res_kind(r["name"])
                ext = os.path.splitext(r["name"])[1].lower()
                with col:
                    st.markdown(
                        f"<div class='rescard'><span class='rc-name'>{icon}&nbsp; {r['name']}</span>"
                        f"<br><span class='rc-meta'>{grp} · {r['size'] / 1e6:.1f} MB</span></div>",
                        unsafe_allow_html=True)
                    st.download_button("Download", data=db.get_resource(r["name"]),
                                       file_name=r["name"],
                                       mime=_MIMES.get(ext, "application/octet-stream"),
                                       key=f"res_{r['name']}", width="stretch")
        st.markdown("<hr class='page-rule'>", unsafe_allow_html=True)

    if os.path.isdir(RESOURCES_DIR):
        st.caption(f"Local folder detected — `{RESOURCES_DIR}`")
        if st.button("Load / refresh files from my CFA folder into the app"):
            files = [f for f in glob.glob(os.path.join(RESOURCES_DIR, "**", "*"), recursive=True)
                     if f.lower().endswith(RESOURCE_EXTS)]
            now = dt.datetime.now().isoformat(timespec="minutes")
            for f in files:
                with open(f, "rb") as fh:
                    db.upsert_resource(os.path.basename(f), fh.read(), now)
            st.success(f"Loaded {len(files)} file(s) into the app database.")
            st.rerun()
    elif have.empty:
        st.info("No materials loaded yet. Run the app locally (where your CFA folder lives), "
                "unlock, and use the loader to push them into the database once — then they're "
                "available wherever you deploy.")


# ----------------------------------------------------------------- dispatch
{"Today": page_today, "Calendar": page_calendar, "Curriculum": page_curriculum,
 "Reviews": page_reviews, "Drill Log": page_drill, "Mocks": page_mocks,
 "Analytics": page_analytics, "Notes": page_notes, "Resources": page_resources}[page]()
