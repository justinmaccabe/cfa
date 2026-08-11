"""Regenerate los_2027.py from the official CFA Institute topic-outline PDF.

    python3 extract_los.py ~/Downloads/2027-cfa_l2_topic_outline.pdf

A dev-time tool, not part of the app: the app reads the generated los_2027.py, so
nothing at runtime depends on the PDF or on poppler being installed. Re-run it when
CFA Institute publishes the next outline (the 2028 edition should parse unchanged —
the anchors below are the document's own structure, not page coordinates).

How the PDF text is shaped, and the three anchors this relies on:

    2027 Level II Topic Outlines      <- HEAD: begins a topic-area section
    <topic name>                      <- may wrap over two lines
    LEARNING OUTCOMES                 <- MARK
    <learning-module name>            <- usually one line, occasionally two
    The candidate should be able to:  <- CUE
    □ los text, wrapping onto
      indented continuation lines
    □ ...

So: a topic name is whatever sits between HEAD and MARK; an LM name is the block of
non-blank lines directly above a CUE (a blank line always separates it from the
preceding bullet, which is what lets us tell the two apart); every other non-bullet
line continues the current bullet. Bullets wrap across page breaks, hence stripping
page furniture *before* the walk rather than during it.

The official outline is finer-grained than our reading list in two places, so 51 LMs
fold into 42 readings: Quant reading 1 is four official LMs, and Ethics reading 41 is
seven (one per Standard). Both folds are asserted at the end of a run — if a future
outline restructures anything, this fails loudly instead of silently dropping LOS.
"""
import os
import re
import subprocess
import sys

import curriculum as curr

HEAD = "2027 Level II Topic Outlines"
MARK = "LEARNING OUTCOMES"
CUE = "The candidate should be able to:"

# Running head/foot labels: the curriculum *volume* names, which differ from the
# topic-section headers for three areas (Corporate Finance / Equities / Portfolio
# Construction) and from our own topic labels for four.
RUNNING = {"Quantitative Methods", "Economics", "Financial Statement Analysis",
           "Corporate Finance", "Equities", "Fixed Income", "Derivatives",
           "Alternative Investments", "Portfolio Construction",
           "Ethical and Professional Standards"}

# Official LM name -> our name in curriculum.MODULES, where the wording differs.
LM_ALIAS = {
    "Environmental, Social, and Governance (ESG) Considerations in Investment Analysis":
        "ESG Considerations in Investment Analysis",
}

# Expected folds, asserted after parsing: reading_no -> number of official LMs.
EXPECTED_FOLDS = {1: 4, 41: 7}
EXPECTED = {"topics": 10, "lms": 51, "los": 382}


def pdf_lines(path):
    """PDF -> stripped text lines with page furniture removed."""
    try:
        raw = subprocess.run(["pdftotext", "-layout", path, "-"],
                             capture_output=True, text=True, check=True).stdout
    except FileNotFoundError:
        sys.exit("need `pdftotext` (brew install poppler)")

    def is_junk(ln):
        s = ln.strip()
        if "CFA Institute" in s and "candidate use only" in s:
            return True
        # running head/foot: "2   Quantitative Methods" | "Quantitative Methods    3"
        m = re.match(r"^(\d+)\s{2,}(.+)$", s) or re.match(r"^(.+?)\s{2,}(\d+)$", s)
        if m:
            core = (m.group(2) if m.group(1).isdigit() else m.group(1)).strip()
            return core in RUNNING
        return False

    return [ln.strip() for ln in raw.splitlines() if not is_junk(ln)]


def lm_name_blocks(lines):
    """{first-line index -> joined LM name} for every learning-module heading.

    Walks back from each CUE to the blank line above it, stopping early at a bullet
    or a marker so a bullet's continuation line can never be mistaken for a name.
    Nearly all names are one line; "Guidance for Standard VII: Responsibilities as a
    / CFA Institute Member or CFA Candidate" is the one that wraps.
    """
    names, owned = {}, set()
    for i, s in enumerate(lines):
        if s != CUE:
            continue
        block, j = [], i - 1
        while j >= 0 and not lines[j]:
            j -= 1
        while (j >= 0 and lines[j] and not lines[j].startswith("□")
               and lines[j] not in (MARK, HEAD, CUE)):
            block.append(j)
            j -= 1
        if block:
            block.reverse()
            names[block[0]] = _tidy(" ".join(lines[k] for k in block))
            owned.update(block)
    return names, owned


def _tidy(s):
    return re.sub(r"\s+", " ", s).strip()


def parse(lines):
    """-> [{topic, lm, los: [...]}] in document order."""
    names, owned = lm_name_blocks(lines)
    out, topic, lm, bullets, cur = [], None, None, [], None

    def close_bullet():
        nonlocal cur
        if cur:
            bullets.append(_tidy(cur))
        cur = None

    def flush_lm():
        nonlocal lm, bullets
        close_bullet()
        if lm:
            out.append({"topic": topic, "lm": lm, "los": bullets})
        lm, bullets = None, []

    i = 0
    while i < len(lines):
        s = lines[i]
        if not s or s in (MARK, CUE):
            i += 1
            continue

        if s == HEAD:                      # topic name runs from here until MARK
            flush_lm()
            parts, j = [], i + 1
            while j < len(lines) and lines[j] != MARK:
                if lines[j] and j not in owned:
                    parts.append(lines[j])
                j += 1
            topic = _tidy(" ".join(parts))
            i = j + 1
            continue

        if i in owned:
            if i in names:                 # first line of a name block
                flush_lm()
                lm = names[i]
            i += 1
            continue

        if s.startswith("□"):
            close_bullet()
            cur = s.lstrip("□").strip()
        elif cur is not None:              # continuation of the current bullet
            cur += " " + s
        i += 1

    flush_lm()
    return out


def fold_to_readings(records):
    """Attach each official LM to one of our 42 readings -> [(rd, lm, seq, text)]."""
    by_name = {n: rd for (_t, n, _bk, rd) in curr.MODULES}
    guidance_rd = by_name["Guidance for Standards I-VII"]

    rows, seq = [], {}
    for r in records:
        name = LM_ALIAS.get(r["lm"], r["lm"])
        if name in by_name:
            rd = by_name[name]
        elif re.match(r"^Guidance for Standard [IV]+\b", name):
            rd = guidance_rd               # seven official Standard LMs, one reading
        else:
            sys.exit(f"unmapped learning module: {r['lm']!r}\n"
                     f"add it to curriculum.MODULES or to LM_ALIAS above")
        for text in r["los"]:
            seq[rd] = seq.get(rd, 0) + 1
            rows.append((rd, r["lm"], seq[rd], text))
    return rows


def verify(records, rows):
    topics = {r["topic"] for r in records}
    got = {"topics": len(topics), "lms": len(records), "los": len(rows)}
    if got != EXPECTED:
        sys.exit(f"structure changed: expected {EXPECTED}, got {got}.\n"
                 "The outline has been restructured — reconcile curriculum.MODULES "
                 "against it, then update EXPECTED and EXPECTED_FOLDS.")
    lms_per_reading = {}
    for rd, lm, _s, _t in rows:
        lms_per_reading.setdefault(rd, set()).add(lm)
    folds = {rd: len(v) for rd, v in lms_per_reading.items() if len(v) > 1}
    if folds != EXPECTED_FOLDS:
        sys.exit(f"multi-LM readings changed: expected {EXPECTED_FOLDS}, got {folds}")
    missing = {rd for (_t, _n, _b, rd) in curr.MODULES} - set(lms_per_reading)
    if missing:
        sys.exit(f"readings with no LOS: {sorted(missing)}")
    return topics


def write_module(path, rows, records, topics):
    n_lm = len(records)
    lines = [
        '"""Official CFA Institute 2027 Level II Learning Outcome Statements.',
        "",
        "GENERATED FILE — do not hand-edit. Regenerate with:",
        "    python3 extract_los.py ~/Downloads/2027-cfa_l2_topic_outline.pdf",
        "",
        f"Source: CFA Institute, \"2027 Level II Topic Outlines\" ({len(topics)} topic areas,",
        f"{n_lm} learning modules, {len(rows)} LOS). Reference data only — the tick state lives",
        "in the `los` table (see db.py), the same split as curriculum.py vs modules.",
        "",
        "reading_no keys back to curriculum.READINGS, so the 51 official learning modules",
        "fold into our 42 readings: reading 1 (Multiple Regression) is four official LMs and",
        "reading 41 (Guidance for Standards I-VII) is seven, one per Standard. lm is kept per",
        "row so the app can group a reading's LOS under the official module they came from.",
        '"""',
        "",
        f'SOURCE = "CFA Institute — 2027 Level II Topic Outlines"',
        "",
        "# (reading_no, official learning-module name, seq within reading, LOS text)",
        "LOS = [",
    ]
    last_rd = None
    for rd, lm, seq, text in rows:
        if rd != last_rd:
            title = next(t for (_tp, t, _b, r) in
                         [(a, b, c, d) for (a, b, c, d) in curr.READINGS] if r == rd)
            lines.append(f"    # ---- R{rd}: {title}")
            last_rd = rd
        lines.append(f"    ({rd}, {lm!r}, {seq}, {text!r}),")
    lines += ["]", ""]
    with open(path, "w") as fh:
        fh.write("\n".join(lines))


def main():
    pdf = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1
                             else "~/Downloads/2027-cfa_l2_topic_outline.pdf")
    if not os.path.exists(pdf):
        sys.exit(f"no such PDF: {pdf}")
    records = parse(pdf_lines(pdf))
    rows = fold_to_readings(records)
    topics = verify(records, rows)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "los_2027.py")
    write_module(out, rows, records, topics)
    print(f"{len(topics)} topic areas · {len(records)} learning modules · {len(rows)} LOS")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
