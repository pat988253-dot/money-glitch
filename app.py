"""Money Glitch — Home page (dashboard)."""

from datetime import date

import pandas as pd
import streamlit as st

import db
import rates

st.set_page_config(page_title="Money Glitch", page_icon="💸", layout="wide")

PAID_COLOR = "#2a78d6"     # blue
PENDING_COLOR = "#eb6834"  # orange

rate_info = rates.get_rate()
rate = rate_info["rate"]
st.sidebar.caption(rates.rate_label(rate_info))

st.title("💸 Money Glitch")
st.caption("Your side-income tracker")

entries = rates.with_conversions(db.list_entries(), rate)
if not entries:
    st.info("No income yet. Use **Add Entry** in the sidebar to record your first one.")
    st.stop()

df = pd.DataFrame(entries)
this_month = date.today().strftime("%Y-%m")
in_month = df["date"].str.startswith(this_month)
is_paid = df["status"] == "paid"


def original_subtotals(rows):
    """'500.00 USD + 120,000 COP' — used when there is no exchange rate."""
    sums = rows.groupby("currency")["amount"].sum()
    return " + ".join(f"{v:,.2f} {c}" if c == "USD" else f"{v:,.0f} {c}" for c, v in sums.items()) or "0"


# --- Headline numbers -------------------------------------------------------
col_earned, col_pending = st.columns(2)
for col, label, rows in (
    (col_earned, f"Earned this month ({date.today():%B})", df[is_paid & in_month]),
    (col_pending, "Pending (all dates)", df[~is_paid]),
):
    with col, st.container(border=True):
        if rate:
            st.metric(label, rates.fmt_usd(rows["usd"].sum()))
            st.caption(f"{rates.fmt_cop(rows['cop'].sum())} · {len(rows)} entr{'y' if len(rows) == 1 else 'ies'}")
        else:
            st.metric(label, original_subtotals(rows))
            st.caption("No exchange rate — shown in original currencies")

# --- Breakdown by source ----------------------------------------------------
st.subheader("Breakdown by source")
period = st.radio("Period", ["This month", "All time"], horizontal=True, label_visibility="collapsed")
scope = df[in_month] if period == "This month" else df

if scope.empty:
    st.caption("No entries in this period.")
    st.stop()

if not rate:
    st.warning("Can't combine USD and COP without an exchange rate — showing original currencies.")
    st.dataframe(
        [
            {
                "Source": source,
                "Status": status.capitalize(),
                "Amount": f"{amount:,.2f} USD" if currency == "USD" else f"{amount:,.0f} COP",
            }
            for (source, currency, status), amount in scope.groupby(["source", "currency", "status"])["amount"].sum().items()
        ],
        hide_index=True,
        width="stretch",
    )
    st.stop()

by_source = (
    scope.pivot_table(index="source", columns="status", values="usd", aggfunc="sum", fill_value=0)
    .reindex(columns=["paid", "pending"], fill_value=0)
    .rename(columns={"paid": "Paid", "pending": "Pending"})
)
by_source["Total"] = by_source["Paid"] + by_source["Pending"]
by_source = by_source.sort_values("Total", ascending=False).reset_index().rename(columns={"source": "Source"})

st.bar_chart(
    by_source,
    x="Source",
    y=["Paid", "Pending"],
    color=[PAID_COLOR, PENDING_COLOR],
    horizontal=True,
    stack=True,
    x_label="USD",
    y_label="",
    height=max(160, 60 * len(by_source)),
)

st.dataframe(
    [
        {
            "Source": r["Source"],
            "Paid (USD)": rates.fmt_usd(r["Paid"]),
            "Pending (USD)": rates.fmt_usd(r["Pending"]),
            "Total (USD)": rates.fmt_usd(r["Total"]),
            "Total (COP)": rates.fmt_cop(r["Total"] * rate),
        }
        for _, r in by_source.iterrows()
    ],
    hide_index=True,
    width="stretch",
)
