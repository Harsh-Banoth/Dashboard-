# Setup Checklist (Mac)

A linear, copy-paste checklist to get this running with zero guesswork.
Follow in order — each step assumes the previous one succeeded.

---

## ☐ 1. Install Homebrew (skip if already installed)
```bash
curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash
```

## ☐ 2. Install Python and PostgreSQL
```bash
brew install python
brew install postgresql@16
brew services start postgresql@16
createdb stockdata
```

Verify Postgres is running:
```bash
psql -d stockdata -c "SELECT version();"
```
You should see a version string printed. If this fails, Postgres isn't
running — try `brew services restart postgresql@16`.

## ☐ 3. Open the project in VS Code
- Unzip the project folder
- VS Code → File → Open Folder → select the unzipped folder
- Open a terminal inside VS Code: **Terminal → New Terminal**

## ☐ 4. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```
Your terminal prompt should now start with `(venv)`. **Every command below
assumes this is active** — if you close and reopen the terminal, run
`source venv/bin/activate` again first.

## ☐ 5. Point VS Code's interpreter at the venv (important!)
This step is what most commonly goes wrong — VS Code's "Run" button and
debugger use whatever interpreter is *selected*, not necessarily the one
active in your terminal.

1. `Cmd+Shift+P` → type **"Python: Select Interpreter"**
2. Choose the one that shows `./venv/bin/python` (often labeled
   `('venv': venv)`)
3. If it's not listed, choose **"Enter interpreter path" → "Find..."** and
   navigate to `venv/bin/python` inside your project folder

**Sanity check** — run this in the VS Code terminal to confirm everything
lines up:
```bash
which python
```
This should print a path that contains `venv/bin/python`. If it instead
shows `/usr/bin/python3`, re-run `source venv/bin/activate`.

## ☐ 6. Install dependencies
```bash
pip install -r requirements.txt
```

Confirm pandas installed correctly:
```bash
python -c "import pandas; print(pandas.__version__)"
```
This should print a version number, not an error.

## ☐ 7. Fetch and clean the data
```bash
python scripts/fetch_data.py
python scripts/clean_data.py
```
`fetch_data.py` takes a few minutes (downloading ~25 stocks + 7 indices,
with a polite delay between requests). You'll see `[ok]` lines as each
file downloads. If a few show `[fail]`, just re-run the script — it skips
files already downloaded and retries the missing ones.

## ☐ 8. Load data into Postgres
```bash
psql -d stockdata -f sql/schema.sql
psql -d stockdata -f sql/load_data.sql
```

Confirm the load worked:
```bash
psql -d stockdata -c "SELECT COUNT(*) FROM daily_prices;"
```
Should return a row count in the thousands.

## ☐ 9. Set up your .env file
```bash
cp .env.example .env
```
Open `.env` in VS Code and set `DB_USER` to your Mac username (run
`whoami` in the terminal if you're not sure). Leave `DB_PASSWORD` blank
unless you set one when installing Postgres.

## ☐ 10. Run the dashboard
```bash
streamlit run dashboard/app.py
```
This should open your browser automatically to `localhost:8501`. If it
doesn't, copy the URL Streamlit prints in the terminal into your browser
manually.

---

## Common errors and fixes

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'pandas'` (or any package) | Your VS Code interpreter isn't pointed at the venv — redo Step 5, or run the script via terminal (`python scripts/...py`) instead of the ▶ Run button |
| `psql: command not found` | Postgres isn't installed or not in your PATH — redo Step 2, then restart your terminal |
| `could not connect to server` | Postgres isn't running — `brew services start postgresql@16` |
| Streamlit shows "Could not connect to the database" | Check your `.env` values match Step 9; confirm Step 8 completed without errors |
| `fetch_data.py` shows many `[fail]` lines | NSE may be rate-limiting — wait a few minutes and re-run; the script skips already-downloaded files |
