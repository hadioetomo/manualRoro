import streamlit as st
import requests
from datetime import datetime, date, time, timezone
from supabase import create_client


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Manual RORO",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# SESSION STATE
# ============================================================

DEFAULT_SESSION = {
    "profile": None,
    "selected_vessel": None,
    "schedule_loaded": False,
    "last_transaction": None,
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    .main-title {
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .sub-title {
        color: #6b7280;
        font-size: 14px;
        margin-bottom: 20px;
    }

    .vessel-card {
        padding: 20px;
        border-radius: 14px;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        margin: 10px 0 20px 0;
    }

    .vessel-name {
        font-size: 25px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .vessel-info {
        color: #4b5563;
        line-height: 1.8;
    }

    .transaction-success {
        padding: 22px;
        border-radius: 14px;
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        margin-top: 20px;
    }

    .transaction-number {
        font-size: 28px;
        font-weight: 700;
    }

    .small-label {
        color: #6b7280;
        font-size: 13px;
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

        # ----------------------------------------------------
        # Ambil profile user
        # ----------------------------------------------------

        profile_response = supabase.rpc(
            "get_my_profile"
        ).execute()

        if not profile_response.data:

            supabase.auth.sign_out()

            return False, "Profile user tidak ditemukan."

        profile = profile_response.data[0]

        if profile.get("status") != "ACTIVE":

            supabase.auth.sign_out()

            return False, "Akun tidak aktif."

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
# API - GET SCHEDULE
# ============================================================

def get_schedule_from_api():

    try:

        response = requests.get(
            SCHEDULE_API,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        # ----------------------------------------------------
        # API langsung array
        # ----------------------------------------------------

        if isinstance(data, list):
            return data, None

        # ----------------------------------------------------
        # API menggunakan data/Data
        # ----------------------------------------------------

        if isinstance(data, dict):

            if isinstance(data.get("data"), list):
                return data["data"], None

            if isinstance(data.get("Data"), list):
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
# DATE PARSER
# ============================================================

def parse_api_datetime(value):

    if not value:
        return None

    if isinstance(value, datetime):
        return value

    formats = [
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                str(value),
                fmt
            ).replace(
                tzinfo=timezone.utc
            )

        except ValueError:
            continue

    return None


# ============================================================
# BOOLEAN PARSER
# ============================================================

def parse_bool(value):

    if value is None:
        return None

    if str(value) in ["1", "true", "TRUE", "True"]:
        return True

    if str(value) in ["0", "false", "FALSE", "False"]:
        return False

    return None


# ============================================================
# CONVERT API RECORD
# ============================================================

def convert_schedule_record(item):

    return {

        "voyage_no":
            item.get("VOYAGE_NO"),

        "kd_jadwal":
            item.get("KD_JADWAL"),

        "kd_kapal":
            item.get("KD_KAPAL"),

        "nama_kapal":
            item.get("NAMA_KAPAL"),

        "kd_operator":
            item.get("KD_OPERATOR"),

        "nm_operator":
            item.get("NM_OPERATOR"),

        "kd_operator_sap":
            item.get("KD_OPERATOR_SAP"),

        "kd_port_asal":
            item.get("KD_PORT_ASAL"),

        "nm_port_asal":
            item.get("NM_PORT_ASAL"),

        "kd_port_prev":
            item.get("KD_PORT_PREV"),

        "nm_port_prev":
            item.get("NM_PORT_PREV"),

        "kd_port_next":
            item.get("KD_PORT_NEXT"),

        "nm_port_next":
            item.get("NM_PORT_NEXT"),

        "kd_port_dest":
            item.get("KD_PORT_DEST"),

        "nm_port_dest":
            item.get("NM_PORT_DEST"),

        "kd_dermaga":
            item.get("KD_DERMAGA"),

        "nm_dermaga":
            item.get("NM_DERMAGA"),

        "kade_awal":
            item.get("KADE_AWAL"),

        "kade_akhir":
            item.get("KADE_AKHIR"),

        "no_gate":
            item.get("NO_GATE"),

        "eta":
            parse_api_datetime(item.get("ETA")),

        "et_berthing":
            parse_api_datetime(item.get("ET_BERTHING")),

        "et_boarding":
            parse_api_datetime(item.get("ET_BOARDING")),

        "etd":
            parse_api_datetime(item.get("ETD")),

        "open_date":
            parse_api_datetime(item.get("OPEN_DATE")),

        "closing_date":
            parse_api_datetime(item.get("CLOSING_DATE")),

        "is_open_checkin":
            parse_bool(item.get("IS_OPEN_CHECKIN")),

        "is_open_gate":
            parse_bool(item.get("IS_OPEN_GATE")),

        "first_line":
            parse_api_datetime(item.get("FIRST_LINE")),

        "at_start_act":
            parse_api_datetime(item.get("AT_START_ACT")),

        "at_start_debarkasi":
            parse_api_datetime(
                item.get("AT_START_DEBARKASI")
            ),

        "at_end_debarkasi":
            parse_api_datetime(
                item.get("AT_END_DEBARKASI")
            ),

        "at_start_embarkasi":
            parse_api_datetime(
                item.get("AT_START_EMBARKASI")
            ),

        "at_end_embarkasi":
            parse_api_datetime(
                item.get("AT_END_EMBARKASI")
            ),

        "at_end_act":
            parse_api_datetime(item.get("AT_END_ACT")),

        "last_line":
            parse_api_datetime(item.get("LAST_LINE")),

        "ves_stat":
            item.get("VES_STAT"),

        "rec_stat":
            item.get("REC_STAT"),

        "status_kirim_manifest":
            item.get("STATUS_KIRIM_MANIFEST"),

        "sts_go":
            item.get("STS_GO"),

        "vesops_status":
            item.get("VESOPS_STATUS"),

        "onschedule_status":
            item.get("ONSCHEDULE_STATUS"),

        "no_pkk":
            item.get("NO_PKK"),

        "source":
            "API",

        "raw_data":
            item,

        "api_created_date":
            parse_api_datetime(item.get("CREATED_DATE")),

        "api_created_by":
            item.get("CREATED_BY"),

        "api_last_updated_date":
            parse_api_datetime(
                item.get("LAST_UPDATED_DATE")
            ),

        "api_last_updated_by":
            item.get("LAST_UPDATED_BY"),

        "program_name":
            item.get("PROGRAM_NAME")
    }


# ============================================================
# UPSERT SCHEDULE
# ============================================================

def save_schedule_to_supabase(api_data):

    saved = 0
    errors = []

    for item in api_data:

        record = convert_schedule_record(item)

        # ----------------------------------------------------
        # Data minimal
        # ----------------------------------------------------

        if not record["nama_kapal"]:
            continue

        try:

            # ------------------------------------------------
            # Gunakan KD_JADWAL sebagai identitas jika ada
            # ------------------------------------------------

            existing = None

            if record["kd_jadwal"]:

                result = (
                    supabase
                    .table("schedule_voyages")
                    .select("id")
                    .eq(
                        "kd_jadwal",
                        record["kd_jadwal"]
                    )
                    .limit(1)
                    .execute()
                )

                if result.data:
                    existing = result.data[0]

            # ------------------------------------------------
            # Update
            # ------------------------------------------------

            if existing:

                (
                    supabase
                    .table("schedule_voyages")
                    .update(record)
                    .eq(
                        "id",
                        existing["id"]
                    )
                    .execute()
                )

            # ------------------------------------------------
            # Insert
            # ------------------------------------------------

            else:

                (
                    supabase
                    .table("schedule_voyages")
                    .insert(record)
                    .execute()
                )

            saved += 1

        except Exception as e:

            errors.append(
                f"{record['nama_kapal']}: {str(e)}"
            )

    return saved, errors


# ============================================================
# LOAD SCHEDULE DATABASE
# ============================================================

def get_schedule_database():

    try:

        result = (
            supabase
            .table("schedule_voyages")
            .select("*")
            .order(
                "eta",
                desc=False
            )
            .limit(200)
            .execute()
        )

        return result.data or [], None

    except Exception as e:

        return [], str(e)


# ============================================================
# GET TRANSACTION NUMBER
# ============================================================

def generate_transaction_number():

    result = supabase.rpc(
        "generate_transaction_no"
    ).execute()

    if result.data:
        return result.data

    raise Exception(
        "Gagal membuat nomor transaksi."
    )


# ============================================================
# CHECK DUPLICATE QR
# ============================================================

def check_duplicate_qr(
    schedule_id,
    qr_ticket
):

    result = (
        supabase
        .table("weighing_transactions")
        .select(
            "id, transaction_no, status"
        )
        .eq(
            "schedule_voyage_id",
            schedule_id
        )
        .eq(
            "qr_ticket",
            qr_ticket
        )
        .eq(
            "status",
            "COMPLETED"
        )
        .limit(1)
        .execute()
    )

    return result.data or []


# ============================================================
# SAVE WEIGHING TRANSACTION
# ============================================================

def save_transaction(
    vessel,
    qr_ticket,
    vehicle_group,
    bruto,
    profile
):

    try:

        schedule_id = vessel["id"]

        # ----------------------------------------------------
        # Duplicate QR
        # ----------------------------------------------------

        duplicate = check_duplicate_qr(
            schedule_id,
            qr_ticket
        )

        if duplicate:

            return (
                False,
                "QR tiket sudah digunakan pada "
                "kegiatan kapal ini.",
                None
            )

        # ----------------------------------------------------
        # Transaction number
        # ----------------------------------------------------

        transaction_no = (
            generate_transaction_number()
        )

        # ----------------------------------------------------
        # Source
        # ----------------------------------------------------

        transaction_source = (
            "MANUAL"
            if vessel.get("source") == "MANUAL"
            else "API"
        )

        # ----------------------------------------------------
        # Data transaction
        # ----------------------------------------------------

        record = {

            "transaction_no":
                transaction_no,

            "qr_ticket":
                qr_ticket.strip(),

            "schedule_voyage_id":
                schedule_id,

            "vehicle_group":
                vehicle_group,

            "bruto_kg":
                float(bruto),

            "destination_berth_code":
                vessel.get("kd_dermaga"),

            "destination_berth_name":
                vessel.get("nm_dermaga"),

            "operator_user_id":
                profile["id"],

            "transaction_source":
                transaction_source,

            "status":
                "COMPLETED",

            "transaction_time":
                datetime.now(
                    timezone.utc
                ).isoformat()
        }

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        result = (
            supabase
            .table("weighing_transactions")
            .insert(record)
            .execute()
        )

        if not result.data:

            return (
                False,
                "Transaksi gagal disimpan.",
                None
            )

        return (
            True,
            "Transaksi berhasil disimpan.",
            result.data[0]
        )

    except Exception as e:

        return (
            False,
            str(e),
            None
        )


# ============================================================
# LOGIN SCREEN
# ============================================================

if st.session_state.profile is None:

    st.markdown(
        '<div class="main-title">'
        '⚓ Manual RORO'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Sistem Input Kendaraan Pelabuhan'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns(
        [1, 1.4, 1]
    )

    with col2:

        st.subheader(
            "Login"
        )

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

                with st.spinner(
                    "Login..."
                ):

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
        f"**{profile.get('name', '-') }**"
    )

    st.caption(
        f"NIPP: {profile.get('nipp', '-')}"
    )

    st.caption(
        f"Role: {profile.get('role_code', '-')}"
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
        'Monitoring Manual RORO'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Get transaction statistics
    # --------------------------------------------------------

    try:

        transaction_result = (
            supabase
            .table("weighing_transactions")
            .select(
                "id, bruto_kg, status"
            )
            .eq(
                "status",
                "COMPLETED"
            )
            .execute()
        )

        transactions = (
            transaction_result.data or []
        )

    except Exception:

        transactions = []

    total_transactions = len(
        transactions
    )

    total_bruto = sum(
        float(x["bruto_kg"])
        for x in transactions
    )

    schedule_data, schedule_error = (
        get_schedule_database()
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Kegiatan Kapal",
            len(schedule_data)
        )

    with col2:

        st.metric(
            "Total Transaksi",
            total_transactions
        )

    with col3:

        st.metric(
            "Total Bruto",
            f"{total_bruto:,.0f} Kg"
        )

    st.divider()

    st.info(
        "Gunakan **Input Kendaraan** untuk "
        "mencatat kendaraan masuk pelabuhan."
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
        'Data kapal dari ScheduleBoard'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(
        [1, 3]
    )

    with col1:

        refresh = st.button(
            "🔄 Sinkronisasi API",
            type="primary",
            use_container_width=True
        )

    if refresh:

        with st.spinner(
            "Mengambil data ScheduleBoard..."
        ):

            api_data, api_error = (
                get_schedule_from_api()
            )

        if api_error:

            st.error(api_error)

        else:

            with st.spinner(
                "Menyimpan ke Supabase..."
            ):

                saved, errors = (
                    save_schedule_to_supabase(
                        api_data
                    )
                )

            st.success(
                f"{saved} kegiatan kapal "
                f"berhasil disinkronkan."
            )

            if errors:

                with st.expander(
                    "Lihat error"
                ):

                    for error in errors:

                        st.write(
                            error
                        )

    st.divider()

    schedule_data, error = (
        get_schedule_database()
    )

    if error:

        st.error(error)

    elif not schedule_data:

        st.info(
            "Belum ada data kegiatan kapal."
        )

    else:

        for vessel in schedule_data:

            with st.container(
                border=True
            ):

                col1, col2, col3 = st.columns(
                    [2, 2, 1]
                )

                with col1:

                    st.markdown(
                        f"### 🚢 "
                        f"{vessel.get('nama_kapal', '-')}"
                    )

                    st.caption(
                        f"Voyage: "
                        f"{vessel.get('voyage_no', '-')}"
                    )

                with col2:

                    st.write(
                        f"**Rute:** "
                        f"{vessel.get('nm_port_asal', '-')}"
                        f" → "
                        f"{vessel.get('nm_port_dest', '-')}"
                    )

                    st.write(
                        f"**Dermaga:** "
                        f"{vessel.get('nm_dermaga', '-')}"
                    )

                with col3:

                    st.write(
                        f"**Source:** "
                        f"{vessel.get('source', '-')}"
                    )

                    st.write(
                        f"**Status:** "
                        f"{vessel.get('vesops_status', '-')}"
                    )


    st.divider()

    st.subheader(
        "⚠️ Input Kapal Manual"
    )

    st.caption(
        "Gunakan apabila data kapal dari API "
        "tidak tersedia."
    )

    with st.expander(
        "Tambah Kegiatan Kapal Manual"
    ):

        manual_name = st.text_input(
            "Nama Kapal",
            key="manual_name"
        )

        manual_voyage = st.text_input(
            "Voyage",
            key="manual_voyage"
        )

        manual_origin = st.text_input(
            "Pelabuhan Asal",
            key="manual_origin"
        )

        manual_destination = st.text_input(
            "Pelabuhan Tujuan",
            key="manual_destination"
        )

        manual_berth = st.text_input(
            "Dermaga",
            key="manual_berth"
        )

        if st.button(
            "Simpan Kapal Manual",
            type="primary"
        ):

            if not manual_name:

                st.error(
                    "Nama kapal wajib diisi."
                )

            else:

                try:

                    manual_record = {

                        "nama_kapal":
                            manual_name,

                        "voyage_no":
                            manual_voyage,

                        "nm_port_asal":
                            manual_origin,

                        "nm_port_dest":
                            manual_destination,

                        "nm_dermaga":
                            manual_berth,

                        "source":
                            "MANUAL",

                        "raw_data":
                            None
                    }

                    result = (
                        supabase
                        .table(
                            "schedule_voyages"
                        )
                        .insert(
                            manual_record
                        )
                        .execute()
                    )

                    if result.data:

                        st.success(
                            "Kapal manual berhasil "
                            "disimpan."
                        )

                        st.rerun()

                except Exception as e:

                    st.error(
                        f"Gagal menyimpan: {e}"
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
        'Pencatatan kendaraan masuk pelabuhan'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # LOAD VESSELS
    # --------------------------------------------------------

    schedule_data, error = (
        get_schedule_database()
    )

    if error:

        st.error(error)
        st.stop()

    if not schedule_data:

        st.warning(
            "Belum ada kegiatan kapal."
        )

        st.info(
            "Buka menu Kegiatan Kapal "
            "kemudian klik Sinkronisasi API."
        )

        st.stop()

    # --------------------------------------------------------
    # SELECT VESSEL
    # --------------------------------------------------------

    st.markdown(
        "### 1️⃣ Kegiatan Kapal"
    )

    vessel_map = {}

    for vessel in schedule_data:

        label = (
            f"{vessel.get('nama_kapal', '-')}"
            f" | "
            f"{vessel.get('voyage_no', '-')}"
            f" | "
            f"{vessel.get('nm_dermaga', '-')}"
        )

        vessel_map[label] = vessel

    selected_label = st.selectbox(
        "Pilih kegiatan kapal",
        list(vessel_map.keys())
    )

    vessel = vessel_map[
        selected_label
    ]

    # --------------------------------------------------------
    # VESSEL CARD
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="vessel-card">

        <div class="vessel-name">
        🚢 {vessel.get("nama_kapal", "-")}
        </div>

        <div class="vessel-info">

        <b>Voyage:</b>
        {vessel.get("voyage_no", "-")}

        <br>

        <b>Rute:</b>
        {vessel.get("nm_port_asal", "-")}
        →
        {vessel.get("nm_port_dest", "-")}

        <br>

        <b>Dermaga:</b>
        {vessel.get("nm_dermaga", "-")}

        <br>

        <b>ETA:</b>
        {vessel.get("eta", "-")}

        &nbsp;&nbsp;

        <b>ETD:</b>
        {vessel.get("etd", "-")}

        <br>

        <b>Source:</b>
        {vessel.get("source", "-")}

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # QR
    # --------------------------------------------------------

    st.markdown(
        "### 2️⃣ QR Tiket"
    )

    qr_ticket = st.text_input(
        "Scan QR tiket",
        placeholder=(
            "Arahkan scanner QR ke kolom ini..."
        ),
        key="qr_ticket"
    )

    # --------------------------------------------------------
    # VEHICLE GROUP
    # --------------------------------------------------------

    st.markdown(
        "### 3️⃣ Golongan Kendaraan"
    )

    vehicle_group = st.radio(
        "Pilih golongan",
        [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6"
        ],
        horizontal=True
    )

    # --------------------------------------------------------
    # BRUTO
    # --------------------------------------------------------

    st.markdown(
        "### 4️⃣ Berat Bruto"
    )

    bruto = st.number_input(
        "Bruto (Kg)",
        min_value=0.0,
        step=10.0,
        format="%.2f",
        key="bruto"
    )

    st.caption(
        "Masukkan berat bruto hasil timbangan."
    )

    st.divider()

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    st.markdown(
        "### Ringkasan Transaksi"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.write(
            "**Kapal**"
        )

        st.write(
            vessel.get(
                "nama_kapal",
                "-"
            )
        )

    with col2:

        st.write(
            "**Golongan**"
        )

        st.write(
            f"Golongan {vehicle_group}"
        )

    with col3:

        st.write(
            "**Bruto**"
        )

        st.write(
            f"{bruto:,.2f} Kg"
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    if st.button(
        "💾 SIMPAN TRANSAKSI",
        type="primary",
        use_container_width=True
    ):

        errors = []

        if not qr_ticket.strip():

            errors.append(
                "QR tiket wajib diisi."
            )

        if bruto <= 0:

            errors.append(
                "Berat bruto harus lebih dari 0 Kg."
            )

        if not vessel.get("id"):

            errors.append(
                "ID kegiatan kapal tidak ditemukan."
            )

        if errors:

            for error in errors:

                st.error(error)

        else:

            with st.spinner(
                "Menyimpan transaksi..."
            ):

                success, message, transaction = (
                    save_transaction(
                        vessel,
                        qr_ticket,
                        vehicle_group,
                        bruto,
                        profile
                    )
                )

            if success:

                st.session_state.last_transaction = (
                    transaction
                )

                st.success(
                    "Transaksi berhasil disimpan."
                )

                st.markdown(
                    f"""
                    <div class="transaction-success">

                    <div class="small-label">
                    NOMOR TRANSAKSI
                    </div>

                    <div class="transaction-number">
                    {transaction["transaction_no"]}
                    </div>

                    <br>

                    <b>Kapal:</b>
                    {vessel.get("nama_kapal", "-")}

                    <br>

                    <b>Golongan:</b>
                    {vehicle_group}

                    <br>

                    <b>Bruto:</b>
                    {bruto:,.2f} Kg

                    <br>

                    <b>Dermaga:</b>
                    {vessel.get("nm_dermaga", "-")}

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.error(message)


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
        'Cari transaksi berdasarkan QR atau '
        'nomor transaksi'
        '</div>',
        unsafe_allow_html=True
    )

    search = st.text_input(
        "QR Tiket / Nomor Transaksi"
    )

    if st.button(
        "🔎 Cari",
        type="primary"
    ):

        if not search.strip():

            st.warning(
                "Masukkan QR tiket atau "
                "nomor transaksi."
            )

        else:

            try:

                result = (
                    supabase
                    .table(
                        "weighing_transactions"
                    )
                    .select(
                        """
                        *,
                        schedule_voyages(
                            nama_kapal,
                            voyage_no,
                            nm_port_asal,
                            nm_port_dest,
                            nm_dermaga
                        )
                        """
                    )
                    .or_(
                        f"qr_ticket.eq.{search},"
                        f"transaction_no.eq.{search}"
                    )
                    .limit(1)
                    .execute()
                )

                if not result.data:

                    st.warning(
                        "Transaksi tidak ditemukan."
                    )

                else:

                    trx = result.data[0]

                    vessel = trx.get(
                        "schedule_voyages"
                    ) or {}

                    st.success(
                        "Transaksi ditemukan."
                    )

                    st.write(
                        f"**Nomor:** "
                        f"{trx.get('transaction_no')}"
                    )

                    st.write(
                        f"**QR:** "
                        f"{trx.get('qr_ticket')}"
                    )

                    st.write(
                        f"**Kapal:** "
                        f"{vessel.get('nama_kapal', '-')}"
                    )

                    st.write(
                        f"**Voyage:** "
                        f"{vessel.get('voyage_no', '-')}"
                    )

                    st.write(
                        f"**Golongan:** "
                        f"{trx.get('vehicle_group')}"
                    )

                    st.write(
                        f"**Bruto:** "
                        f"{float(trx.get('bruto_kg', 0)):,.2f} Kg"
                    )

                    st.write(
                        f"**Dermaga:** "
                        f"{trx.get('destination_berth_name', '-')}"
                    )

                    st.write(
                        f"**Waktu:** "
                        f"{trx.get('transaction_time', '-')}"
                    )

                    st.divider()

                    st.info(
                        "Tombol cetak tiket akan "
                        "ditambahkan pada tahap Reprint."
                    )

            except Exception as e:

                st.error(
                    f"Gagal mencari transaksi: {e}"
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

        start_date = st.date_input(
            "Tanggal Mulai",
            value=date.today()
        )

    with col2:

        end_date = st.date_input(
            "Tanggal Akhir",
            value=date.today()
        )

    if start_date > end_date:

        st.error(
            "Tanggal mulai tidak boleh "
            "lebih besar dari tanggal akhir."
        )

        st.stop()

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    try:

        start_datetime = datetime.combine(
            start_date,
            time.min
        ).replace(
            tzinfo=timezone.utc
        )

        end_datetime = datetime.combine(
            end_date,
            time.max
        ).replace(
            tzinfo=timezone.utc
        )

        result = (
            supabase
            .table(
                "weighing_transactions"
            )
            .select(
                """
                *,
                schedule_voyages(
                    nama_kapal,
                    voyage_no,
                    nm_dermaga
                )
                """
            )
            .gte(
                "transaction_time",
                start_datetime.isoformat()
            )
            .lte(
                "transaction_time",
                end_datetime.isoformat()
            )
            .eq(
                "status",
                "COMPLETED"
            )
            .order(
                "transaction_time",
                desc=True
            )
            .execute()
        )

        data = result.data or []

    except Exception as e:

        st.error(
            f"Gagal mengambil laporan: {e}"
        )

        data = []

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    st.write(
        f"**{len(data)} transaksi ditemukan.**"
    )

    if data:

        rows = []

        for trx in data:

            vessel = (
                trx.get("schedule_voyages")
                or {}
            )

            rows.append({

                "Nomor Transaksi":
                    trx.get(
                        "transaction_no",
                        "-"
                    ),

                "QR Tiket":
                    trx.get(
                        "qr_ticket",
                        "-"
                    ),

                "Kapal":
                    vessel.get(
                        "nama_kapal",
                        "-"
                    ),

                "Voyage":
                    vessel.get(
                        "voyage_no",
                        "-"
                    ),

                "Golongan":
                    trx.get(
                        "vehicle_group",
                        "-"
                    ),

                "Bruto Kg":
                    trx.get(
                        "bruto_kg",
                        0
                    ),

                "Dermaga":
                    trx.get(
                        "destination_berth_name",
                        "-"
                    ),

                "Waktu":
                    trx.get(
                        "transaction_time",
                        "-"
                    ),

                "Source":
                    trx.get(
                        "transaction_source",
                        "-"
                    )
            })

        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # CSV
        # ----------------------------------------------------

        import pandas as pd

        df = pd.DataFrame(rows)

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download CSV",
            data=csv,
            file_name=(
                f"laporan_roro_"
                f"{start_date}_"
                f"{end_date}.csv"
            ),
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info(
            "Tidak ada transaksi pada periode tersebut."
        )
