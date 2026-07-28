# Deploying the tracker (so it syncs work ↔ home)

Chosen stack: **Streamlit Community Cloud** (free hosting) + **Neon** (free serverless
Postgres). Neon auto-wakes on connection, so an app used in study bursts never needs
manual un-pausing. Local dev keeps using the SQLite `cfa.db` with zero setup; only the
deployed app needs Postgres.

These steps need **your** accounts — they can't be automated (account creation / login).
Everything in the repo is already prepped for them.

## 1. Neon — get a Postgres URL (5 min)
1. Sign up at neon.tech (free tier).
2. Create a project (any name, e.g. `cfa-l2`). Region: closest to you.
3. Copy the **connection string** (looks like `postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require`).

## 2. GitHub — push this repo (private)
`gh` needs a one-time login first (this is the "please run: gh auth login" message):
```bash
gh auth login          # choose GitHub.com → HTTPS → log in via browser
cd ~/Documents/cfa-l2-tracker
gh repo create cfa-l2-tracker --private --source=. --push
```
No `gh`? Make an empty **private** repo at github.com/new, then:
```bash
cd ~/Documents/cfa-l2-tracker
git remote add origin https://github.com/<your-username>/cfa-l2-tracker.git
git branch -M main && git push -u origin main
```
The auto-set commit author ("Opt Admin …") is harmless; to use your name instead (optional):
`git config --global user.name "Justin Maccabe" && git config --global user.email "justin.maccabe@ofg.com"`.
Copyrighted PDFs never land here — `.gitignore` excludes `*.pdf` / `*.xlsx`; the files live in the DB.

## 3. Streamlit Community Cloud — deploy
1. Go to share.streamlit.io → **New app** → pick your `cfa-l2-tracker` repo, `app.py`.
2. **Advanced settings → Secrets**, paste:
   ```toml
   DATABASE_URL = "postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require"
   ```
3. Deploy. First boot creates the tables and seeds the 45 sections + 171 sub-modules.

## 4. One-time: load your files + set your password into the CLOUD db
The Postgres starts empty of your PDFs/notes. Push them up once from your machine,
pointed at Neon:
```bash
cd ~/Documents/cfa-l2-tracker
export DATABASE_URL="postgresql://...(your Neon string)..."
.venv/bin/python -c "
import db, glob, os, datetime as dt
db.init_db()
now = dt.datetime.now().isoformat(timespec='minutes')
for f in glob.glob(os.path.expanduser('~/Desktop/CFA/**/*'), recursive=True):
    if f.lower().endswith(('.pdf','.xlsx','.png','.jpg','.jpeg')):
        db.upsert_resource(os.path.basename(f), open(f,'rb').read(), now)
print('loaded', len(db.list_resources()), 'files to Neon')
"
```
Then open the deployed app, go to **Resources** or **Notes**, and set your password
(it hashes into the DB and works on every device from then on).

## After go-live
Open the same URL on your work computer and your laptop — same data, same password,
same notes. That's the handoff.
