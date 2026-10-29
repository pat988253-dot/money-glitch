# Money Glitch — project conventions

Personal side-income tracker. Single user, runs locally. The owner is not a software
engineer: explain decisions briefly in plain words and keep the stack simple.

## Stack (do not add to it without asking)
- Python 3.13, Streamlit (UI), SQLite via the standard-library `sqlite3` (storage),
  `requests` (exchange-rate API). No ORM, no frontend framework, no extra services.
- Dependencies are pinned in `requirements.txt` and installed into `.venv/`.

## Layout
- `app.py` — Home page (dashboard). Entry point: `streamlit run app.py`.
- `pages/N_Name.py` — one file per extra page; the number sets sidebar order.
- `db.py` — the ONLY module that touches SQLite. Pages call its functions; no SQL in pages.
- `rates.py` — the ONLY module that talks to the exchange-rate API (open.er-api.com, no key).
  Also holds conversion and money-formatting helpers (`convert`, `fmt_usd`, `fmt_cop`).
  A cached rate younger than 1 hour is reused instead of calling the API.
- `data/` — runtime files (`money_glitch.db`). Created automatically; never commit it.

## Data rules
- An entry stores its **original** amount and currency (`USD` or `COP`). Converted values
  are computed when displayed, never stored, so a rate change can't corrupt data.
- Conversion uses the current USD→COP rate: live API first, then the last good rate cached
  in SQLite (shown with its "as of" date). The UI always says which one is in use.
- Status is exactly `pending` or `paid`. Dates are stored as ISO text `YYYY-MM-DD`.
- "Earned this month" = `paid` entries dated in the current calendar month.
  "Pending" = all `pending` entries, any date.
- Money display: USD with 2 decimals (`$1,234.56`), COP with no decimals (`COP 1,234,567`).

## Code style
- Small, plain functions with short docstrings; readable over clever.
- Validate input in the form (amount > 0, source not blank) before calling `db.py`.
- Use parameterized SQL (`?` placeholders) — never build SQL with f-strings.
- Failures (no internet, API down) show a friendly message; the app must still open.

## Working agreement
- Build in small steps; after each step run the app and let the owner check it before
  moving on.
- Run: `.venv\Scripts\streamlit run app.py` → http://localhost:8501
