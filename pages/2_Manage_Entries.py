"""Manage Entries page — pick an entry from the table, then edit or delete it."""

from datetime import date

import streamlit as st

import db
import rates

st.set_page_config(page_title="Manage Entries · Money Glitch", page_icon="💸", layout="wide")

rate_info = rates.get_rate()
st.sidebar.caption(rates.rate_label(rate_info))

st.title("✏️ Manage entries")

if "manage_msg" in st.session_state:
    st.success(st.session_state.pop("manage_msg"))

entries = rates.with_conversions(db.list_entries(), rate_info["rate"])
if not entries:
    st.info("No entries yet. Use **Add Entry** in the sidebar.")
    st.stop()

status_filter = st.radio("Show", ["All", "Pending", "Paid"], horizontal=True)
if status_filter != "All":
    entries = [e for e in entries if e["status"] == status_filter.lower()]
if not entries:
    st.caption(f"No {status_filter.lower()} entries.")
    st.stop()

st.caption("Click a row to edit or delete it.")
# Changing the key after a save/delete clears the selected row.
table = st.dataframe(
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
        for e in entries
    ],
    hide_index=True,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    key=f"table_{st.session_state.get('table_version', 0)}_{status_filter}",
)


def done(message):
    """Show a message after the rerun and clear the row selection."""
    st.session_state["manage_msg"] = message
    st.session_state["table_version"] = st.session_state.get("table_version", 0) + 1
    st.rerun()


selected = table.selection.rows
if not selected:
    st.stop()

entry = entries[selected[0]]
st.divider()
st.subheader(f"Edit: {entry['source']} — {entry['amount']:,.2f} {entry['currency']} on {entry['date']}")

k = f"edit_{entry['id']}"  # per-entry keys so the form refills when you pick another row
with st.form(k):
    sources = db.list_sources()
    source = st.selectbox(
        "Source", sources, index=sources.index(entry["source"]), accept_new_options=True, key=f"{k}_source"
    )
    col_amount, col_currency = st.columns([3, 1])
    amount = col_amount.number_input(
        "Amount", min_value=0.0, step=1.0, format="%.2f", value=float(entry["amount"]), key=f"{k}_amount"
    )
    currency = col_currency.selectbox(
        "Currency", db.CURRENCIES, index=db.CURRENCIES.index(entry["currency"]), key=f"{k}_currency"
    )
    col_date, col_status = st.columns(2)
    entry_date = col_date.date_input(
        "Date", value=date.fromisoformat(entry["date"]), format="YYYY-MM-DD", key=f"{k}_date"
    )
    status = col_status.radio(
        "Status", db.STATUSES, index=db.STATUSES.index(entry["status"]), horizontal=True,
        format_func=str.capitalize, key=f"{k}_status",
    )
    notes = st.text_area("Notes (optional)", value=entry["notes"], key=f"{k}_notes")
    saved = st.form_submit_button("Save changes", type="primary")

if saved:
    errors = []
    if not source or not source.strip():
        errors.append("Please enter a source.")
    if amount <= 0:
        errors.append("Amount must be greater than 0.")
    for e in errors:
        st.error(e)
    if not errors:
        db.update_entry(entry["id"], source, amount, currency, entry_date, status, notes)
        done(f"Updated: {source.strip()} — {amount:,.2f} {currency} ({status})")

with st.popover("🗑️ Delete this entry"):
    st.write("This can't be undone.")
    if st.button("Yes, delete permanently", type="primary", key=f"{k}_delete"):
        db.delete_entry(entry["id"])
        done(f"Deleted: {entry['source']} — {entry['amount']:,.2f} {entry['currency']} on {entry['date']}")
