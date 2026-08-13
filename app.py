import streamlit as st
import requests
from supabase import create_client


# ============================================================
# CONFIG
# ============================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

SCHEDULE_API = (
    "https://ptosr.pelindo.co.id/"
    "ScheduleBoard/GetData"
    "?kd_cabang=61&kd_terminal=601"
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Manual RORO",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION
# ============================================================

defaults = {
    "access_token": None,
    "refresh_token": None,
    "profile": None,
    "schedule_data": [],
    "selected_vessel": None,
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    .main-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .sub-title {
        color: #6b7280;
        font-size: 15px;
        margin-bottom: 25px;
    }

    .vessel-card {
        padding: 20px;
        border-radius: 14px;
        background: #f7f8fa;
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
    }

    .vessel-name {
        font-size: 25px;
        font-weight: 700;
    }

    .vessel-info {
        color: #555;
        font-size: 14px;
        line-height: 1.8;
    }

    .section-title {
        font-size: 18px;
        font-weight: 650;
        margin-top: 15px;
        margin-bottom: 8px;
    }

    .bruto-box {
        padding: 12px;
        border-radius: 10px;
        background: #f7f8fa;
        border: 1px solid #e5e7eb;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOGIN
# ============================================================

def login(email, password):

    try:

        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not response.session:
            return False, "Session login tidak ditemukan."

        st.session_state.access_token = (
            response.session.access_token
        )

        st.session_state.refresh_token = (
            response.session.refresh_token
        )

        profile_response = supabase.rpc(
            "get_my_profile"
        ).execute()

        if not profile_response.data:

            supabase.auth.sign_out()

            return (
                False,
                "Profile user tidak ditemukan."
            )

        profile = profile_response.data[0]

        if profile["status"] != "ACTIVE":

            supabase.auth.sign_out()

            return (
                False,
                "Akun tidak aktif."
            )

        st.session_state.profile = profile

        return True, "Login berhasil."

    except Exception as e:

        return False, str(e)


# ============================================================
# LOGOUT
# ============================================================

def logout():

    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.clear()

    st.rerun()


# ============================================================
# GET API
# ============================================================

def get_schedule():

    try:

        response = requests.get(
            SCHEDULE_API,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            return data, None

        if isinstance(data, dict):

            if "data" in data:
                return data["data"], None

            if "Data" in data:
                return data["Data"], None

            if "NAMA_KAPAL" in data:
                return [data], None

        return [], "Format response API tidak dikenali."

    except requests.exceptions.Timeout:

        return [], "API timeout."

    except requests.exceptions.RequestException as e:

        return [], f"API tidak dapat diakses: {e}"

    except Exception as e:

        return [], str(e)


# ============================================================
# LOAD API
# ============================================================

def refresh_schedule():

    with st.spinner("Mengambil kegiatan kapal..."):

        data, error = get_schedule()

    if error:

        st.session_state.schedule_data = []

        return False, error

    st.session_state.schedule_data = data

    return True, f"{len(data)} kegiatan kapal tersedia."


# ============================================================
# LOGIN SCREEN
# ============================================================

if st.session_state.profile is None:

    st.markdown(
        '<div class="main-title">⚓ Manual RORO</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Sistem Input Kendaraan Pelabuhan'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns([1, 1.4, 1])

    with col2:

        st.subheader("Login Administrator")

        email = st.text_input(
            "Email"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Masuk",
            type="primary",
            use_container_width=True
        ):

            if not email or not password:

                st.error(
                    "Email dan password wajib diisi."
                )

            else:

                with st.spinner("Login..."):

                    success, message = login(
                        email,
                        password
                    )

                if success:

                    st.rerun()

                else:

                    st.error(message)

    st.stop()


# ============================================================
# PROFILE
# ============================================================

profile = st.session_state.profile


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## ⚓ Manual RORO"
    )

    st.caption(
        "Vehicle Entry System"
    )

    st.divider()

    st.write(
        f"**{profile['name']}**"
    )

    st.caption(
        f"NIPP: {profile['nipp']}"
    )

    st.caption(
        f"Role: {profile['role_code']}"
    )

    st.divider()

    menu = st.radio(
        "MENU",
        [
            "🏠 Dashboard",
            "🚢 Kegiatan Kapal",
            "🚛 Input Kendaraan",
            "🖨️ Reprint",
            "📊 Laporan"
        ]
    )

    st.divider()

    if st.button(
        "Keluar",
        use_container_width=True
    ):

        logout()


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">'
        'Dashboard'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Selamat datang di Manual RORO'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Kegiatan Kapal",
            len(
                st.session_state.schedule_data
            )
        )

    with col2:

        st.metric(
            "User",
            1
        )

    with col3:

        st.metric(
            "Status",
            "ONLINE"
        )

    st.divider()

    st.info(
        "Gunakan menu **Kegiatan Kapal** untuk "
        "memuat jadwal kapal dari ScheduleBoard."
    )


# ============================================================
# KEGIATAN KAPAL
# ============================================================

elif menu == "🚢 Kegiatan Kapal":

    st.markdown(
        '<div class="main-title">'
        'Kegiatan Kapal'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Jadwal kapal dari ScheduleBoard'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🔄 Refresh Data",
        type="primary"
    ):

        success, message = refresh_schedule()

        if success:
            st.success(message)
        else:
            st.error(message)

    st.divider()

    if st.session_state.schedule_data:

        display_data = []

        for item in st.session_state.schedule_data:

            display_data.append({

                "Kapal":
                    item.get("NAMA_KAPAL", "-"),

                "Voyage":
                    item.get("VOYAGE_NO", "-"),

                "Rute":
                    (
                        f"{item.get('NM_PORT_ASAL', '-')}"
                        " → "
                        f"{item.get('NM_PORT_DEST', '-')}"
                    ),

                "Dermaga":
                    item.get("NM_DERMAGA", "-"),

                "ETA":
                    item.get("ETA", "-"),

                "ETD":
                    item.get("ETD", "-"),

                "Status":
                    item.get("VESOPS_STATUS", "-")
            })

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Belum ada data. "
            "Klik Refresh Data."
        )

    st.divider()

    st.subheader(
        "Input Kapal Manual"
    )

    st.caption(
        "Gunakan hanya jika data kapal dari API "
        "tidak tersedia."
    )

    with st.expander(
        "Buka Input Manual"
    ):

        manual_name = st.text_input(
            "Nama Kapal"
        )

        manual_voyage = st.text_input(
            "Voyage"
        )

        manual_origin = st.text_input(
            "Pelabuhan Asal"
        )

        manual_destination = st.text_input(
            "Pelabuhan Tujuan"
        )

        manual_berth = st.text_input(
            "Dermaga"
        )

        if st.button(
            "Gunakan Kapal Manual"
        ):

            if not manual_name:

                st.error(
                    "Nama kapal wajib diisi."
                )

            else:

                st.session_state.selected_vessel = {

                    "NAMA_KAPAL":
                        manual_name,

                    "VOYAGE_NO":
                        manual_voyage,

                    "NM_PORT_ASAL":
                        manual_origin,

                    "NM_PORT_DEST":
                        manual_destination,

                    "NM_DERMAGA":
                        manual_berth,

                    "SOURCE":
                        "MANUAL"
                }

                st.success(
                    f"{manual_name} dipilih."
                )


# ============================================================
# INPUT KENDARAAN
# ============================================================

elif menu == "🚛 Input Kendaraan":

    st.markdown(
        '<div class="main-title">'
        'Input Kendaraan'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Input kendaraan masuk pelabuhan'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # SELECT VESSEL
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '1. Kegiatan Kapal'
        '</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.schedule_data:

        success, message = refresh_schedule()

        if not success:

            st.error(message)

    if st.session_state.schedule_data:

        vessel_options = []

        for item in st.session_state.schedule_data:

            label = (
                f"{item.get('NAMA_KAPAL', '-')}"
                f" | {item.get('VOYAGE_NO', '-')}"
                f" | {item.get('NM_DERMAGA', '-')}"
            )

            vessel_options.append(
                (label, item)
            )

        labels = [
            x[0]
            for x in vessel_options
        ]

        selected_label = st.selectbox(
            "Pilih kegiatan kapal",
            labels
        )

        selected_vessel = next(
            item
            for label, item in vessel_options
            if label == selected_label
        )

        st.session_state.selected_vessel = (
            selected_vessel
        )

    # --------------------------------------------------------
    # VESSEL CARD
    # --------------------------------------------------------

    vessel = st.session_state.selected_vessel

    if vessel:

        st.markdown(
            f"""
            <div class="vessel-card">

            <div class="vessel-name">
            🚢 {vessel.get("NAMA_KAPAL", "-")}
            </div>

            <div class="vessel-info">

            <b>Voyage:</b>
            {vessel.get("VOYAGE_NO", "-")}
            <br>

            <b>Rute:</b>
            {vessel.get("NM_PORT_ASAL", "-")}
            →
            {vessel.get("NM_PORT_DEST", "-")}
            <br>

            <b>Dermaga:</b>
            {vessel.get("NM_DERMAGA", "-")}
            <br>

            <b>ETA:</b>
            {vessel.get("ETA", "-")}
            &nbsp;&nbsp;
            <b>ETD:</b>
            {vessel.get("ETD", "-")}

            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # --------------------------------------------------------
    # QR
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '2. QR Tiket'
        '</div>',
        unsafe_allow_html=True
    )

    qr_ticket = st.text_input(
        "Scan QR Tiket",
        placeholder="Scan menggunakan QR scanner..."
    )

    st.divider()

    # --------------------------------------------------------
    # VEHICLE GROUP
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '3. Golongan Kendaraan'
        '</div>',
        unsafe_allow_html=True
    )

    vehicle_group = st.selectbox(
        "Pilih golongan",
        [
            "Golongan 1",
            "Golongan 2",
            "Golongan 3",
            "Golongan 4",
            "Golongan 5",
            "Golongan 6"
        ]
    )

    st.divider()

    # --------------------------------------------------------
    # BRUTO
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '4. Berat Bruto'
        '</div>',
        unsafe_allow_html=True
    )

    bruto = st.number_input(
        "Bruto (Kg)",
        min_value=0.0,
        step=10.0,
        format="%.2f"
    )

    st.caption(
        "Berat yang dicatat adalah berat BRUTO."
    )

    st.divider()

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Ringkasan'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            "**Kapal**"
        )

        st.write(
            vessel.get("NAMA_KAPAL", "-")
            if vessel else "-"
        )

        st.write(
            "**Golongan**"
        )

        st.write(
            vehicle_group
        )

    with col2:

        st.write(
            "**QR Tiket**"
        )

        st.write(
            qr_ticket or "-"
        )

        st.write(
            "**Bruto**"
        )

        st.write(
            f"{bruto:,.2f} Kg"
        )

    st.divider()

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    if st.button(
        "💾 SIMPAN TRANSAKSI",
        type="primary",
        use_container_width=True
    ):

        errors = []

        if not vessel:

            errors.append(
                "Kegiatan kapal belum dipilih."
            )

        if not qr_ticket:

            errors.append(
                "QR tiket belum diisi."
            )

        if bruto <= 0:

            errors.append(
                "Berat bruto harus lebih dari 0."
            )

        if errors:

            for error in errors:
                st.error(error)

        else:

            st.success(
                "Data valid."
            )

            st.info(
                "Penyimpanan transaksi akan "
                "diaktifkan setelah tabel "
                "weighing_transactions dibuat."
            )


# ============================================================
# REPRINT
# ============================================================

elif menu == "🖨️ Reprint":

    st.markdown(
        '<div class="main-title">'
        'Reprint'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Cetak ulang tiket kendaraan'
        '</div>',
        unsafe_allow_html=True
    )

    qr = st.text_input(
        "QR Tiket"
    )

    if st.button(
        "Cari Transaksi",
        type="primary"
    ):

        if not qr:

            st.error(
                "Masukkan QR tiket."
            )

        else:

            st.info(
                "Fitur reprint akan aktif "
                "setelah database transaksi dibuat."
            )


# ============================================================
# LAPORAN
# ============================================================

elif menu == "📊 Laporan":

    st.markdown(
        '<div class="main-title">'
        'Laporan'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Log data timbangan'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.date_input(
            "Tanggal Mulai"
        )

    with col2:

        st.date_input(
            "Tanggal Akhir"
        )

    st.info(
        "Laporan akan dapat difilter berdasarkan "
        "tanggal dan kegiatan kapal."
    )
