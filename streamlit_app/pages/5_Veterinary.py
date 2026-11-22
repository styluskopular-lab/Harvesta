from pathlib import Path
from datetime import date
import httpx
import streamlit as st
from api_config import get_api_url

st.set_page_config(
    page_title="Veterinary | Harvesta",
    page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"),
    layout="wide",
)

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
if st.session_state.get("dark_mode", False):
    st.markdown('<style>.stApp{background:#102319!important;color:#edf5ee!important}.stApp h1,.stApp h2,.stApp h3,.stApp p{color:#edf5ee!important}[data-testid="stSidebar"]{background:#13291b!important}</style>', unsafe_allow_html=True)

DEFAULT_API_URL = get_api_url()
API_URL = st.sidebar.text_input("API URL", value=DEFAULT_API_URL, key="api_vet")

if "token" not in st.session_state or not st.session_state.token:
    st.warning("Please sign in before booking veterinary support.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
st.title("Veterinary Care")
st.caption("Find animal-care support across Uganda")

district = st.text_input("District", value="Mukono")
try:
    providers_response = httpx.get(
        f"{API_URL}/veterinary/providers",
        params={"district": district},
        timeout=10,
    )
    providers = providers_response.json() if providers_response.status_code == 200 else []
except Exception:
    providers = []

if not providers:
    st.info("No available providers match this district.")
else:
    for provider in providers:
        with st.container(border=True):
            st.subheader(provider["name"])
            st.write(provider["specialization"])
            st.write(f"District: {provider['district']}")
            st.write(f"Phone: {provider['phone']}")
            if provider.get("description"):
                st.caption(provider["description"])

st.divider()
st.subheader("Request a visit")
provider_names = {provider["id"]: provider["name"] for provider in providers}
if provider_names:
    provider_id = st.selectbox("Veterinarian", list(provider_names), format_func=lambda value: provider_names[value])
    animal = st.selectbox("Animal", ["Cow", "Goat", "Chicken", "Pig", "Sheep", "Horse", "Dog", "Cat"])
    symptoms = st.text_area("Symptoms or care needed")
    visit_date = st.date_input("Preferred date", value=date.today())
    if st.button("Book veterinary visit", type="primary", use_container_width=True):
        if len(symptoms.strip()) < 3:
            st.error("Describe the symptoms or requested care.")
        else:
            response = httpx.post(
                f"{API_URL}/veterinary/bookings",
                headers=headers,
                json={
                    "veterinarian_id": provider_id,
                    "animal_type": animal,
                    "symptoms": symptoms,
                    "preferred_date": str(visit_date),
                },
                timeout=10,
            )
            if response.status_code == 201:
                st.success("Visit requested. The veterinarian will confirm the booking.")
            else:
                st.error(response.json().get("detail", "Booking failed"))
