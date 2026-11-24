from pathlib import Path
import sys
import csv
import io
import json

import httpx
import streamlit as st

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from streamlit_app.api_config import sidebar_api_url
except ImportError:
    from api_config import sidebar_api_url

st.set_page_config(
    page_title="Account Settings | Harvesta",
    page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"),
    layout="wide",
)

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

API_URL = sidebar_api_url()
if not st.session_state.get("token"):
    st.warning("Please sign in first.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
st.title("Account Settings")
user = st.session_state.get("user") or {}
st.write(f"Signed in as **{user.get('full_name', 'Harvesta user')}**")

st.subheader("Notification preferences")
notification_options = {
    "Email": "email",
    "SMS": "sms",
    "Email and SMS": "both",
}
current_preference = user.get("notification_preference", "email")
preference_label = next(
    (label for label, value in notification_options.items() if value == current_preference),
    "Email",
)
selected_preference = st.selectbox(
    "Preferred notification channel",
    list(notification_options),
    index=list(notification_options).index(preference_label),
    key=f"notification_preference_setting_{user.get('id')}",
)
if st.button("Save notification preference"):
    try:
        preference_response = httpx.patch(
            f"{API_URL}/auth/me",
            json={"notification_preference": notification_options[selected_preference]},
            headers=headers,
            timeout=10,
        )
        if preference_response.status_code == 200:
            st.session_state.user = preference_response.json()
            st.success("Notification preference saved.")
            st.rerun()
        st.error(preference_response.json().get("detail", "Could not save preference."))
    except httpx.HTTPError as exc:
        st.error(f"Could not save preference: {exc}")

st.divider()
st.subheader("Harvesta Wallet")
try:
    wallet_response = httpx.get(f"{API_URL}/wallet/", headers=headers, timeout=10)
except httpx.HTTPError as exc:
    wallet_response = None
    st.error(f"Could not load wallet: {exc}")

if wallet_response is not None and wallet_response.status_code == 200:
    wallet_data = wallet_response.json()
    st.metric("Available balance", f"UGX {wallet_data['balance_ugx']:,.0f}")
    transactions = wallet_data.get("transactions", [])
    if transactions:
        st.dataframe(
            [
                {
                    "Date": item["created_at"][:19].replace("T", " "),
                    "Type": item["transaction_type"].replace("_", " ").title(),
                    "Amount (UGX)": item["amount_ugx"],
                    "Status": item["status"].title(),
                    "Method": item.get("payment_method") or "—",
                    "Reference": item.get("reference") or "—",
                }
                for item in transactions
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.caption("Wallet transactions will appear here.")
elif wallet_response is not None:
    st.error(wallet_response.json().get("detail", "Could not load wallet."))

deposit_col, withdrawal_col = st.columns(2)
with deposit_col:
    st.markdown("#### Deposit funds")
    deposit_amount = st.number_input(
        "Deposit amount (UGX)", min_value=1000, step=1000, key="wallet_deposit_amount"
    )
    deposit_method = st.selectbox(
        "Deposit method",
        ["MTN / Airtel Mobile Money", "Visa / Mastercard", "PayPal"],
        key="wallet_deposit_method",
    )
    deposit_reference = st.text_input(
        "Transaction reference (optional)", key="wallet_deposit_reference"
    )
    try:
        deposit_quote_response = httpx.post(
            f"{API_URL}/wallet/quote",
            json={"operation": "deposit", "amount_ugx": int(deposit_amount)},
            headers=headers,
            timeout=10,
        )
        if deposit_quote_response.status_code == 200:
            deposit_quote = deposit_quote_response.json()
            st.caption("Deposit fee and tax estimate (UGX)")
            st.dataframe(
                [
                    {"Item": "Base amount", "UGX": deposit_quote["base_amount_ugx"]},
                    {"Item": "Service fee", "UGX": deposit_quote["service_fee_ugx"]},
                    {"Item": "Estimated transaction levy", "UGX": deposit_quote["withdrawal_levy_ugx"]},
                    {"Item": "Estimated VAT", "UGX": deposit_quote["vat_ugx"]},
                    {"Item": "Total estimated taxes", "UGX": deposit_quote["total_tax_ugx"]},
                    {"Item": "Total payable", "UGX": deposit_quote["total_payable_ugx"]},
                    {"Item": "Net wallet credit", "UGX": deposit_quote["net_amount_ugx"]},
                ],
                hide_index=True,
                use_container_width=True,
            )
            st.caption(deposit_quote["tax_note"])
        else:
            deposit_quote = None
            st.error(deposit_quote_response.json().get("detail", "Could not quote deposit."))
    except httpx.HTTPError as exc:
        deposit_quote = None
        st.error(f"Could not quote deposit: {exc}")
    if st.button("Request deposit", key="wallet_deposit_submit"):
        if deposit_quote is None:
            st.error("Review the deposit quote before continuing.")
        else:
            method = {
                "MTN / Airtel Mobile Money": "mobile_money",
                "Visa / Mastercard": "card",
                "PayPal": "paypal",
            }[deposit_method]
            try:
                deposit_response = httpx.post(
                    f"{API_URL}/wallet/deposits",
                    json={
                        "amount_ugx": int(deposit_amount),
                        "payment_method": method,
                        "reference": deposit_reference or None,
                    },
                    headers=headers,
                    timeout=10,
                )
                if deposit_response.status_code == 201:
                    st.success("Deposit request recorded. Funds remain pending manual verification.")
                    st.rerun()
                st.error(deposit_response.json().get("detail", "Could not request deposit."))
            except httpx.HTTPError as exc:
                st.error(f"Could not request deposit: {exc}")

with withdrawal_col:
    st.markdown("#### Withdraw funds")
    withdrawal_amount = st.number_input(
        "Withdrawal amount (UGX)",
        min_value=1000,
        step=1000,
        key="wallet_withdrawal_amount",
    )
    withdrawal_destination = st.text_input(
        "Mobile Money destination", placeholder="+256 7XX XXX XXX",
        key="wallet_withdrawal_destination",
    )
    try:
        withdrawal_quote_response = httpx.post(
            f"{API_URL}/wallet/quote",
            json={"operation": "withdrawal", "amount_ugx": int(withdrawal_amount)},
            headers=headers,
            timeout=10,
        )
        if withdrawal_quote_response.status_code == 200:
            withdrawal_quote = withdrawal_quote_response.json()
            st.caption("Withdrawal fee and tax estimate (UGX)")
            st.dataframe(
                [
                    {"Item": "Base payout", "UGX": withdrawal_quote["base_amount_ugx"]},
                    {"Item": "Service fee", "UGX": withdrawal_quote["service_fee_ugx"]},
                    {"Item": "Estimated withdrawal levy", "UGX": withdrawal_quote["withdrawal_levy_ugx"]},
                    {"Item": "Estimated VAT", "UGX": withdrawal_quote["vat_ugx"]},
                    {"Item": "Total estimated taxes", "UGX": withdrawal_quote["total_tax_ugx"]},
                    {"Item": "Total wallet amount reserved", "UGX": withdrawal_quote["total_payable_ugx"]},
                    {"Item": "Net payout", "UGX": withdrawal_quote["net_amount_ugx"]},
                ],
                hide_index=True,
                use_container_width=True,
            )
            st.caption(withdrawal_quote["tax_note"])
        else:
            withdrawal_quote = None
            st.error(withdrawal_quote_response.json().get("detail", "Could not quote withdrawal."))
    except httpx.HTTPError as exc:
        withdrawal_quote = None
        st.error(f"Could not quote withdrawal: {exc}")
    if st.button("Request withdrawal", key="wallet_withdrawal_submit"):
        if withdrawal_quote is None:
            st.error("Review the withdrawal quote before continuing.")
        elif not withdrawal_destination.strip():
            st.error("Enter a Mobile Money destination.")
        else:
            try:
                withdrawal_response = httpx.post(
                    f"{API_URL}/wallet/withdrawals",
                    json={
                        "amount_ugx": int(withdrawal_amount),
                        "destination": withdrawal_destination.strip(),
                    },
                    headers=headers,
                    timeout=10,
                )
                if withdrawal_response.status_code == 201:
                    st.success("Withdrawal request recorded and reserved for manual processing.")
                    st.rerun()
                st.error(withdrawal_response.json().get("detail", "Could not request withdrawal."))
            except httpx.HTTPError as exc:
                st.error(f"Could not request withdrawal: {exc}")

if user.get("role") == "admin":
    st.markdown("#### Pending wallet requests")
    try:
        pending_response = httpx.get(
            f"{API_URL}/wallet/admin/pending", headers=headers, timeout=10
        )
        if pending_response.status_code == 200:
            for transaction in pending_response.json():
                with st.expander(
                    f"Request #{transaction['id']} · "
                    f"{transaction['transaction_type'].title()} · "
                    f"UGX {transaction['amount_ugx']:,}"
                ):
                    st.write(
                        f"User #{transaction.get('user_id')} · "
                        f"{transaction.get('payment_method') or 'Manual payout'}"
                    )
                    resolution_reference = st.text_input(
                        "Verified provider reference (optional)",
                        key=f"wallet_resolution_ref_{transaction['id']}",
                    )
                    approve_col, reject_col = st.columns(2)
                    for column, decision in (
                        (approve_col, "completed"),
                        (reject_col, "rejected"),
                    ):
                        with column:
                            if st.button(
                                decision.title(),
                                key=f"wallet_resolution_{transaction['id']}_{decision}",
                            ):
                                try:
                                    result = httpx.patch(
                                        f"{API_URL}/wallet/admin/transactions/{transaction['id']}",
                                        json={
                                            "status": decision,
                                            "reference": resolution_reference or None,
                                        },
                                        headers=headers,
                                        timeout=10,
                                    )
                                    if result.status_code == 200:
                                        st.success(f"Request {decision}.")
                                        st.rerun()
                                    st.error(result.json().get("detail", "Could not resolve request."))
                                except httpx.HTTPError as exc:
                                    st.error(f"Could not resolve wallet request: {exc}")
        else:
            st.error(pending_response.json().get("detail", "Could not load pending requests."))
    except httpx.HTTPError as exc:
        st.error(f"Could not load pending wallet requests: {exc}")

st.divider()
st.subheader("App rating")
try:
    rating_status_response = httpx.get(
        f"{API_URL}/reviews/prompt", headers=headers, timeout=10
    )
    rating_status = rating_status_response.json() if rating_status_response.status_code == 200 else {}
except httpx.HTTPError as exc:
    rating_status = {}
    st.error(f"Could not load rating status: {exc}")
preview_rating = st.checkbox(
    "Preview 1-Week Rating Prompt",
    key=f"preview_one_week_rating_{user.get('id')}",
)
if rating_status.get("submitted"):
    st.success("Thank you — your Harvesta rating has been submitted.")
elif rating_status.get("eligible") or preview_rating:
    st.markdown("#### How is Harvesta working for you?")
    rating = st.select_slider(
        "Rate Harvesta",
        options=[1, 2, 3, 4, 5],
        value=5,
        key=f"settings_review_rating_{user.get('id')}",
    )
    review_comments = st.text_area(
        "Optional comments",
        key=f"app_review_comments_{user.get('id')}",
    )
    if st.button("Submit rating", key=f"settings_submit_review_{user.get('id')}"):
        try:
            review_response = httpx.post(
                f"{API_URL}/reviews/",
                json={"rating": rating, "comments": review_comments or None},
                headers=headers,
                timeout=10,
            )
            if review_response.status_code == 201:
                st.success("Thank you for sharing your feedback.")
                st.rerun()
            st.error(review_response.json().get("detail", "Could not submit rating."))
        except httpx.HTTPError as exc:
            st.error(f"Could not submit rating: {exc}")
else:
    st.caption(
        f"Your account is {rating_status.get('account_age_days', 0)} days old. "
        "The rating prompt becomes available after one week."
    )

st.subheader("Privacy and data")

try:
    response = httpx.get(f"{API_URL}/auth/me/export", headers=headers, timeout=15)
except Exception as exc:
    response = None
    st.error(f"Could not prepare export: {exc}")

if response is not None and response.status_code == 200:
    data = response.json()
    json_data = json.dumps(data, indent=2, default=str)
    st.download_button(
        "Export My Data (JSON)",
        data=json_data,
        file_name="harvesta-my-data.json",
        mime="application/json",
        use_container_width=True,
    )

    flat_rows = []
    account = data.get("account", {})
    flat_rows.append({"section": "account", **account})
    for section in ("farms", "products", "crop_plots", "livestock", "farm_finance"):
        for item in data.get(section, []):
            flat_rows.append({"section": section, **item})
    buffer = io.StringIO()
    fieldnames = sorted({key for row in flat_rows for key in row})
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(flat_rows)
    st.download_button(
        "Export My Data (CSV)",
        data=buffer.getvalue(),
        file_name="harvesta-my-data.csv",
        mime="text/csv",
        use_container_width=True,
    )
elif response is not None:
    st.error(response.json().get("detail", "Could not export account data"))

st.divider()
st.subheader("Delete My Account")
st.warning("This permanently deletes the account and associated Harvesta records.")
confirm = st.checkbox("I understand that this action cannot be undone.")
if st.button("Delete My Account", type="secondary", use_container_width=True):
    if not confirm:
        st.error("Confirm account deletion first.")
    else:
        deleted = httpx.delete(f"{API_URL}/auth/me", headers=headers, timeout=15)
        if deleted.status_code == 200:
            st.session_state.token = None
            st.session_state.user = None
            st.success("Your account and associated records were deleted.")
            st.switch_page("Home.py")
        else:
            st.error(deleted.json().get("detail", "Could not delete account"))

st.markdown("---")
st.caption("\u00a9 2026 Harvesta. All rights reserved.")
