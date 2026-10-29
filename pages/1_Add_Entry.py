"""Add Entry page — form to record a new income entry."""

from datetime import date

import streamlit as st

import db
import rates

st.set_page_config(page_title="Add Entry · Money Glitch", page_icon="💸", layout="wide")

st.title("➕ Add income")

# Show the confirmation from the previous submit (the form clears itself on submit).
if "added_msg" in st.session_state:
    st.success(st.session_state.pop("added_msg"))

with st.form("add_entry", clear_on_submit=True):
    source = st.selectbox(
        "Source",
        options=db.list_sources(),
        index=None,
        placeholder="Pick one or type a new source (e.g. Upwork, Tutoring)",
        accept_new_options=True,
    )

    col_amount, col_currency = st.columns([3, 1])
    amount = col_amount.number_input("Amount", min_value=0.0, step=1.0, format="%.2f")
    currency = col_currency.selectbox("Currency", db.CURRENCIES)

    col_date, col_status = st.columns(2)
    entry_date = col_date.date_input("Date", value=date.today(), format="YYYY-MM-DD")
    status = col_status.radio("Status", db.STATUSES, horizontal=True, format_func=str.capitalize)

    notes = st.text_area("Notes (optional)", placeholder="Invoice #, client, anything useful")

    submitted = st.form_submit_button("Save entry", type="primary")

if submitted:
    errors = []
    if not source or not source.strip():
        errors.append("Please enter a source.")
    if amount <= 0:
        errors.append("Amount must be greater than 0.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        db.add_entry(source, amount, currency, entry_date, status, notes)
        st.session_state["added_msg"] = f"Saved: {source.strip()} — {amount:,.2f} {currency} ({status})"
        st.rerun()

st.divider()
st.subheader("Latest entries")
rate_info = rates.get_rate()
st.sidebar.caption(rates.rate_label(rate_info))

recent = rates.with_conversions(db.list_entries()[:5], rate_info["rate"])
if recent:
    st.dataframe(
        [
            {
                "Date": e["date"],
                "Source": e["source"],
                "Original": f"{e['amount']:,.2f} {e['currency']}",
                "USD": rates.fmt_usd(e["usd"]),
                "COP": rates.fmt_cop(e["cop"]),
                "Status": e["status"].capitalize(),
                "Notes": e["notes"],
            }
            for e in recent
        ],
        hide_index=True,
        width="stretch",
    )
else:
    st.caption("No entries yet — add your first one above.")
