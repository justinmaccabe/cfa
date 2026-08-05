"""One-shot: push local study materials into whatever DATABASE_URL is set (e.g. your
Neon cloud DB), so the deployed app can serve them.

    export DATABASE_URL="postgresql://...neon..."
    python load_to_cloud.py
"""
import datetime as dt
import glob
import os

import db

PRETTY = {"CFA_L2_Study_Planner_2.xlsx": "CFA L2 Study Planner.xlsx",
          "aug 2025.png": "CFA Level I - Result (Aug 2025).png",
          "may 2026.png": "CFA Level I - Result (May 2026, Pass).png"}
EXTS = (".pdf", ".xlsx", ".png", ".jpg", ".jpeg")
SRC = os.environ.get("CFA_RESOURCES_DIR", os.path.expanduser("~/Desktop/CFA"))


def main():
    if not os.environ.get("DATABASE_URL"):
        raise SystemExit("Set DATABASE_URL first (your Neon connection string).")
    db.init_db()
    now = dt.datetime.now().isoformat(timespec="minutes")
    n = 0
    for f in glob.glob(os.path.join(SRC, "**", "*"), recursive=True):
        if f.lower().endswith(EXTS):
            base = os.path.basename(f)
            with open(f, "rb") as fh:
                db.upsert_resource(PRETTY.get(base, base), fh.read(), now)
            n += 1
    print(f"uploaded {n} files; resources now: {len(db.list_resources())}")


if __name__ == "__main__":
    main()
