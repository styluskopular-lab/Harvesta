import streamlit as st
import httpx
import sys
from datetime import date, timedelta
from pathlib import Path

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from streamlit_app.api_config import sidebar_api_url
except ImportError:
    from api_config import sidebar_api_url

st.set_page_config(page_title="My Farm | Harvesta", page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"), layout="wide")

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
if st.session_state.get("dark_mode", False):
    st.markdown('<style>.stApp{background:#102319!important;color:#edf5ee!important}.stApp h1,.stApp h2,.stApp h3,.stApp p{color:#edf5ee!important}[data-testid="stSidebar"]{background:#13291b!important}</style>', unsafe_allow_html=True)

API_URL = sidebar_api_url()

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Please log in as a **farmer** from the Home page first.")
    st.stop()

def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

st.title("My Farm")

# --- Farms ---
st.subheader("Your Farms")
try:
    r = httpx.get(f"{API_URL}/farms/me", headers=headers(), timeout=10)
    farms = r.json() if r.status_code == 200 else []
except Exception:
    farms = []

if farms:
    for f in farms:
        with st.expander(f"{f['name']} – {f['location']}"):
            st.write(f"**Size:** {f.get('size_hectares', 'N/A')} hectares")
            st.write(f"**Crops:** {f.get('crop_types', '—')}")
            st.write(f"**Livestock:** {f.get('livestock', '—')}")
            st.write(f.get("description", ""))
else:
    st.info("No farm registered yet.")

with st.expander("Register a new farm"):
    with st.form("new_farm"):
        name = st.text_input("Farm Name")
        location = st.text_input("Location")
        size = st.number_input("Size (hectares)", min_value=0.1, value=5.0)
        crops = st.text_input("Crop types (comma-separated)", value="maize,tomatoes")
        livestock = st.text_input("Livestock (comma-separated)", value="")
        desc = st.text_area("Description")
        if st.form_submit_button("Create Farm"):
            payload = {
                "name": name,
                "location": location,
                "size_hectares": size,
                "crop_types": crops,
                "livestock": livestock or None,
                "description": desc or None,
            }
            r = httpx.post(f"{API_URL}/farms/", json=payload, headers=headers(), timeout=10)
            if r.status_code in (200, 201):
                st.success("Farm created!")
                st.rerun()
            else:
                st.error(r.json().get("detail", "Failed"))

st.divider()

# --- Products ---
st.subheader("Your Products")
try:
    r = httpx.get(f"{API_URL}/products/farmer/me", headers=headers(), timeout=10)
    my_products = r.json() if r.status_code == 200 else []
except Exception:
    my_products = []

if my_products:
    for p in my_products:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{p['name']}** – {p['quantity']} {p['unit']} @ UGX {p['price_per_unit']:,.0f}")
            st.caption(p.get("farmer_location") or "Uganda")
        with col2:
            st.caption(p["status"])
        with col3:
            st.caption(p["category"])
else:
    st.info("You have no products listed yet.")

with st.expander("List a new product"):
    farmer = st.session_state.get("user") or {}
    listing_location = (
        farmer.get("district")
        or farmer.get("location_name")
        or "your account location"
    )
    st.caption(f"Marketplace buyers will see your listing location as {listing_location}.")
    with st.form("new_product"):
        pname = st.text_input("Product Name")
        category = st.selectbox("Category", ["crop", "livestock", "processed", "other"])
        quantity = st.number_input("Quantity", min_value=0.1, value=50.0)
        unit = st.selectbox("Unit", ["kg", "pieces", "liters", "bunches", "crates"])
        price = st.number_input("Price per unit (UGX)", min_value=100.0, value=5000.0)
        harvest = st.date_input("Harvest Date", value=date.today())
        desc = st.text_area("Description")
        image_url = st.text_input("Image URL (optional)")
        farm_id = st.number_input("Farm ID (optional)", min_value=0, value=0)

        if st.form_submit_button("Publish Product"):
            payload = {
                "name": pname,
                "category": category,
                "quantity": quantity,
                "unit": unit,
                "price_per_unit": price,
                "harvest_date": str(harvest),
                "description": desc or None,
                "image_url": image_url or None,
                "farm_id": farm_id if farm_id > 0 else None,
                "status": "available",
            }
            r = httpx.post(f"{API_URL}/products/", json=payload, headers=headers(), timeout=10)
            if r.status_code in (200, 201):
                st.success("Product listed successfully!")
                st.rerun()
            else:
                st.error(r.json().get("detail", "Failed to create product"))

st.divider()
st.subheader("Crop Plots")

try:
    plot_response = httpx.get(f"{API_URL}/farm-records/crop-plots", headers=headers(), timeout=10)
    crop_plots = plot_response.json() if plot_response.status_code == 200 else []
except Exception:
    crop_plots = []

if crop_plots:
    for plot in crop_plots:
        planting = date.fromisoformat(plot["planting_date"])
        harvest = date.fromisoformat(plot["expected_harvest_date"]) if plot.get("expected_harvest_date") else None
        c1, c2 = st.columns([4, 1])
        with c1:
            st.write(f"**{plot['plot_name']}** - {plot['crop_type']}")
            st.caption(f"Planting date: {planting.strftime('%d %b %Y')}")
            if harvest:
                remaining = (harvest - date.today()).days
                countdown = f"{remaining} days remaining" if remaining >= 0 else f"{abs(remaining)} days overdue"
                st.write(f"Expected harvest: {harvest.strftime('%d %b %Y')} ({countdown})")
                total_days = max((harvest - planting).days, 1)
                elapsed = max(0, min((date.today() - planting).days, total_days))
                progress = elapsed / total_days
                if remaining <= 0:
                    growth_stage = "Harvest Ready"
                    st.success("HARVEST READY")
                elif progress < 0.10:
                    growth_stage = "Land Preparation"
                elif progress < 0.25:
                    growth_stage = "Planting"
                elif progress < 0.50:
                    growth_stage = "Vegetative/Weeding"
                elif progress < 0.75:
                    growth_stage = "Flowering/Pest Control"
                elif progress < 1:
                    growth_stage = "Grain/Fruit Filling"
                else:
                    growth_stage = "Harvest Ready"
                st.caption(f"Current growth stage: {growth_stage}")
                st.progress(min(max(progress, 0.0), 1.0))
        with c2:
            if st.button("Delete", key=f"delete_plot_{plot['id']}"):
                deleted = httpx.delete(f"{API_URL}/farm-records/crop-plots/{plot['id']}", headers=headers(), timeout=10)
                if deleted.status_code == 204:
                    st.rerun()
                else:
                    st.error("Could not delete crop plot.")
else:
    st.info("No crop plots registered.")

with st.expander("Add a crop plot"):
    stages = [
        "Land Preparation",
        "Planting",
        "Weeding & Fertilization",
        "Pest/Disease Control",
        "Harvesting",
        "Post-Harvest Handling",
    ]
    with st.form("crop_plot_form"):
        plot_name = st.text_input("Plot name", placeholder="North Maize Plot")
        crop_type = st.selectbox("Crop type", [
            "Maize", "Matooke", "Beans", "Irish Potatoes",
            "Cassava", "Coffee Robusta", "Coffee Arabica",
            "Rice", "Cabbage", "Tomatoes",
        ])
        variety = st.text_input("Variety or local cultivar")
        planting_date = st.date_input("Planting date", value=date.today())
        expected_harvest_days = st.number_input(
            "Expected harvest days",
            min_value=1,
            max_value=3650,
            value=120,
            step=1,
        )
        stage = st.selectbox("Crop stage", stages)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Crop Plot", use_container_width=True)
        if submitted:
            if not plot_name.strip():
                st.error("Enter a plot name.")
            else:
                response = httpx.post(
                    f"{API_URL}/farm-records/crop-plots",
                    headers=headers(),
                    json={
                        "plot_name": plot_name,
                        "crop_type": crop_type,
                        "variety": variety or None,
                        "planting_date": str(planting_date),
                        "expected_harvest_days": int(expected_harvest_days),
                        "crop_stage": stage,
                        "notes": notes or None,
                    },
                    timeout=10,
                )
                if response.status_code == 201:
                    st.success("Crop plot added.")
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Could not add crop plot"))

st.divider()
st.subheader("Livestock Reproduction Tracker")

try:
    livestock_response = httpx.get(f"{API_URL}/farm-records/livestock", headers=headers(), timeout=10)
    livestock = livestock_response.json() if livestock_response.status_code == 200 else []
except Exception:
    livestock = []

breeds = {
    "Cattle": ["Ankole", "Friesian", "Boran", "Crossbred dairy", "Zebu"],
    "Goat": ["Mubende", "Kigezi", "Boer", "Crossbred", "Small East African"],
    "Pig": ["Large White", "Landrace", "Camborough", "Crossbred"],
}

if livestock:
    for animal in livestock:
        status = animal["status"]
        due = animal.get("due_date")
        c1, c2 = st.columns([4, 1])
        with c1:
            st.write(f"**{animal['animal_name']}** - {animal['animal_type']} ({animal['breed']})")
            if due:
                st.write(f"Due date: {due}")
            if status == "OVERDUE":
                st.error("OVERDUE")
            elif status == "DUE SOON — 14 DAYS OUT":
                st.warning("DUE SOON — 14 DAYS OUT")
            else:
                st.success("ON TRACK")
        with c2:
            if st.button("Delete", key=f"delete_animal_{animal['id']}"):
                deleted = httpx.delete(f"{API_URL}/farm-records/livestock/{animal['id']}", headers=headers(), timeout=10)
                if deleted.status_code == 204:
                    st.rerun()
                else:
                    st.error("Could not delete livestock record.")
else:
    st.info("No livestock records registered.")

with st.expander("Register an animal"):
    with st.form("livestock_form"):
        animal_name = st.text_input("Animal name or identifier")
        animal_type = st.selectbox("Animal type", list(breeds))
        breed = st.selectbox("Breed", breeds[animal_type])
        tag_number = st.text_input("Tag number (optional)")
        sex = st.selectbox("Sex", ["Female", "Male"])
        service_date = st.date_input("Service / breeding date", value=date.today())
        track_service = st.checkbox("Track pregnancy / breeding cycle", value=True)
        submitted = st.form_submit_button("Register Livestock", use_container_width=True)
        if submitted:
            if not animal_name.strip():
                st.error("Enter an animal name or identifier.")
            else:
                response = httpx.post(
                    f"{API_URL}/farm-records/livestock",
                    headers=headers,
                    json={
                        "animal_name": animal_name,
                        "animal_type": animal_type,
                        "breed": breed,
                        "tag_number": tag_number or None,
                        "sex": sex,
                        "service_date": str(service_date) if track_service else None,
                    },
                    timeout=10,
                )
                if response.status_code == 201:
                    st.success("Livestock record added.")
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Could not register livestock"))

st.markdown("---")
st.caption("\u00a9 2026 Harvesta. All rights reserved.")
