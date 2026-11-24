from pathlib import Path
import sys
from datetime import date
import httpx
import pandas as pd
import streamlit as st

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from streamlit_app.api_config import get_api_url, normalize_api_url
except ImportError:
    from api_config import get_api_url, normalize_api_url

st.set_page_config(
    page_title="Farm Finance | Harvesta",
    page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"),
    layout="wide",
)

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

DEFAULT_API_URL = get_api_url()
API_URL = normalize_api_url(st.session_state.get("api_url") or DEFAULT_API_URL)
if not st.session_state.get("authenticated") or not st.session_state.get("token"):
    st.warning("Please sign in with a farmer account.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
st.title("Farmer Financial Growth Board")
st.caption("Real-time farm income and expense records in UGX")

try:
    summary_response = httpx.get(f"{API_URL}/farm-finance/summary", headers=headers, timeout=10)
    summary = summary_response.json() if summary_response.status_code == 200 else {}
except Exception as exc:
    summary = {}
    st.error(f"Could not load finance summary: {exc}")

revenue = float(summary.get("total_revenue", 0))
cost = float(summary.get("total_cost", 0))
profit = float(summary.get("gross_profit", 0))
margin = float(summary.get("gross_margin", 0))

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue (UGX)", f"{revenue:,.0f}")
k2.metric("Total Cost (UGX)", f"{cost:,.0f}")
k3.metric("Gross Profit (UGX)", f"{profit:,.0f}")
k4.metric("Gross Margin (%)", f"{margin:.2f}%")

monthly = summary.get("monthly", [])
if monthly:
    chart_data = pd.DataFrame(monthly).set_index("month")
    st.subheader("Revenue vs Cost")
    st.bar_chart(chart_data[["revenue", "cost"]])

budget = summary.get("budget_breakdown", [])
if budget:
    st.subheader("Budget Breakdown")
    budget_data = pd.DataFrame(budget).set_index("category")
    st.bar_chart(budget_data["amount"])

st.divider()
st.subheader("Log a financial transaction")
with st.form("farm_transaction_form"):
    transaction_type = st.selectbox("Transaction type", ["Income", "Expense"])
    category = st.selectbox(
        "Category",
        ["Produce sales", "Seeds", "Fertilizer", "Labor", "Vet care",
         "Animal feed", "Equipment", "Transport", "Water", "Other"],
    )
    amount = st.number_input("Amount (UGX)", min_value=1.0, value=50000.0, step=1000.0)
    transaction_date = st.date_input("Date", value=date.today())
    description = st.text_area("Description")
    submitted = st.form_submit_button("Save Transaction", use_container_width=True)
    if submitted:
        response = httpx.post(
            f"{API_URL}/farm-finance/transactions",
            headers=headers,
            json={
                "transaction_type": "income" if transaction_type == "Income" else "expense",
                "category": category,
                "amount": amount,
                "transaction_date": str(transaction_date),
                "description": description or None,
            },
            timeout=10,
        )
        if response.status_code == 201:
            st.success("Financial transaction saved.")
            st.rerun()
        else:
            st.error(response.json().get("detail", "Could not save transaction"))

try:
    transactions_response = httpx.get(f"{API_URL}/farm-finance/transactions", headers=headers, timeout=10)
    transactions = transactions_response.json() if transactions_response.status_code == 200 else []
except Exception:
    transactions = []

if transactions:
    st.subheader("Recent transactions")
    for transaction in transactions:
        c1, c2 = st.columns([5, 1])
        with c1:
            label = "Income" if transaction["transaction_type"] == "income" else "Expense"
            st.write(
                f"**{label}: UGX {transaction['amount']:,.0f}** - "
                f"{transaction['category']} - {transaction['transaction_date']}"
            )
        with c2:
            if st.button("Delete", key=f"delete_finance_{transaction['id']}"):
                deleted = httpx.delete(
                    f"{API_URL}/farm-finance/transactions/{transaction['id']}",
                    headers=headers,
                    timeout=10,
                )
                if deleted.status_code == 204:
                    st.rerun()
                else:
                    st.error("Could not delete transaction")

st.markdown("---")
st.caption("\u00a9 2026 Harvesta. All rights reserved.")
