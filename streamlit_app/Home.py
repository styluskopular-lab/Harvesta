import streamlit as st
import httpx
import sys
from pathlib import Path
import re
from datetime import date

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from streamlit_app.api_config import api_post, sidebar_api_url
except ImportError:
    from api_config import api_post, sidebar_api_url

st.set_page_config(
    page_title="Harvesta",
    page_icon=str(Path(__file__).parents[1] / "harvesta_icon.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

# Shared visual system
css_path = Path(__file__).with_name("styles.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

API_URL = sidebar_api_url()

# Session state
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "rules_accepted" not in st.session_state:
    st.session_state.rules_accepted = False

def api_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def login(email: str, password: str):
    try:
        r = api_post(
            f"{API_URL}/auth/login/json",
            json={"email": email, "password": password},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            st.session_state.token = data["access_token"]
            st.session_state.authenticated = True
            # Fetch user
            me = httpx.get(f"{API_URL}/auth/me", headers=api_headers(), timeout=10)
            if me.status_code == 200:
                user = me.json()
                st.session_state.user = user
                st.session_state.authenticated = True
                st.session_state.rules_accepted = bool(user.get("privacy_consent", False))
                return True
            st.session_state.token = None
            st.session_state.authenticated = False
            st.error("Signed in, but your account could not be loaded. Please try again.")
            return False
        else:
            st.error(r.json().get("detail", "Login failed"))
            return False
    except Exception as e:
        st.error(f"Connection error: {e}")
        return False


def backend_error_message(response):
    try:
        payload = response.json()
    except Exception:
        return f"Registration failed ({response.status_code}). Please try again."

    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        messages = []
        for item in detail:
            message = item.get("msg") if isinstance(item, dict) else str(item)
            location = item.get("loc", []) if isinstance(item, dict) else []
            field = str(location[-1]).replace("_", " ").title() if location else ""
            messages.append(f"{field}: {message}" if field else str(message))
        return "\n".join(messages)
    return f"Registration failed ({response.status_code}). Please check the form."


def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.authenticated = False
    st.session_state.rules_accepted = False
    st.rerun()


# Sidebar
with st.sidebar:
    st.markdown("# Harvesta")
    st.caption("Uganda-grown. Uganda-built.")

    if st.session_state.user:
        st.success(f"Logged in as **{st.session_state.user['full_name']}**")
        st.write(f"Role: `{st.session_state.user['role']}`")
        if st.button("Logout"):
            logout()
    else:
        auth_tab, register_tab = st.tabs(["Sign in", "Create account"])
        with auth_tab:
            email = st.text_input("Gmail or phone", value="buyer@harvesta.ug", key="login_email")
            password = st.text_input("Password", type="password", value="buyer123", key="login_password")
            if st.button("Sign In", use_container_width=True, key="login_button"):
                if login(email, password):
                    st.switch_page("pages/6_Dashboard.py")
        with register_tab:
            with st.form("create_account_form", clear_on_submit=False):
                full_name = st.text_input("Full name", key="register_name")
                country_codes = [
                    ("Uganda (+256)", "+256"),
                    ("Afghanistan (+93)", "+93"), ("Albania (+355)", "+355"),
                    ("Algeria (+213)", "+213"), ("Andorra (+376)", "+376"),
                    ("Angola (+244)", "+244"), ("Argentina (+54)", "+54"),
                    ("Armenia (+374)", "+374"), ("Australia (+61)", "+61"),
                    ("Austria (+43)", "+43"), ("Azerbaijan (+994)", "+994"),
                    ("Bahamas (+1242)", "+1242"), ("Bahrain (+973)", "+973"),
                    ("Bangladesh (+880)", "+880"), ("Barbados (+1246)", "+1246"),
                    ("Belarus (+375)", "+375"), ("Belgium (+32)", "+32"),
                    ("Belize (+501)", "+501"), ("Benin (+229)", "+229"),
                    ("Bhutan (+975)", "+975"), ("Bolivia (+591)", "+591"),
                    ("Bosnia and Herzegovina (+387)", "+387"), ("Botswana (+267)", "+267"),
                    ("Brazil (+55)", "+55"), ("Brunei (+673)", "+673"),
                    ("Bulgaria (+359)", "+359"), ("Burkina Faso (+226)", "+226"),
                    ("Burundi (+257)", "+257"), ("Cambodia (+855)", "+855"),
                    ("Cameroon (+237)", "+237"), ("Canada (+1)", "+1"),
                    ("Central African Republic (+236)", "+236"), ("Chad (+235)", "+235"),
                    ("Chile (+56)", "+56"), ("China (+86)", "+86"),
                    ("Colombia (+57)", "+57"), ("Comoros (+269)", "+269"),
                    ("Congo (+242)", "+242"), ("Costa Rica (+506)", "+506"),
                    ("Cote d'Ivoire (+225)", "+225"), ("Croatia (+385)", "+385"),
                    ("Cuba (+53)", "+53"), ("Cyprus (+357)", "+357"),
                    ("Czechia (+420)", "+420"), ("DR Congo (+243)", "+243"),
                    ("Denmark (+45)", "+45"), ("Djibouti (+253)", "+253"),
                    ("Dominican Republic (+1809)", "+1809"), ("Ecuador (+593)", "+593"),
                    ("Egypt (+20)", "+20"), ("El Salvador (+503)", "+503"),
                    ("Eritrea (+291)", "+291"), ("Estonia (+372)", "+372"),
                    ("Eswatini (+268)", "+268"), ("Ethiopia (+251)", "+251"),
                    ("Fiji (+679)", "+679"), ("Finland (+358)", "+358"),
                    ("France (+33)", "+33"), ("Gabon (+241)", "+241"),
                    ("Gambia (+220)", "+220"), ("Georgia (+995)", "+995"),
                    ("Germany (+49)", "+49"), ("Ghana (+233)", "+233"),
                    ("Greece (+30)", "+30"), ("Guatemala (+502)", "+502"),
                    ("Guinea (+224)", "+224"), ("Guyana (+592)", "+592"),
                    ("Haiti (+509)", "+509"), ("Honduras (+504)", "+504"),
                    ("Hong Kong (+852)", "+852"), ("Hungary (+36)", "+36"),
                    ("Iceland (+354)", "+354"), ("India (+91)", "+91"),
                    ("Indonesia (+62)", "+62"), ("Iran (+98)", "+98"),
                    ("Iraq (+964)", "+964"), ("Ireland (+353)", "+353"),
                    ("Israel (+972)", "+972"), ("Italy (+39)", "+39"),
                    ("Jamaica (+1876)", "+1876"), ("Japan (+81)", "+81"),
                    ("Jordan (+962)", "+962"), ("Kazakhstan (+7)", "+7"),
                    ("Kenya (+254)", "+254"), ("Kosovo (+383)", "+383"),
                    ("Kuwait (+965)", "+965"), ("Kyrgyzstan (+996)", "+996"),
                    ("Laos (+856)", "+856"), ("Latvia (+371)", "+371"),
                    ("Lebanon (+961)", "+961"), ("Lesotho (+266)", "+266"),
                    ("Liberia (+231)", "+231"), ("Libya (+218)", "+218"),
                    ("Lithuania (+370)", "+370"), ("Luxembourg (+352)", "+352"),
                    ("Madagascar (+261)", "+261"), ("Malawi (+265)", "+265"),
                    ("Malaysia (+60)", "+60"), ("Maldives (+960)", "+960"),
                    ("Mali (+223)", "+223"), ("Malta (+356)", "+356"),
                    ("Mauritania (+222)", "+222"), ("Mauritius (+230)", "+230"),
                    ("Mexico (+52)", "+52"), ("Moldova (+373)", "+373"),
                    ("Monaco (+377)", "+377"), ("Mongolia (+976)", "+976"),
                    ("Montenegro (+382)", "+382"), ("Morocco (+212)", "+212"),
                    ("Mozambique (+258)", "+258"), ("Myanmar (+95)", "+95"),
                    ("Namibia (+264)", "+264"), ("Nepal (+977)", "+977"),
                    ("Netherlands (+31)", "+31"), ("New Zealand (+64)", "+64"),
                    ("Nicaragua (+505)", "+505"), ("Niger (+227)", "+227"),
                    ("Nigeria (+234)", "+234"), ("North Korea (+850)", "+850"),
                    ("North Macedonia (+389)", "+389"), ("Norway (+47)", "+47"),
                    ("Oman (+968)", "+968"), ("Pakistan (+92)", "+92"),
                    ("Palestine (+970)", "+970"), ("Panama (+507)", "+507"),
                    ("Papua New Guinea (+675)", "+675"), ("Paraguay (+595)", "+595"),
                    ("Peru (+51)", "+51"), ("Philippines (+63)", "+63"),
                    ("Poland (+48)", "+48"), ("Portugal (+351)", "+351"),
                    ("Qatar (+974)", "+974"), ("Romania (+40)", "+40"),
                    ("Russia (+7)", "+7"), ("Rwanda (+250)", "+250"),
                    ("Saudi Arabia (+966)", "+966"), ("Senegal (+221)", "+221"),
                    ("Serbia (+381)", "+381"), ("Seychelles (+248)", "+248"),
                    ("Sierra Leone (+232)", "+232"), ("Singapore (+65)", "+65"),
                    ("Slovakia (+421)", "+421"), ("Slovenia (+386)", "+386"),
                    ("Somalia (+252)", "+252"), ("South Africa (+27)", "+27"),
                    ("South Korea (+82)", "+82"), ("South Sudan (+211)", "+211"),
                    ("Spain (+34)", "+34"), ("Sri Lanka (+94)", "+94"),
                    ("Sudan (+249)", "+249"), ("Suriname (+597)", "+597"),
                    ("Sweden (+46)", "+46"), ("Switzerland (+41)", "+41"),
                    ("Syria (+963)", "+963"), ("Taiwan (+886)", "+886"),
                    ("Tajikistan (+992)", "+992"), ("Tanzania (+255)", "+255"),
                    ("Thailand (+66)", "+66"), ("Togo (+228)", "+228"),
                    ("Trinidad and Tobago (+1868)", "+1868"), ("Tunisia (+216)", "+216"),
                    ("Turkey (+90)", "+90"), ("Uganda (+256)", "+256"),
                    ("Ukraine (+380)", "+380"), ("United Arab Emirates (+971)", "+971"),
                    ("United Kingdom (+44)", "+44"), ("United States (+1)", "+1"),
                    ("Uruguay (+598)", "+598"), ("Uzbekistan (+998)", "+998"),
                    ("Vanuatu (+678)", "+678"), ("Venezuela (+58)", "+58"),
                    ("Vietnam (+84)", "+84"), ("Yemen (+967)", "+967"),
                    ("Zambia (+260)", "+260"), ("Zimbabwe (+263)", "+263"),
                ]
                country_label = st.selectbox(
                    "Country code",
                    country_codes,
                    index=0,
                    format_func=lambda item: item[0],
                    key="register_country_code",
                )
                local_phone = st.text_input(
                    "Local phone number",
                    placeholder="700000000",
                    key="register_phone",
                )
                reg_email = st.text_input("Gmail address", placeholder="name@gmail.com", key="register_email")
                notification_label = st.selectbox(
                    "Preferred notifications",
                    ["Email", "SMS", "Email and SMS"],
                    key="register_notification_preference",
                    help="Notifications are recorded in Harvesta until provider credentials are configured.",
                )
                nin = st.text_input("Ugandan National Identification Number (NIN)", placeholder="CM123456789012", key="register_nin")
                dob = st.date_input("Date of Birth", value=date(2000, 1, 1), key="register_dob")
                district = st.text_input("District", placeholder="Mukono", key="register_district")
                subcounty = st.text_input("Sub-county / Parish (Optional)", placeholder="Mukono Central", key="register_subcounty")
                village = st.text_input("Village", placeholder="Ntawo", key="register_village")
                location_name = f"{district.strip()}, {subcounty.strip()}, {village.strip()}".strip(", ")
                next_of_kin_name = st.text_input("Next of Kin Name", key="register_kin_name")
                next_of_kin_contact = st.text_input("Next of Kin Contact", placeholder="+256700000000", key="register_kin_contact")
                reg_password = st.text_input("Password", type="password", key="register_password")
                role_label = st.selectbox(
                    "Role",
                    ["Farmer", "Driver / Transporter", "Buyer"],
                    key="register_role",
                )
                role = {"Farmer": "farmer", "Driver / Transporter": "driver", "Buyer": "buyer"}[role_label]
                primary_farm_enterprise = None
                farm_size_acres = None
                dfa_cooperative_id = None
                driving_permit_number = None
                driving_permit_class = None
                vehicle_type = None
                vehicle_plate = None
                goods_insurance_status = None
                if role == "farmer":
                    primary_farm_enterprise = st.selectbox(
                        "Primary Farm Enterprise",
                        ["Crops", "Livestock", "Mixed"],
                        key="register_farm_enterprise",
                    )
                    farm_acres_text = st.text_input(
                        "Farm Size (Acres, Optional)",
                        placeholder="Leave blank if unknown",
                        key="register_farm_acres",
                    )
                    try:
                        farm_size_acres = float(farm_acres_text) if farm_acres_text.strip() else None
                    except ValueError:
                        farm_size_acres = -1
                    dfa_cooperative_id = st.text_input(
                        "UNFFE District Farmer Association / Cooperative Society Membership ID (Optional)",
                        key="register_dfa_id",
                    )
                if role == "driver":
                    driving_permit_number = st.text_input("Uganda Driving Permit Number", key="register_permit_number")
                    driving_permit_class = st.text_input("Driving Permit Class", placeholder="B, C1, CM, C, D", key="register_permit_class")
                    vehicle_type = st.selectbox(
                        "Vehicle Type",
                        ["Boda Boda", "Pickup/Van", "Lorry/Truck"],
                        key="register_vehicle_type",
                    )
                    vehicle_plate = st.text_input("Vehicle Registration Plate", placeholder="UBX 123A", key="register_vehicle_plate")
                    goods_insurance_status = st.selectbox(
                        "PSV / Goods-in-Transit Insurance Status",
                        ["Active", "Pending", "Not applicable", "Expired"],
                        key="register_insurance",
                    )
                st.markdown(
                    '<div style="background:#E5E7EB;border:2px solid #000000;border-radius:12px;padding:16px;color:#000000;font-size:16px;">'
                    '<strong>General Rules, Uganda PDPO Privacy Policy &amp; UNFFE/NARO/MAAIF/MTIC Guidelines</strong><br>'
                    'By continuing, you agree to lawful use, privacy protection, accurate farm records, '
                    'UNFFE farmer organization structures, NARO research/IP attribution, MAAIF standards and MTIC trading rules.'
                    '</div>',
                    unsafe_allow_html=True,
                )
                consent = st.checkbox(
                    "I accept the General Rules, Uganda PDPO Privacy Policy & UNFFE/NARO/MAAIF/MTIC Guidelines.",
                    key="register_consent",
                )
                st.page_link("pages/8_Privacy.py", label="Read Privacy Policy and Terms of Use")
                submitted = st.form_submit_button("Create account", use_container_width=True)

            if submitted:
                errors = []
                phone = f"{country_label[1]}{re.sub(r'\\D', '', local_phone)}"
                if len(full_name.strip()) < 2:
                    errors.append("Enter your full name.")
                nin_normalized = nin.strip().upper()
                if not re.fullmatch(r"(CM|CF)[A-Z0-9]{12}", nin_normalized):
                    errors.append("NIN must be 14 characters and begin with CM or CF.")
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                if age < 18:
                    errors.append("You must be at least 18 years old.")
                if not re.fullmatch(r"[0-9]{6,14}", re.sub(r"\D", "", local_phone)):
                    errors.append("Enter a valid local phone number.")
                if not re.fullmatch(r"[A-Za-z0-9._%+-]+@gmail\.com", reg_email.strip(), re.IGNORECASE):
                    errors.append("Enter a valid Gmail address.")
                if len(district.strip()) < 2 or len(village.strip()) < 2:
                    errors.append("Enter district and village.")
                if len(next_of_kin_name.strip()) < 2 or len(next_of_kin_contact.strip()) < 6:
                    errors.append("Enter Next of Kin name and contact.")
                if len(reg_password) < 6:
                    errors.append("Password must contain at least 6 characters.")
                if not consent:
                    errors.append("Consent to the Privacy Policy and Terms of Use is required.")
                if role == "farmer" and farm_size_acres == -1:
                    errors.append("Farm size must be a number in acres or left blank.")
                if role == "driver" and any(not value for value in [
                    driving_permit_number,
                    driving_permit_class,
                    vehicle_type,
                    vehicle_plate,
                    goods_insurance_status,
                ]):
                    errors.append("Complete all driver permit, vehicle and insurance fields.")

                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    try:
                        response = api_post(
                            f"{API_URL}/auth/register",
                            json={
                                "email": reg_email.strip().lower(),
                                "full_name": full_name,
                                "phone": phone or None,
                                "location_name": location_name or None,
                                "role": role,
                                "notification_preference": {
                                    "Email": "email",
                                    "SMS": "sms",
                                    "Email and SMS": "both",
                                }[notification_label],
                                "password": reg_password,
                                "privacy_consent": consent,
                                "nin": nin_normalized,
                                "date_of_birth": str(dob),
                                "district": district,
                                "subcounty": subcounty,
                                "village": village,
                                "next_of_kin_name": next_of_kin_name,
                                "next_of_kin_contact": next_of_kin_contact,
                                "primary_farm_enterprise": primary_farm_enterprise,
                                "farm_size_acres": farm_size_acres,
                                "dfa_cooperative_id": dfa_cooperative_id or None,
                                "driving_permit_number": driving_permit_number,
                                "driving_permit_class": driving_permit_class,
                                "vehicle_type": vehicle_type,
                                "vehicle_plate": vehicle_plate,
                                "goods_insurance_status": goods_insurance_status,
                            },
                            timeout=10,
                        )
                        if response.status_code == 201:
                            account = response.json()
                            st.session_state.token = account["access_token"]
                            st.session_state.user = {
                                "id": account["id"],
                                "email": account["email"],
                                "full_name": account["full_name"],
                                "phone": account.get("phone"),
                                "role": account["role"],
                                "notification_preference": account.get("notification_preference", "email"),
                                "location_name": account.get("location_name"),
                                "district": account.get("district"),
                                "subcounty": account.get("subcounty"),
                                "village": account.get("village"),
                                "is_active": account["is_active"],
                                "created_at": account["created_at"],
                                "privacy_consent": True,
                            }
                            st.session_state.authenticated = True
                            st.session_state.rules_accepted = True
                            st.toast("Account created!")
                            st.switch_page("pages/6_Dashboard.py")
                        else:
                            st.error(backend_error_message(response))
                    except Exception as e:
                        st.error(f"Connection error: {e}")

    st.divider()
    st.markdown("### Demo accounts")
    st.caption("Buyer: buyer@harvesta.ug")
    st.caption("Password: buyer123")

# Main content
st.markdown("""
<section class="harvesta-hero">
  <span class="eyebrow">Buy Uganda · Build Uganda</span>
  <h1>Good food begins in Uganda.</h1>
  <p>Connect with Ugandan farmers, shop locally made produce and follow every delivery.</p>
</section>
""", unsafe_allow_html=True)

st.markdown('<div class="stat-grid">', unsafe_allow_html=True)
st.markdown("""
<div class="stat-grid">
  <div class="stat-card"><strong>Uganda</strong><span>Local products</span></div>
  <div class="stat-card"><strong>Fresh</strong><span>Harvested locally</span></div>
  <div class="stat-card"><strong>Direct</strong><span>Farmer to family</span></div>
</div>
</div>
""", unsafe_allow_html=True)

st.markdown("## One platform. Every step.")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="feature-card"><div class="icon">Grow</div><h3>Grow</h3><p>Farmers manage farms, harvest dates and live product listings.</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="feature-card"><div class="icon">Shop</div><h3>Shop</h3><p>Buy fresh, seasonal produce directly from trusted local farms.</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="feature-card"><div class="icon">Deliver</div><h3>Deliver</h3><p>Track every order from pickup to its final doorstep.</p></div>', unsafe_allow_html=True)

if st.session_state.user:
    role = st.session_state.user["role"]
    st.success(f"Welcome back, {st.session_state.user['full_name']}! Role: {role.replace('_', ' ').title()}")
else:
    st.info("Sign in from the menu to browse, place orders and manage your farm.")

st.markdown("---")
st.caption("\u00a9 2026 Harvesta. All rights reserved.")
