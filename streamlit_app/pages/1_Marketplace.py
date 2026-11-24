import streamlit as st
import httpx
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from streamlit_app.api_config import sidebar_api_url
except ImportError:
    from api_config import sidebar_api_url

st.set_page_config(page_title="Marketplace | Harvesta", page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"), layout="wide")

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
if st.session_state.get("dark_mode", False):
    st.markdown('<style>.stApp{background:#102319!important;color:#edf5ee!important}.stApp h1,.stApp h2,.stApp h3,.stApp p{color:#edf5ee!important}[data-testid="stSidebar"]{background:#13291b!important}.market-card{background:#193424!important;border-color:#294936!important}</style>', unsafe_allow_html=True)

API_URL = sidebar_api_url()

if "token" not in st.session_state:
    st.session_state.token = None
if "cart" not in st.session_state:
    st.session_state.cart = []


def headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


st.markdown("## Marketplace")
st.caption("Ugandan produce and brands only")

# Filters
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    category = st.selectbox("Category", ["All", "crop", "livestock", "processed", "other"])
with col_f2:
    search = st.text_input("Search products")
with col_f3:
    st.write("")  # spacer
    if st.button("Refresh"):
        st.rerun()

# Fetch products
params = {"status": "available", "limit": 50}
if category != "All":
    params["category"] = category
if search:
    params["search"] = search

try:
    r = httpx.get(f"{API_URL}/products/", params=params, timeout=10)
    products = r.json() if r.status_code == 200 else []
except Exception as e:
    st.error(f"Could not load products: {e}")
    products = []

if not products:
    st.info("No products available right now. Farmers can add produce from the Farm page.")
else:
    # Display in grid
    cols = st.columns(2)
    for idx, p in enumerate(products):
        with cols[idx % 2]:
            with st.container():
                st.markdown('<div class="market-card">', unsafe_allow_html=True)
                if p.get("image_url"):
                    st.image(p["image_url"], use_column_width=True)
                st.markdown(
                    f'<div class="market-card-body">'
                    f'<span class="status-pill">{p["category"].title()}</span>'
                    f'<h3>{p["name"]}</h3>'
                    f'<div class="price">UGX {p["price_per_unit"]:,.0f} / {p["unit"]}</div>'
                    f'<p>{p["quantity"]:,.0f} {p["unit"]} available</p>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"{p.get('farmer_name') or 'Local farmer'} · "
                    f"{p.get('farmer_location') or 'Uganda'}"
                )
                if p.get("description"):
                    st.caption(p["description"][:80])

                qty = st.number_input(
                    "Qty", min_value=0.5, max_value=float(p["quantity"]),
                    value=1.0, step=0.5, key=f"qty_{p['id']}"
                )
                if st.button("Add to Cart", key=f"add_{p['id']}", use_container_width=True):
                    st.session_state.cart.append({
                        "product_id": p["id"],
                        "name": p["name"],
                        "quantity": qty,
                        "unit_price": p["price_per_unit"],
                        "unit": p["unit"],
                    })
                    st.success(f"Added {qty} {p['unit']} of {p['name']}")
                st.markdown('</div></div>', unsafe_allow_html=True)

st.divider()
st.subheader("Your Cart")

if not st.session_state.cart:
    st.write("Cart is empty.")
else:
    total = 0
    for item in st.session_state.cart:
        sub = item["quantity"] * item["unit_price"]
        total += sub
        st.write(f"- {item['name']}: {item['quantity']} {item['unit']} × UGX {item['unit_price']:,.0f} = **UGX {sub:,.0f}**")

    st.markdown(f"### Total: **UGX {total:,.0f}**")

    address = st.text_input("Delivery Address", placeholder="e.g. Nakawa, Kampala, Uganda")
    notes = st.text_area("Notes (optional)")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("Clear Cart"):
            st.session_state.cart = []
            st.rerun()
    with col_c2:
        if st.button("Place Order", type="primary"):
            if not st.session_state.token:
                st.error("Please log in first (use the Home page sidebar).")
            elif st.session_state.get("user", {}).get("role") != "buyer":
                st.error("Only buyer accounts can place orders.")
            elif not address:
                st.error("Please enter a delivery address.")
            else:
                payload = {
                    "items": [{"product_id": i["product_id"], "quantity": i["quantity"]} for i in st.session_state.cart],
                    "delivery_address": address,
                    "notes": notes or None,
                }
                try:
                    r = httpx.post(
                        f"{API_URL}/orders/",
                        json=payload,
                        headers=headers(),
                        timeout=15,
                    )
                    if r.status_code in (200, 201):
                        st.success(f"Order placed successfully! Order ID: {r.json()['id']}")
                        st.session_state.cart = []
                        st.balloons()
                    else:
                        st.error(r.json().get("detail", "Order failed"))
                except Exception as e:
                    st.error(f"Error: {e}")
