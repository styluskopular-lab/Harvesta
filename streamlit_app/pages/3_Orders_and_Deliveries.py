import sys
from pathlib import Path

import httpx
import streamlit as st

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from streamlit_app.api_config import sidebar_api_url
except ImportError:
    from api_config import sidebar_api_url

st.set_page_config(
    page_title="Orders & Deliveries | Harvesta",
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

API_URL = sidebar_api_url()

if not st.session_state.get("token"):
    st.warning("Please log in first from the Home page.")
    st.stop()


def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


user = st.session_state.get("user") or {}
role = user.get("role")


def response_error(response, fallback):
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    return detail or fallback


def render_delivery_summary(delivery):
    if not delivery:
        st.info("Delivery matching is pending.")
        return
    status_text = delivery.get("status", "open").replace("_", " ").title()
    fee = delivery.get("estimated_fee_ugx", 5000)
    st.write(f"**Delivery:** {status_text} · Estimated fee: UGX {fee:,.0f}")
    driver_name = delivery.get("driver_name")
    if driver_name:
        driver_phone = delivery.get("driver_phone")
        contact = f" ({driver_phone})" if driver_phone else ""
        st.write(f"**Driver:** {driver_name}{contact}")
    else:
        st.write("**Driver:** Awaiting a driver")


def render_payment(order, widget_key=None, allow_confirmation=True):
    methods = {
        "cash_on_delivery": "Cash on Delivery",
        "mobile_money": "MTN / Airtel Mobile Money",
    }
    method = methods.get(
        order.get("payment_method"), order.get("payment_method", "Unknown")
    )
    payment_status = order.get("payment_status", "pending")
    display_status = "Paid" if payment_status == "paid" else "Pending"
    st.write(f"**Payment:** {method} · {display_status} in UGX")
    if order.get("payment_reference"):
        st.write(f"**Transaction reference:** {order['payment_reference']}")

    if (
        allow_confirmation
        and payment_status != "paid"
        and role in {"admin", "shop_manager"}
    ):
        if st.button(
            "Confirm payment received",
            key=widget_key or f"confirm_payment_order_{order['id']}",
        ):
            try:
                response = httpx.patch(
                    f"{API_URL}/orders/{order['id']}/payment",
                    json={},
                    headers=headers(),
                    timeout=10,
                )
                if response.status_code == 200:
                    st.success("Payment marked as paid.")
                    st.rerun()
                st.error(response_error(response, "Could not confirm payment."))
            except httpx.HTTPError as exc:
                st.error(f"Could not confirm payment: {exc}")


def render_driver_details(delivery):
    st.write(f"**Pickup district:** {delivery['pickup_district']}")
    st.write(f"**Delivery district:** {delivery['delivery_district']}")
    st.write("**Produce:**")
    for item in delivery.get("items", []):
        st.write(
            f"- {item['product_name']}: {item['quantity']:g} {item['unit']} "
            f"(pickup: {item['pickup_district']})"
        )
    st.write(f"**Estimated delivery fee:** UGX {delivery['estimated_fee_ugx']:,.0f}")


st.title("Orders & Deliveries")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["My Orders", "Incoming Orders", "Driver Board", "Deliveries", "Vans"]
)

with tab1:
    st.subheader("Orders")
    try:
        response = httpx.get(f"{API_URL}/orders/", headers=headers(), timeout=10)
        orders = response.json() if response.status_code == 200 else []
        if response.status_code != 200:
            st.error(response_error(response, "Could not load orders."))
    except httpx.HTTPError as exc:
        st.error(f"Could not load orders: {exc}")
        orders = []

    if not orders:
        st.info("No orders yet.")
    for order in orders:
        with st.expander(
            f"Order #{order['id']} – {order['status'].upper()} – "
            f"UGX {order['total_amount']:,.0f}"
        ):
            st.write(f"**Address:** {order['delivery_address']}")
            st.write(f"**Created:** {order['created_at'][:19]}")
            if order.get("notes"):
                st.write(f"**Notes:** {order['notes']}")
            render_payment(order)
            render_delivery_summary(order.get("delivery"))
            st.write("**Items:**")
            for item in order.get("items", []):
                product_name = item.get("product_name") or f"Product #{item['product_id']}"
                unit = item.get("unit") or "unit"
                st.write(
                    f"- {product_name}: {item['quantity']} {unit} × "
                    f"UGX {item['unit_price']:,.0f} = UGX {item['subtotal']:,.0f}"
                )

with tab2:
    if role != "farmer":
        st.info("Incoming produce orders are available to farmer accounts.")
    else:
        st.subheader("Orders for your produce")
        try:
            response = httpx.get(
                f"{API_URL}/orders/incoming",
                headers=headers(),
                timeout=10,
            )
            incoming_orders = response.json() if response.status_code == 200 else []
            if response.status_code != 200:
                st.error(response_error(response, "Could not load incoming orders."))
        except httpx.HTTPError as exc:
            st.error(f"Could not load incoming orders: {exc}")
            incoming_orders = []

        if not incoming_orders:
            st.info("No buyers have ordered your produce yet.")
        for order in incoming_orders:
            with st.expander(
                f"Order #{order['id']} · {order['status'].title()} · "
                f"UGX {order['total_amount']:,.0f}"
            ):
                st.write(f"**Delivery address:** {order['delivery_address']}")
                st.write(f"**Placed:** {order['created_at'][:19]}")
                render_payment(order)
                render_delivery_summary(order.get("delivery"))
                for item in order["items"]:
                    st.write(
                        f"- {item['product_name']}: {item['quantity']} {item['unit']} "
                        f"× UGX {item['unit_price']:,.0f} = UGX {item['subtotal']:,.0f}"
                    )

with tab3:
    if role != "driver":
        st.info("The open delivery board is available to driver accounts.")
    else:
        st.subheader("Open delivery jobs")
        try:
            response = httpx.get(
                f"{API_URL}/deliveries/open",
                headers=headers(),
                timeout=10,
            )
            open_deliveries = response.json() if response.status_code == 200 else []
            if response.status_code != 200:
                st.error(response_error(response, "Could not load open deliveries."))
        except httpx.HTTPError as exc:
            st.error(f"Could not load open deliveries: {exc}")
            open_deliveries = []

        if not open_deliveries:
            st.info("No open orders are awaiting transport.")
        for delivery in open_deliveries:
            with st.expander(
                f"Delivery #{delivery['id']} · Order #{delivery['order_id']} · "
                f"UGX {delivery['estimated_fee_ugx']:,.0f}"
            ):
                render_driver_details(delivery)
                if st.button(
                    "Accept Delivery",
                    key=f"accept_delivery_{delivery['id']}",
                    type="primary",
                ):
                    try:
                        response = httpx.post(
                            f"{API_URL}/deliveries/{delivery['id']}/accept",
                            headers=headers(),
                            timeout=10,
                        )
                        if response.status_code == 200:
                            st.success("Delivery accepted.")
                            st.rerun()
                        st.error(response_error(response, "Could not accept delivery."))
                    except httpx.HTTPError as exc:
                        st.error(f"Could not accept delivery: {exc}")

with tab4:
    st.subheader("Deliveries")
    try:
        response = httpx.get(f"{API_URL}/deliveries/", headers=headers(), timeout=10)
        deliveries = response.json() if response.status_code == 200 else []
        if response.status_code != 200:
            st.error(response_error(response, "Could not load deliveries."))
    except httpx.HTTPError as exc:
        st.error(f"Could not load deliveries: {exc}")
        deliveries = []

    next_status = {
        "accepted": ("picked_up", "Mark Picked Up"),
        "picked_up": ("in_transit", "Mark In Transit"),
        "in_transit": ("delivered", "Mark Delivered"),
    }
    if not deliveries:
        st.info("No deliveries found.")
    for delivery in deliveries:
        with st.expander(
            f"Delivery #{delivery['id']} · Order #{delivery['order_id']} · "
            f"{delivery['status'].replace('_', ' ').title()}"
        ):
            render_driver_details(delivery)
            render_payment(
                delivery,
                widget_key=f"confirm_payment_delivery_{delivery['id']}",
                allow_confirmation=False,
            )
            render_delivery_summary(delivery)
            if role == "driver" and delivery.get("driver_id") == user.get("id"):
                transition = next_status.get(delivery["status"])
                if transition and st.button(
                    transition[1],
                    key=f"advance_delivery_{delivery['id']}_{transition[0]}",
                ):
                    try:
                        response = httpx.patch(
                            f"{API_URL}/deliveries/{delivery['id']}",
                            json={"status": transition[0]},
                            headers=headers(),
                            timeout=10,
                        )
                        if response.status_code == 200:
                            st.success("Delivery status updated.")
                            st.rerun()
                        st.error(
                            response_error(
                                response,
                                "Could not update delivery status.",
                            )
                        )
                    except httpx.HTTPError as exc:
                        st.error(f"Could not update delivery status: {exc}")

with tab5:
    st.subheader("Harvesta Delivery Vans")
    try:
        response = httpx.get(f"{API_URL}/deliveries/vans", timeout=10)
        vans = response.json() if response.status_code == 200 else []
        if response.status_code != 200:
            st.error(response_error(response, "Could not load delivery vans."))
    except httpx.HTTPError as exc:
        st.error(f"Could not load delivery vans: {exc}")
        vans = []

    if vans:
        for van in vans:
            st.write(
                f"**{van['plate_number']}** ({van['brand_name']}) – "
                f"Capacity: {van['capacity_kg']} kg – Status: `{van['status']}` – "
                f"Location: {van.get('current_location', '—')}"
            )
    else:
        st.info("No vans registered.")
