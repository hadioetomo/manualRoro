import streamlit as st
import requests
from datetime import datetime
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


# API SCHEDULEBOARD
SCHEDULE_API = (
    "https://ptosr.pelindo.co.id/"
    "ScheduleBoard/GetData"
    "?kd_cabang=61&kd_terminal=601"
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Manual RORO",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None

if "profile" not in st.session_state:
    st.session_state.profile = None

if "schedule_data" not in st.session_state:
    st.session_state.schedule_data = []

if "selected_vessel" not in st.session_state:
    st.session_state.selected_vessel = None

if "manual_mode" not in st.session_state:
    st.session_state.manual_mode = False


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

        # Ambil profile
        profile_response = supabase.rpc(
            "get_my_profile"
        ).execute()

        if not profile_response.data:

            supabase.auth.sign_out()

            return (
                False,
                "User berhasil login tetapi "
                "profile tidak ditemukan."
            )

        profile = profile_response.data[0]

        # Cek status
        if profile["status"] != "ACTIVE":

            supabase.auth.sign_out()

            return (
                False,
                "Akun tidak aktif. "
                "Hubungi Administrator."
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

    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.profile = None

    st.rerun()


# ============================================================
# API - GET SCHEDULE
# ============================================================

def get_schedule():

    try:

        response = requests.get(
            SCHEDULE_API,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        # API bisa mengembalikan list langsung
        if isinstance(data, list):
            return data, None

        # Beberapa API membungkus data
        if isinstance(data, dict):

            if "data" in data:
                return data["data"], None

            if "Data" in data:
                return data["Data"], None

            # Jika response hanya satu object
            if "NAMA_KAPAL" in data:
                return [data], None

        return [], "Format response API tidak dikenali."

    except requests.exceptions.Timeout:

        return [], "API timeout."

    except requests.exceptions.RequestException as e:

        return [], f"API tidak dapat diakses: {str(e)}"

    except ValueError:

        return [], "Response API bukan JSON yang valid."

    except Exception as e:

        return [], str(e)


# ============================================================
# LOAD SCHEDULE
# ============================================================

def load_schedule():

    with st.spinner(
        "Mengambil jadwal kapal dari API..."
    ):

        data, error = get_schedule()

    if error:

        st.session_state.schedule_data = []

        return False, error

    st.session_state.schedule_data = data

    return True, f"{len(data)} jadwal ditemukan."


# ============================================================
# VEHICLE GROUP
# ============================================================

# Untuk sementara hanya kode golongan.
# Deskripsi dapat kita sesuaikan dengan ketentuan
# operasional/terminal yang digunakan.

VEHICLE_GROUPS = {
    "1": "Golongan 1",
    "2": "Golongan 2",
    "3": "Golongan 3",
    "4": "Golongan 4",
    "5": "Golongan 5",
    "6": "Golongan 6",
}


# ============================================================
# DEFAULT VEHICLE TYPES
# ============================================================

# Ini sementara.
# Nanti dipindahkan ke tabel master_vehicle_types
# sehingga Admin dapat menambah/mengubahnya.

DEFAULT_VEHICLE_TYPES = {

    "1": [
        "Sepeda"
    ],

    "2": [
        "Sepeda Motor"
    ],

    "3": [
        "Kendaraan Roda 3",
        "Kendaraan Roda 4"
    ],

    "4": [
        "Mobil Penumpang",
        "Pickup"
    ],

    "5": [
        "Truk",
        "Bus"
    ],

    "6": [
        "Truk Besar",
        "Trailer"
    ]
}


# ============================================================
# FORMAT DATE
# ============================================================

def format_datetime(value):

    if not value:
        return "-"

    return str(value).replace("/", "-")


# ============================================================
# LOGIN PAGE
# ============================================================

if st.session_state.profile is None:

    st.title("⚓ Manual RORO")

    st.subheader(
        "Sistem Input Manual Kendaraan Masuk Pelabuhan"
    )

    st.caption(
        "Pelindo Sub Regional Jawa"
    )

    st.divider()

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        st.markdown(
            "### 🔐 Login Administrator"
        )

        email = st.text_input(
            "Email",
            placeholder="Email Admin"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Password"
        )

        login_button = st.button(
            "LOGIN",
            type="primary",
            use_container_width=True
        )

        if login_button:

            if not email or not password:

                st.error(
                    "Email dan password wajib diisi."
                )

            else:

                with st.spinner(
                    "Memproses login..."
                ):

                    success, message = login(
                        email,
                        password
                    )

                if success:

                    st.success(message)

                    st.rerun()

                else:

                    st.error(message)

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

profile = st.session_state.profile

with st.sidebar:

    st.title("⚓ Manual RORO")

    st.caption(
        "Vehicle Entry & Weighing System"
    )

    st.divider()

    st.write("**LOGIN USER**")

    st.write(
        profile["name"]
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
            "🚢 Jadwal Kapal",
            "🚛 Input Kendaraan",
            "🖨️ Reprint",
            "📊 Laporan",
        ]
    )

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.title(
        "🏠 Dashboard Admin"
    )

    st.write(
        f"Selamat datang, **{profile['name']}**."
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Role",
            profile["role_code"]
        )

    with col2:

        st.metric(
            "Status",
            profile["status"]
        )

    with col3:

        st.metric(
            "Jadwal Kapal",
            len(
                st.session_state.schedule_data
            )
        )

    with col4:

        st.metric(
            "Mode",
            "API"
        )

    st.divider()

    st.subheader(
        "Jadwal Kapal"
    )

    if not st.session_state.schedule_data:

        st.info(
            "Belum ada data jadwal. "
            "Silakan buka menu Jadwal Kapal."
        )

    else:

        st.dataframe(
            st.session_state.schedule_data,
            use_container_width=True
        )


# ============================================================
# JADWAL KAPAL
# ============================================================

elif menu == "🚢 Jadwal Kapal":

    st.title(
        "🚢 Jadwal Kapal"
    )

    st.write(
        "Sumber data:"
    )

    st.code(
        SCHEDULE_API
    )

    col1, col2 = st.columns(
        [1, 5]
    )

    with col1:

        if st.button(
            "🔄 Refresh API",
            type="primary"
        ):

            success, message = load_schedule()

            if success:
                st.success(message)
            else:
                st.error(message)

    with col2:

        if st.session_state.schedule_data:

            st.success(
                f"{len(st.session_state.schedule_data)} "
                "data jadwal tersedia."
            )

    st.divider()

    # --------------------------------------------------------
    # API DATA
    # --------------------------------------------------------

    if st.session_state.schedule_data:

        display_data = []

        for item in st.session_state.schedule_data:

            display_data.append({

                "Kapal":
                    item.get("NAMA_KAPAL", "-"),

                "Voyage":
                    item.get("VOYAGE_NO", "-"),

                "Operator":
                    item.get("NM_OPERATOR", "-"),

                "Asal":
                    item.get("NM_PORT_ASAL", "-"),

                "Tujuan":
                    item.get("NM_PORT_DEST", "-"),

                "Dermaga":
                    item.get("NM_DERMAGA", "-"),

                "ETA":
                    format_datetime(
                        item.get("ETA")
                    ),

                "ETD":
                    format_datetime(
                        item.get("ETD")
                    ),

                "Status":
                    item.get("VESOPS_STATUS", "-"),

                "Gate":
                    item.get("NO_GATE", "-"),

            })

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "Data API belum tersedia."
        )

    st.divider()

    # --------------------------------------------------------
    # MANUAL FALLBACK
    # --------------------------------------------------------

    st.subheader(
        "🛠️ Manual Fallback"
    )

    st.write(
        "Digunakan apabila API ScheduleBoard "
        "mengalami gangguan atau data kapal "
        "belum tersedia."
    )

    manual = st.checkbox(
        "Gunakan Input Kapal Manual"
    )

    if manual:

        manual_vessel = st.text_input(
            "Nama Kapal Manual"
        )

        manual_voyage = st.text_input(
            "Nomor Voyage Manual"
        )

        manual_origin = st.text_input(
            "Pelabuhan Asal"
        )

        manual_destination = st.text_input(
            "Pelabuhan Tujuan"
        )

        manual_berth = st.text_input(
            "Dermaga Tujuan"
        )

        manual_eta = st.text_input(
            "ETA",
            placeholder="YYYY-MM-DD HH:MM"
        )

        manual_etd = st.text_input(
            "ETD",
            placeholder="YYYY-MM-DD HH:MM"
        )

        if st.button(
            "Gunakan Data Kapal Manual",
            type="primary"
        ):

            if not manual_vessel:

                st.error(
                    "Nama kapal wajib diisi."
                )

            else:

                st.session_state.selected_vessel = {

                    "NAMA_KAPAL":
                        manual_vessel,

                    "VOYAGE_NO":
                        manual_voyage,

                    "NM_PORT_ASAL":
                        manual_origin,

                    "NM_PORT_DEST":
                        manual_destination,

                    "NM_DERMAGA":
                        manual_berth,

                    "ETA":
                        manual_eta,

                    "ETD":
                        manual_etd,

                    "SOURCE":
                        "MANUAL"

                }

                st.success(
                    f"Kapal {manual_vessel} "
                    "dipilih sebagai fallback manual."
                )


# ============================================================
# INPUT KENDARAAN
# ============================================================

elif menu == "🚛 Input Kendaraan":

    st.title(
        "🚛 Input Kendaraan Masuk Pelabuhan"
    )

    st.caption(
        "Input berat hanya menggunakan BRUTO."
    )

    st.divider()

    # --------------------------------------------------------
    # KAPAL
    # --------------------------------------------------------

    st.subheader(
        "1. Kegiatan Kapal"
    )

    # Jika belum ada data API
    if not st.session_state.schedule_data:

        st.warning(
            "Belum ada jadwal kapal dari API."
        )

        if st.button(
            "🔄 Ambil Jadwal Kapal"
        ):

            success, message = load_schedule()

            if success:

                st.success(message)

                st.rerun()

            else:

                st.error(message)

    else:

        vessel_options = []

        for item in st.session_state.schedule_data:

            vessel_name = item.get(
                "NAMA_KAPAL",
                "-"
            )

            voyage = item.get(
                "VOYAGE_NO",
                "-"
            )

            berth = item.get(
                "NM_DERMAGA",
                "-"
            )

            label = (
                f"{vessel_name} | "
                f"Voyage {voyage} | "
                f"{berth}"
            )

            vessel_options.append(
                (label, item)
            )

        vessel_labels = [
            item[0]
            for item in vessel_options
        ]

        selected_label = st.selectbox(
            "Pilih Kegiatan Kapal",
            vessel_labels
        )

        selected_item = next(
            item
            for label, item in vessel_options
            if label == selected_label
        )

        st.session_state.selected_vessel = (
            selected_item
        )

    # --------------------------------------------------------
    # DISPLAY VESSEL
    # --------------------------------------------------------

    if st.session_state.selected_vessel:

        vessel = (
            st.session_state.selected_vessel
        )

        st.info(
            f"🚢 **{vessel.get('NAMA_KAPAL', '-') }**  \n"
            f"Voyage: `{vessel.get('VOYAGE_NO', '-')}`  \n"
            f"Operator: `{vessel.get('NM_OPERATOR', '-')}`  \n"
            f"Rute: `{vessel.get('NM_PORT_ASAL', '-')}` → "
            f"`{vessel.get('NM_PORT_DEST', '-')}`  \n"
            f"Dermaga: `{vessel.get('NM_DERMAGA', '-')}`"
        )

    st.divider()

    # --------------------------------------------------------
    # QR TICKET
    # --------------------------------------------------------

    st.subheader(
        "2. Tiket Kendaraan"
    )

    qr_ticket = st.text_input(
        "Scan / Masukkan QR Code Tiket",
        placeholder="Scan QR menggunakan scanner..."
    )

    st.caption(
        "QR scanner USB biasanya akan terbaca "
        "sebagai input keyboard."
    )

    st.divider()

    # --------------------------------------------------------
    # VEHICLE
    # --------------------------------------------------------

    st.subheader(
        "3. Jenis Kendaraan"
    )

    col1, col2 = st.columns(2)

    with col1:

        group = st.selectbox(
            "Golongan Kendaraan",
            list(VEHICLE_GROUPS.keys()),
            format_func=lambda x:
                VEHICLE_GROUPS[x]
        )

    with col2:

        vehicle_types = (
            DEFAULT_VEHICLE_TYPES.get(
                group,
                []
            )
        )

        vehicle_type = st.selectbox(
            "Jenis Kendaraan",
            vehicle_types
        )

    st.divider()

    # --------------------------------------------------------
    # BRUTO
    # --------------------------------------------------------

    st.subheader(
        "4. Berat Kendaraan"
    )

    bruto = st.number_input(
        "BRUTO (Kg)",
        min_value=0.0,
        step=10.0,
        format="%.2f"
    )

    st.caption(
        "Sistem ini hanya mencatat berat BRUTO."
    )

    st.divider()

    # --------------------------------------------------------
    # DERMAGA
    # --------------------------------------------------------

    st.subheader(
        "5. Dermaga Tujuan"
    )

    if st.session_state.selected_vessel:

        vessel_berth = (
            st.session_state.selected_vessel
            .get("NM_DERMAGA")
        )

    else:

        vessel_berth = None

    destination_berth = st.text_input(
        "Nama Dermaga Tujuan",
        value=vessel_berth or ""
    )

    st.divider()

    # --------------------------------------------------------
    # PREVIEW
    # --------------------------------------------------------

    st.subheader(
        "6. Preview Transaksi"
    )

    preview_col1, preview_col2 = st.columns(2)

    with preview_col1:

        st.write(
            "**Kapal:**",
            (
                st.session_state.selected_vessel
                .get("NAMA_KAPAL", "-")
                if st.session_state.selected_vessel
                else "-"
            )
        )

        st.write(
            "**Voyage:**",
            (
                st.session_state.selected_vessel
                .get("VOYAGE_NO", "-")
                if st.session_state.selected_vessel
                else "-"
            )
        )

        st.write(
            "**Golongan:**",
            VEHICLE_GROUPS[group]
        )

        st.write(
            "**Jenis:**",
            vehicle_type
        )

    with preview_col2:

        st.write(
            "**QR Ticket:**",
            qr_ticket or "-"
        )

        st.write(
            "**Bruto:**",
            f"{bruto:,.2f} Kg"
        )

        st.write(
            "**Dermaga:**",
            destination_berth or "-"
        )

        st.write(
            "**Operator Input:**",
            profile["nipp"]
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

        if not st.session_state.selected_vessel:
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

        if not destination_berth:
            errors.append(
                "Dermaga tujuan belum diisi."
            )

        if errors:

            for error in errors:
                st.error(error)

        else:

            st.warning(
                "Form sudah valid, tetapi tabel "
                "transaksi Supabase belum kita aktifkan."
            )

            st.info(
                "Tahap berikutnya adalah membuat "
                "tabel weighing_transactions sebelum "
                "data benar-benar disimpan."
            )


# ============================================================
# REPRINT
# ============================================================

elif menu == "🖨️ Reprint":

    st.title(
        "🖨️ Reprint Tiket"
    )

    st.info(
        "Modul reprint akan menggunakan "
        "QR tiket sebagai pencarian transaksi."
    )

    qr_search = st.text_input(
        "QR Ticket"
    )

    if st.button(
        "CARI TRANSAKSI"
    ):

        if not qr_search:

            st.error(
                "Masukkan QR ticket."
            )

        else:

            st.warning(
                "Tabel transaksi belum dibuat."
            )


# ============================================================
# LAPORAN
# ============================================================

elif menu == "📊 Laporan":

    st.title(
        "📊 Laporan Timbangan"
    )

    st.write(
        "Filter laporan akan tersedia setelah "
        "tabel transaksi dibuat."
    )

    col1, col2 = st.columns(2)

    with col1:

        tanggal_awal = st.date_input(
            "Tanggal Awal"
        )

    with col2:

        tanggal_akhir = st.date_input(
            "Tanggal Akhir"
        )

    st.info(
        "Nanti laporan dapat difilter berdasarkan "
        "tanggal, nama kapal/kegiatan, golongan, "
        "jenis kendaraan dan operator."
    )
