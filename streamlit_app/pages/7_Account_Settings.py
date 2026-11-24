from pathlib import Path
import csv
import io
import json

import httpx
import streamlit as st
from streamlit_app.api_config import get_api_url, normalize_api_url

st.set_page_config(
    page_title="Account Settings | Harvesta",
    page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"),
    layout="wide",
)

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

DEFAULT_API_URL = get_api_url()
API_URL = normalize_api_url(st.sidebar.text_input("API URL", value=DEFAULT_API_URL, key="api_account"))
if not st.session_state.get("token"):
    st.warning("Please sign in first.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}
st.title("Account Settings")
user = st.session_state.get("user") or {}
st.write(f"Signed in as **{user.get('full_name', 'Harvesta user')}**")

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
