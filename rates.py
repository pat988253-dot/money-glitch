"""USD⇄COP exchange rate (live API with cached fallback) and money helpers.

Order of preference when asking for the rate:
  1. Cached rate fetched less than an hour ago (avoids calling the API on every click).
  2. Live rate from the API — saved to the cache on success.
  3. Older cached rate, if the API can't be reached.
  4. Nothing — callers show amounts in their original currency only.
"""

from datetime import datetime, timedelta, timezone

import requests

import db

API_URL = "https://open.er-api.com/v6/latest/USD"  # free, no API key; provider updates daily
PAIR = "USD_COP"
FRESH_FOR = timedelta(hours=1)
TIMEOUT_SECONDS = 5


def _now():
    return datetime.now(timezone.utc)


def fetch_live_rate():
    """Ask the API for 1 USD in COP. Returns a float, or None on any failure."""
    try:
        resp = requests.get(API_URL, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        rate = float(data["rates"]["COP"])
        return rate if rate > 0 else None
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None


def get_rate():
    """Current USD→COP rate as a dict: {rate, fetched_at, source}.

    source is "live", "cached" or "unavailable" (then rate and fetched_at are None).
    """
    cached = db.load_rate(PAIR)
    if cached:
        cached_at = datetime.fromisoformat(cached["fetched_at"])
        if _now() - cached_at < FRESH_FOR:
            return {"rate": cached["rate"], "fetched_at": cached_at, "source": "live"}

    rate = fetch_live_rate()
    if rate is not None:
        now = _now()
        db.save_rate(PAIR, rate, now.isoformat())
        return {"rate": rate, "fetched_at": now, "source": "live"}

    if cached:
        return {"rate": cached["rate"], "fetched_at": datetime.fromisoformat(cached["fetched_at"]),
                "source": "cached"}

    return {"rate": None, "fetched_at": None, "source": "unavailable"}


def convert(amount, currency, rate):
    """Return (usd, cop) for an amount. If rate is None, the other currency is None."""
    if currency == "USD":
        return amount, (amount * rate if rate else None)
    return (amount / rate if rate else None), amount


def fmt_usd(value):
    return "—" if value is None else f"${value:,.2f}"


def fmt_cop(value):
    return "—" if value is None else f"COP {value:,.0f}"


def rate_label(info):
    """One-line description of the rate in use, for the sidebar."""
    if info["source"] == "unavailable":
        return "⚠️ No exchange rate available (offline and nothing cached). Showing original currency only."
    when = info["fetched_at"].astimezone().strftime("%Y-%m-%d %H:%M")
    line = f"1 USD = {info['rate']:,.2f} COP"
    if info["source"] == "live":
        return f"🟢 {line} · live, checked {when}"
    return f"🟡 {line} · offline — using saved rate from {when}"


def with_conversions(entries, rate):
    """Copy of entries with 'usd' and 'cop' fields added."""
    out = []
    for e in entries:
        usd, cop = convert(e["amount"], e["currency"], rate)
        out.append({**e, "usd": usd, "cop": cop})
    return out
