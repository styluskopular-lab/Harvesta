from pathlib import Path
import sys
import httpx
import streamlit as st

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from streamlit_app.api_config import sidebar_api_url
except ImportError:
    from api_config import sidebar_api_url

st.set_page_config(
    page_title="Dashboard | Harvesta",
    page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"),
    layout="wide",
)

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

if st.session_state.get("dark_mode", False):
    st.markdown(
        '<style>.stApp{background:#102319!important;color:#edf5ee!important}'
        '.stApp h1,.stApp h2,.stApp h3,.stApp p{color:#edf5ee!important}'
        '[data-testid="stSidebar"]{background:#13291b!important}</style>',
        unsafe_allow_html=True,
    )

user = st.session_state.get("user")
if not st.session_state.get("authenticated") or not user:
    st.warning("Please sign in or create an account first.")
    if st.button("Go to sign in"):
        st.switch_page("Home.py")
    st.stop()
if not st.session_state.get("rules_accepted", False):
    st.error("General Rules, Uganda PDPO Privacy Policy & UNFFE/NARO/MAAIF/MTIC Guidelines acceptance is required.")
    if st.button("Review and accept rules"):
        st.switch_page("pages/8_Privacy.py")
    st.stop()

st.title("Dashboard")
st.success(f"Welcome, {user['full_name']}")

API_URL = sidebar_api_url()
headers = {"Authorization": f"Bearer {st.session_state.token}"}

try:
    farms = httpx.get(f"{API_URL}/farms/me", headers=headers, timeout=10)
    plots = httpx.get(f"{API_URL}/farm-records/crop-plots", headers=headers, timeout=10)
    livestock = httpx.get(f"{API_URL}/farm-records/livestock", headers=headers, timeout=10)
    orders = httpx.get(f"{API_URL}/orders/", headers=headers, timeout=10)
    farm_count = len(farms.json()) if farms.status_code == 200 else 0
    plot_count = len(plots.json()) if plots.status_code == 200 else 0
    livestock_count = len(livestock.json()) if livestock.status_code == 200 else 0
    order_count = len(orders.json()) if orders.status_code == 200 else 0
except Exception:
    farm_count = plot_count = livestock_count = order_count = 0

try:
    wallet_response = httpx.get(f"{API_URL}/wallet/", headers=headers, timeout=10)
    wallet_balance = (
        wallet_response.json().get("balance_ugx", 0)
        if wallet_response.status_code == 200
        else None
    )
except httpx.HTTPError:
    wallet_balance = None

try:
    review_response = httpx.get(f"{API_URL}/reviews/prompt", headers=headers, timeout=10)
    review_status = review_response.json() if review_response.status_code == 200 else {}
except httpx.HTTPError:
    review_status = {}

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Account", user["role"].replace("_", " ").title())
with c2:
    st.metric("Location", user.get("location_name") or "Not set")
with c3:
    st.metric("Phone", user.get("phone") or "Not set")

d1, d2, d3, d4, d5 = st.columns(5)
d1.metric("Farms", farm_count)
d2.metric("Crop plots", plot_count)
d3.metric("Livestock", livestock_count)
d4.metric("Orders", order_count)
d5.metric(
    "Wallet balance",
    f"UGX {wallet_balance:,.0f}" if wallet_balance is not None else "Unavailable",
)

if review_status.get("eligible"):
    st.info("You have been using Harvesta for one week. Please rate your experience.")
    rating = st.select_slider("Rate Harvesta (1–5)", options=[1, 2, 3, 4, 5], value=5)
    comments = st.text_area("Optional feedback", key="dashboard_review_comments")
    if st.button("Submit app rating", type="primary"):
        try:
            review_submit = httpx.post(
                f"{API_URL}/reviews/",
                json={"rating": rating, "comments": comments or None},
                headers=headers,
                timeout=10,
            )
            if review_submit.status_code == 201:
                st.success("Thank you for rating Harvesta.")
                st.rerun()
            st.error(review_submit.json().get("detail", "Could not submit rating."))
        except httpx.HTTPError as exc:
            st.error(f"Could not submit rating: {exc}")

st.markdown("### Quick actions")
a1, a2, a3, a4 = st.columns(4)
with a1:
    if st.button("Browse Marketplace", use_container_width=True):
        st.switch_page("pages/1_Marketplace.py")
with a2:
    if st.button("View orders", use_container_width=True):
        st.switch_page("pages/3_Orders_and_Deliveries.py")
with a3:
    if st.button("Check weather", use_container_width=True):
        st.switch_page("pages/4_Farm_Weather.py")
with a4:
    if st.button("Wallet & settings", use_container_width=True):
        st.switch_page("pages/7_Account_Settings.py")

st.markdown("---")
st.caption("\u00a9 2026 Harvesta. All rights reserved.")
