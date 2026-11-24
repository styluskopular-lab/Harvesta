import streamlit as st
import httpx
from pathlib import Path
from streamlit_app.api_config import get_api_url, normalize_api_url

st.set_page_config(page_title="Orders & Deliveries | Harvesta", page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"), layout="wide")

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
if st.session_state.get("dark_mode", False):
    st.markdown('<style>.stApp{background:#102319!important;color:#edf5ee!important}.stApp h1,.stApp h2,.stApp h3,.stApp p{color:#edf5ee!important}[data-testid="stSidebar"]{background:#13291b!important}</style>', unsafe_allow_html=True)

DEFAULT_API_URL = get_api_url()
API_URL = normalize_api_url(st.sidebar.text_input("API URL", value=DEFAULT_API_URL, key="api_ord"))

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Please log in first from the Home page.")
    st.stop()

def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

st.title("Orders & Deliveries")

tab1, tab2, tab3 = st.tabs(["My Orders", "Deliveries", "Vans"])

with tab1:
    st.subheader("Orders")
    try:
        r = httpx.get(f"{API_URL}/orders/", headers=headers(), timeout=10)
        orders = r.json() if r.status_code == 200 else []
    except Exception as e:
        st.error(str(e))
        orders = []

    if not orders:
        st.info("No orders yet.")
    else:
        for o in orders:
            with st.expander(f"Order #{o['id']} – {o['status'].upper()} – UGX {o['total_amount']:,.0f}"):
                st.write(f"**Address:** {o['delivery_address']}")
                st.write(f"**Created:** {o['created_at'][:19]}")
                if o.get("notes"):
                    st.write(f"**Notes:** {o['notes']}")
                st.write("**Items:**")
                for item in o.get("items", []):
                    st.write(f"- Product ID {item['product_id']}: {item['quantity']} × {item['unit_price']:,.0f} = {item['subtotal']:,.0f}")

with tab2:
    st.subheader("Deliveries")
    try:
        r = httpx.get(f"{API_URL}/deliveries/", headers=headers(), timeout=10)
        deliveries = r.json() if r.status_code == 200 else []
    except Exception:
        deliveries = []

    if not deliveries:
        st.info("No deliveries found.")
    else:
        for d in deliveries:
            status_emoji = {
                "assigned": "🟡",
                "picked_up": "🟠",
                "in_transit": "🔵",
                "delivered": "🟢",
                "failed": "🔴",
            }.get(d["status"], "⚪")
            st.write(f"{status_emoji} **Delivery #{d['id']}** for Order #{d['order_id']} → `{d['status']}`")

with tab3:
    st.subheader("Harvesta Delivery Vans")
    try:
        r = httpx.get(f"{API_URL}/deliveries/vans", timeout=10)
        vans = r.json() if r.status_code == 200 else []
    except Exception:
        vans = []

    if vans:
        for v in vans:
            st.write(f"**{v['plate_number']}** ({v['brand_name']}) – Capacity: {v['capacity_kg']} kg – Status: `{v['status']}` – Location: {v.get('current_location', '—')}")
    else:
        st.info("No vans registered.")
