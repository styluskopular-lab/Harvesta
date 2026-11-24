from pathlib import Path

import httpx
import streamlit as st
from api_config import get_api_url, normalize_api_url

st.set_page_config(
    page_title="Farm Weather | Harvesta",
    page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"),
    layout="wide",
)

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
if st.session_state.get("dark_mode", False):
    st.markdown('<style>.stApp{background:#102319!important;color:#edf5ee!important}.stApp h1,.stApp h2,.stApp h3,.stApp p{color:#edf5ee!important}[data-testid="stSidebar"]{background:#13291b!important}</style>', unsafe_allow_html=True)

DEFAULT_API_URL = get_api_url()
API_URL = normalize_api_url(st.sidebar.text_input("API URL", value=DEFAULT_API_URL, key="api_weather"))
st.title("Farm Weather")
st.caption("Seven-day weather forecast for farm planning")

district = st.selectbox("Location", [
    ("Kampala", 0.3476, 32.5825),
    ("Mukono", 0.3550, 32.7550),
    ("Mbarara", -0.6072, 30.6545),
    ("Gulu", 2.7663, 32.3056),
    ("Kabale", -1.2486, 29.9899),
    ("Mbale", 1.0822, 34.1754),
], format_func=lambda item: item[0])

lat = st.number_input("Latitude", value=district[1], format="%.4f")
lon = st.number_input("Longitude", value=district[2], format="%.4f")

if st.button("Get forecast", type="primary", use_container_width=True):
    try:
        response = httpx.get(
            f"{API_URL}/weather/forecast",
            params={"latitude": lat, "longitude": lon},
            timeout=15,
        )
        response.raise_for_status()
        forecast = response.json()
        current = forecast.get("current") or {}
        c1, c2, c3 = st.columns(3)
        c1.metric("Temperature", f"{current.get('temperature_2m', '—')} C")
        c2.metric("Humidity", f"{current.get('relative_humidity_2m', '—')} %")
        c3.metric("Rain", f"{current.get('precipitation', '—')} mm")

        daily = forecast.get("daily")
        if daily:
            st.subheader("Next seven days")
            for index, day in enumerate(daily["time"]):
                with st.container(border=True):
                    st.write(f"**{day}**")
                    st.write(
                        f"Temperature: {daily['temperature_2m_min'][index]} - "
                        f"{daily['temperature_2m_max'][index]} C"
                    )
                    st.write(
                        f"Rain chance: "
                        f"{daily['precipitation_probability_max'][index]}%"
                    )
        if forecast.get("warning"):
            st.warning(forecast["warning"])
    except Exception as exc:
        st.error(f"Weather service unavailable: {exc}")
