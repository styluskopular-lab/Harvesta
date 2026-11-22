from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Privacy Policy & Terms | Harvesta",
    page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"),
    layout="wide",
)

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.title("Privacy Policy & Terms of Use")
st.caption("Rules, laws and agricultural guidelines for Harvesta")

st.header("Uganda laws and electronic transactions")
st.write(
    "The Data Protection and Privacy Act, 2019 governs explicit consent for NIN, date of birth, phone, "
    "location and farm records, encryption at rest, export/deletion rights and applicable PDPO registration."
)
st.write(
    "The Computer Misuse Act, 2011 (as amended) prohibits unauthorized access, account sharing, "
    "electronic fraud and tampering with market or logistics records."
)
st.write(
    "The Electronic Transactions Act, 2011 and Electronic Signatures Act, 2011 support lawful digital "
    "marketplace contracts, e-receipts and timestamped delivery confirmations."
)
st.write(
    "The Copyright and Neighbouring Rights Act, 2006 and NITA-U Act, 2009 protect Harvesta software/UI "
    "and user-uploaded media rights."
)

st.header("Data we collect")
st.write(
    "Harvesta stores the account holder's name, Gmail address, selected country code and phone number, "
    "district, sub-county/parish, village, exact location or P.O. Box, NIN, date of birth, next of kin, "
    "account role, farmer or driver KYC fields, farm records, crop plots, livestock records, orders and consent record."
)

st.header("Storage and protection")
st.write(
    "Passwords are hashed and never stored as plain text. Access is protected with signed tokens. "
    "Production deployment should encrypt databases and backups, restrict administrative access, use TLS and apply retention controls."
)

st.header("Farmer control")
st.write(
    "Users may export account and farm data as JSON or CSV and request or initiate account deletion from Account Settings."
)

st.header("Legal use")
st.write(
    "Do not upload unlawful, infringing or malicious content. Users remain responsible for content they submit. "
    "Harvesta does not grant ownership rights to independent user submissions."
)

st.header("Copyright")
st.write(
    "Users retain ownership of original data and text they submit, subject to licences needed to lawfully use it on Harvesta. "
    "Reusing Harvesta branding or original platform content requires permission."
)

st.markdown("---")
st.caption("\u00a9 2026 Harvesta. All rights reserved.")
