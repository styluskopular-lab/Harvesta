from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Regulatory & Compliance Hub | Harvesta",
    page_icon=str(Path(__file__).parents[2] / "harvesta_icon.png"),
    layout="wide",
)

css_path = Path(__file__).parents[1] / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.title("Regulatory & Compliance Hub")
st.markdown(
    '<div style="background:#E5E7EB;border:2px solid #000000;padding:16px;color:#000000;font-size:16px;">'
    '<strong>Farmer organizations and agricultural standards</strong></div>',
    unsafe_allow_html=True,
)

st.header("Uganda National Farmers Federation (UNFFE)")
st.write(
    "UNFFE-aligned structures use Village Special Interest Groups, Parish/Sub-County Committees "
    "and District Farmer Associations. Key functions include climate-smart capacity building, "
    "farmer advocacy, and forward/backward market linkages."
)

st.header("National Agricultural Research Organisation (NARO)")
st.write(
    "NARO-certified seed varieties, animal breeds and post-harvest technologies must carry visible "
    "source attribution. Reuse of NARO research and plant varieties must respect National Agricultural "
    "Research Act 2005 and NARO intellectual-property rules covering new plant varieties, utility models "
    "and traditional knowledge."
)

st.header("MAAIF")
st.write(
    "Vision: A competitive, profitable and sustainable agricultural sector.<br>"
    "Mission: To transform subsistence farming to commercial agriculture.<br>"
    "Core Values: Accountability, Professionalism, Integrity, Client-Focus and Teamwork.",
    unsafe_allow_html=True,
)
st.write(
    "MAAIF agricultural input and veterinary quality standards apply. Disease quarantine alerts "
    "must be acted on and suspected outbreaks reported to the relevant veterinary authority."
)

st.header("MTIC")
st.write(
    "Produce must be traded using exact weights or units such as UGX per kg or UGX per bunch. "
    "Primary cooperative societies follow the Cooperative Societies Act (Cap 112), democratic member "
    "control and a minimum 30 members, subject to current DCO certification requirements."
)

st.header("Uganda ICT and operating-law rules")
st.write(
    "PDPO Uganda: explicit consent for NIN, DOB, phone and farm/GPS records, encryption at rest, "
    "right to export or delete data and applicable Data Protection Office registration compliance."
)
st.write(
    "Computer Misuse Act, 2011 (as amended): unauthorized access, account sharing, electronic fraud "
    "and tampering with market or logistics records are prohibited."
)
st.write(
    "Electronic Transactions Act, 2011 and Electronic Signatures Act, 2011: digital marketplace contracts, "
    "e-receipts and timestamped delivery confirmations are legally relevant where applicable."
)
st.write(
    "Copyright and Neighbouring Rights Act, 2006 and NITA-U Act, 2009: Harvesta software/UI copyright "
    "and user-uploaded media rights are protected."
)

st.header("Required Ugandan Sector Licenses")
for item in [
    "KCCA or Local Government Trading License",
    "PDPO Data Collector/Controller Certificate",
    "NDA licensed veterinary pharmacy linkage",
    "URA TIN and EFRIS e-invoicing compliance",
    "Ministry of Works & Transport goods-in-transit compliance",
    "URA goods-in-transit and commercial driver compliance",
]:
    st.checkbox(item, key=f"license_{item}")

st.markdown("---")
st.caption("\u00a9 2026 Harvesta. All rights reserved.")
