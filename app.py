import streamlit as st
import requests
import pandas as pd

from datetime import datetime, date, time, timezone
from supabase import create_client
from streamlit_autorefresh import st_autorefresh


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

AUTO_SYNC_MINUTES = 10
AUTO_REFRESH_MS = AUTO_SYNC_MINUTES * 60 * 1000


# ============================================================
# AUTO REFRESH
# ============================================================

st_autorefresh(
    interval=AUTO_REFRESH_MS,
    key="roro_auto_refresh"
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {

    "profile": None,

    "initial_sync_done": False,

    "last_sync_time": None,

    "last_sync_result": None,

    "notification": None,

    "selected_vessel": None,

    "last_transaction": None
}

for key, value in DEFAULT_STATE.items():

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
        max-width: 1250px;
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

    .sync-card {
        padding: 18px;
        border-radius: 14px;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
    }

    .new-vessel {
        padding: 15px;
        border-radius: 12px;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        margin-bottom: 10px;
    }

    .changed-vessel {
        padding: 15px;
        border-radius: 12px;
        background: #fff7ed;
        border: 1px solid #fed7aa;
        margin-bottom: 10px;
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
# JSON SAFE
# ============================================================

def json_safe(value):

    """
    Mengubah datetime/date/dict/list menjadi
    object yang aman dikirim ke Supabase JSON.
    """

    if isinstance(value, datetime):

        return value.isoformat()

    if isinstance(value, date):

        return value.isoformat()

    if isinstance(value, dict):

        return {
            key: json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, list):

        return [
            json_safe(item)
            for item in value
        ]

    return value


# ============================================================
# PARSE DATETIME
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

        "%Y-%m-%d %H:%M:%S",

        "%Y-%m-%dT%H:%M:%S",

        "%Y-%m-%dT%H:%M:%S.%f"
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
# BOOLEAN
# ============================================================

def parse_bool(value):

    if value is None:

        return None

    if str(value).lower() in [
        "1",
        "true"
    ]:

        return True

    if str(value).lower() in [
        "0",
        "false"
    ]:

        return False

    return None


# ============================================================
# API GET
# ============================================================

def get_schedule_from_api():

    try:

        response = requests.get(
            SCHEDULE_API,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        # API berupa array

        if isinstance(data, list):

            return data, None

        # API berupa object

        if isinstance(data, dict):

            if isinstance(
                data.get("data"),
                list
            ):

                return data["data"], None

            if isinstance(
                data.get("Data"),
                list
            ):

                return data["Data"], None

            if "NAMA_KAPAL" in data:

                return [data], None

        return [], (
            "Format response API tidak dikenali."
        )

    except requests.exceptions.Timeout:

        return [], "API timeout."

    except requests.exceptions.RequestException as e:

        return [], (
            f"API tidak dapat diakses: {e}"
        )

    except Exception as e:

        return [], str(e)


# ============================================================
# CONVERT API RECORD
# ============================================================

def convert_schedule_record(item):

    record = {

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
            parse_api_datetime(
                item.get("ETA")
            ),

        "et_berthing":
            parse_api_datetime(
                item.get("ET_BERTHING")
            ),

        "et_boarding":
            parse_api_datetime(
                item.get("ET_BOARDING")
            ),

        "etd":
            parse_api_datetime(
                item.get("ETD")
            ),

        "open_date":
            parse_api_datetime(
                item.get("OPEN_DATE")
            ),

        "closing_date":
            parse_api_datetime(
                item.get("CLOSING_DATE")
            ),

        "is_open_checkin":
            parse_bool(
                item.get("IS_OPEN_CHECKIN")
            ),

        "is_open_gate":
            parse_bool(
                item.get("IS_OPEN_GATE")
            ),

        "first_line":
            parse_api_datetime(
                item.get("FIRST_LINE")
            ),

        "at_start_act":
            parse_api_datetime(
                item.get("AT_START_ACT")
            ),

        "at_start_debarkasi":
            parse_api_datetime(
                item.get(
                    "AT_START_DEBARKASI"
                )
            ),

        "at_end_debarkasi":
            parse_api_datetime(
                item.get(
                    "AT_END_DEBARKASI"
                )
            ),

        "at_start_embarkasi":
            parse_api_datetime(
                item.get(
                    "AT_START_EMBARKASI"
                )
            ),

        "at_end_embarkasi":
            parse_api_datetime(
                item.get(
                    "AT_END_EMBARKASI"
                )
            ),

        "at_end_act":
            parse_api_datetime(
                item.get("AT_END_ACT")
            ),

        "last_line":
            parse_api_datetime(
                item.get("LAST_LINE")
            ),

        "ves_stat":
            item.get("VES_STAT"),

        "rec_stat":
            item.get("REC_STAT"),

        "status_kirim_manifest":
            item.get(
                "STATUS_KIRIM_MANIFEST"
            ),

        "sts_go":
            item.get("STS_GO"),

        "vesops_status":
            item.get(
                "VESOPS_STATUS"
            ),

        "onschedule_status":
            item.get(
                "ONSCHEDULE_STATUS"
            ),

        "no_pkk":
            item.get("NO_PKK"),

        "source":
            "API",

        "raw_data":
            json_safe(item),

        "api_created_date":
            parse_api_datetime(
                item.get("CREATED_DATE")
            ),

        "api_created_by":
            item.get("CREATED_BY"),

        "api_last_updated_date":
            parse_api_datetime(
                item.get(
                    "LAST_UPDATED_DATE"
                )
            ),

        "api_last_updated_by":
            item.get(
                "LAST_UPDATED_BY"
            ),

        "program_name":
            item.get(
                "PROGRAM_NAME"
            )
    }

    return json_safe(record)


# ============================================================
# GET EXISTING RECORD
# ============================================================

def get_existing_schedule(kd_jadwal):

    if not kd_jadwal:

        return None

    try:

        result = (
            supabase
            .table("schedule_voyages")
            .select("*")
            .eq(
                "kd_jadwal",
                kd_jadwal
            )
            .limit(1)
            .execute()
        )

        if result.data:

            return result.data[0]

    except Exception:

        pass

    return None


# ============================================================
# DETECT CHANGES
# ============================================================

def detect_changes(
    old,
    new
):

    changes = []

    fields = [

        (
            "nama_kapal",
            "Nama Kapal"
        ),

        (
            "voyage_no",
            "Voyage"
        ),

        (
            "nm_port_asal",
            "Pelabuhan Asal"
        ),

        (
            "nm_port_dest",
            "Pelabuhan Tujuan"
        ),

        (
            "nm_dermaga",
            "Dermaga"
        ),

        (
            "eta",
            "ETA"
        ),

        (
            "etd",
            "ETD"
        ),

        (
            "vesops_status",
            "Status"
        ),

        (
            "is_open_checkin",
            "Open Check-in"
        ),

        (
            "is_open_gate",
            "Open Gate"
        )
    ]

    for field, label in fields:

        old_value = old.get(field)
        new_value = new.get(field)

        # Convert datetime/string agar
        # perbandingan konsisten

        old_value = (
            str(old_value)
            if old_value is not None
            else None
        )

        new_value = (
            str(new_value)
            if new_value is not None
            else None
        )

        if old_value != new_value:

            changes.append({

                "field":
                    label,

                "old":
                    old_value or "-",

                "new":
                    new_value or "-"
            })

    return changes


# ============================================================
# SAVE / UPDATE SCHEDULE
# ============================================================

def save_schedule_to_supabase(
    api_data,
    detect_change=True
):

    inserted = 0
    updated = 0

    new_vessels = []
    changed_vessels = []

    errors = []

    for item in api_data:

        try:

            record = (
                convert_schedule_record(
                    item
                )
            )

            nama_kapal = (
                record.get(
                    "nama_kapal"
                )
            )

            kd_jadwal = (
                record.get(
                    "kd_jadwal"
                )
            )

            if not nama_kapal:

                continue

            if not kd_jadwal:

                errors.append(
                    f"{nama_kapal}: "
                    "KD_JADWAL kosong."
                )

                continue

            # =================================================
            # Existing
            # =================================================

            existing = (
                get_existing_schedule(
                    kd_jadwal
                )
            )

            # =================================================
            # NEW
            # =================================================

            if not existing:

                (
                    supabase
                    .table(
                        "schedule_voyages"
                    )
                    .insert(record)
                    .execute()
                )

                inserted += 1

                new_vessels.append({

                    "kd_jadwal":
                        kd_jadwal,

                    "nama_kapal":
                        nama_kapal,

                    "voyage_no":
                        record.get(
                            "voyage_no"
                        ),

                    "dermaga":
                        record.get(
                            "nm_dermaga"
                        )
                })

            # =================================================
            # EXISTING
            # =================================================

            else:

                changes = []

                if detect_change:

                    changes = detect_changes(
                        existing,
                        record
                    )

                (
                    supabase
                    .table(
                        "schedule_voyages"
                    )
                    .update(record)
                    .eq(
                        "id",
                        existing["id"]
                    )
                    .execute()
                )

                updated += 1

                if changes:

                    changed_vessels.append({

                        "id":
                            existing["id"],

                        "kd_jadwal":
                            kd_jadwal,

                        "nama_kapal":
                            nama_kapal,

                        "changes":
                            changes
                    })

        except Exception as e:

            errors.append(
                f"{item.get('NAMA_KAPAL', '-')}: "
                f"{str(e)}"
            )

    return {

        "inserted":
            inserted,

        "updated":
            updated,

        "new_vessels":
            new_vessels,

        "changed_vessels":
            changed_vessels,

        "errors":
            errors
    }


# ============================================================
# PERFORM SYNC
# ============================================================

def perform_schedule_sync(
    initial=False
):

    api_data, api_error = (
        get_schedule_from_api()
    )

    if api_error:

        return {

            "success":
                False,

            "message":
                api_error,

            "result":
                None
        }

    result = (
        save_schedule_to_supabase(
            api_data,
            detect_change=not initial
        )
    )

    sync_time = datetime.now(
        timezone.utc
    )

    st.session_state.last_sync_time = (
        sync_time
    )

    response = {

        "success":
            True,

        "message":
            "Sinkronisasi berhasil.",

        "result":
            result,

        "sync_time":
            sync_time,

        "total_api":
            len(api_data)
    }

    st.session_state.last_sync_result = (
        response
    )

    return response


# ============================================================
# LOGIN
# ============================================================

def login(
    email,
    password
):

    try:

        response = (
            supabase
            .auth
            .sign_in_with_password({
                "email":
                    email,

                "password":
                    password
            })
        )

        if not response.session:

            return (
                False,
                "Session login tidak ditemukan."
            )

        # ====================================================
        # Ambil profile
        # ====================================================

        profile_response = (
            supabase
            .rpc(
                "get_my_profile"
            )
            .execute()
        )

        if not profile_response.data:

            supabase.auth.sign_out()

            return (
                False,
                "Profile user tidak ditemukan."
            )

        profile = (
            profile_response.data[0]
        )

        if profile.get(
            "status"
        ) != "ACTIVE":

            supabase.auth.sign_out()

            return (
                False,
                "Akun tidak aktif."
            )

        st.session_state.profile = (
            profile
        )

        return (
            True,
            "Login berhasil."
        )

    except Exception as e:

        return (
            False,
            str(e)
        )


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
# TRANSACTION NUMBER
# ============================================================

def generate_transaction_number():

    result = (
        supabase
        .rpc(
            "generate_transaction_no"
        )
        .execute()
    )

    if result.data:

        return result.data

    raise Exception(
        "Gagal membuat nomor transaksi."
    )


# ============================================================
# DUPLICATE QR
# ============================================================

def check_duplicate_qr(
    schedule_id,
    qr_ticket
):

    result = (
        supabase
        .table(
            "weighing_transactions"
        )
        .select(
            "id,transaction_no,status"
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

    return (
        result.data or []
    )


# ============================================================
# SAVE TRANSACTION
# ============================================================

def save_transaction(
    vessel,
    qr_ticket,
    vehicle_group,
    bruto,
    profile
):

    try:

        schedule_id = (
            vessel["id"]
        )

        duplicate = (
            check_duplicate_qr(
                schedule_id,
                qr_ticket
            )
        )

        if duplicate:

            return (
                False,
                "QR tiket sudah digunakan "
                "pada kegiatan kapal ini.",
                None
            )

        transaction_no = (
            generate_transaction_number()
        )

        source = (
            "MANUAL"
            if vessel.get(
                "source"
            ) == "MANUAL"
            else "API"
        )

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
                vessel.get(
                    "kd_dermaga"
                ),

            "destination_berth_name":
                vessel.get(
                    "nm_dermaga"
                ),

            "operator_user_id":
                profile["id"],

            "transaction_source":
                source,

            "status":
                "COMPLETED",

            "transaction_time":
                datetime.now(
                    timezone.utc
                ).isoformat()
        }

        result = (
            supabase
            .table(
                "weighing_transactions"
            )
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
# LOGIN PAGE
# ============================================================

if st.session_state.profile is None:

    st.markdown(
        """
        <div class="main-title">
        ⚓ Manual RORO
        </div>

        <div class="sub-title">
        Sistem Input Kendaraan Pelabuhan
        </div>
        """,
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

                    success, message = (
                        login(
                            email,
                            password
                        )
                    )

                if success:

                    st.rerun()

                else:

                    st.error(
                        message
                    )

    st.stop()


# ============================================================
# PROFILE
# ============================================================

profile = (
    st.session_state.profile
)


# ============================================================
# INITIAL SYNC
# ============================================================

if not st.session_state.initial_sync_done:

    with st.spinner(
        "Mengambil jadwal kapal terbaru..."
    ):

        result = perform_schedule_sync(
            initial=True
        )

    st.session_state.initial_sync_done = (
        True
    )

    st.session_state.last_sync_result = (
        result
    )

    if not result["success"]:

        st.warning(
            "⚠️ API ScheduleBoard tidak dapat "
            "diakses. Data lokal tetap dapat digunakan."
        )


# ============================================================
# AUTO SYNC DETECTION
# ============================================================

current_result = (
    st.session_state.last_sync_result
)

# Streamlit rerun akan terjadi setiap 10 menit.
# Kita sync ulang jika sudah lebih dari 10 menit.

should_sync = False

if st.session_state.last_sync_time:

    elapsed = (
        datetime.now(
            timezone.utc
        )
        -
        st.session_state.last_sync_time
    ).total_seconds()

    if elapsed >= (
        AUTO_SYNC_MINUTES * 60
    ):

        should_sync = True


if should_sync:

    result = perform_schedule_sync(
        initial=False
    )

    st.session_state.last_sync_result = (
        result
    )


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
        f"**{profile.get('name', '-')}"
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

    # ========================================================
    # SYNC STATUS
    # ========================================================

    if st.session_state.last_sync_time:

        sync_display = (
            st.session_state
            .last_sync_time
            .astimezone()
            .strftime(
                "%d-%m-%Y %H:%M:%S"
            )
        )

        st.caption(
            "Sinkron terakhir:"
        )

        st.caption(
            sync_display
        )

    st.caption(
        f"Auto sync: {AUTO_SYNC_MINUTES} menit"
    )

    st.divider()

    if st.button(
        "🔄 Sinkron Sekarang",
        use_container_width=True
    ):

        with st.spinner(
            "Sinkronisasi..."
        ):

            result = (
                perform_schedule_sync(
                    initial=False
                )
            )

        st.session_state.last_sync_result = (
            result
        )

        st.rerun()

    if st.button(
        "Keluar",
        use_container_width=True
    ):

        logout()


# ============================================================
# NOTIFICATION
# ============================================================

sync_result = (
    st.session_state.last_sync_result
)

if sync_result:

    result_data = (
        sync_result.get(
            "result"
        )
        or {}
    )

    new_vessels = (
        result_data.get(
            "new_vessels",
            []
        )
    )

    changed_vessels = (
        result_data.get(
            "changed_vessels",
            []
        )
    )

    errors = (
        result_data.get(
            "errors",
            []
        )
    )

    # ========================================================
    # NEW
    # ========================================================

    if new_vessels:

        st.warning(
            f"🔔 {len(new_vessels)} "
            "jadwal kapal baru ditemukan."
        )

        with st.expander(
            "Lihat jadwal kapal baru",
            expanded=True
        ):

            for vessel in new_vessels:

                st.markdown(
                    f"""
                    <div class="new-vessel">

                    🚢 <b>
                    {vessel.get("nama_kapal", "-")}
                    </b>

                    <br>

                    Voyage:
                    {vessel.get("voyage_no", "-")}

                    <br>

                    Dermaga:
                    {vessel.get("dermaga", "-")}

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if st.button(
                "🔄 SINKRON SEKARANG",
                type="primary"
            ):

                with st.spinner(
                    "Sinkronisasi ulang..."
                ):

                    fresh_result = (
                        perform_schedule_sync(
                            initial=False
                        )
                    )

                st.session_state.last_sync_result = (
                    fresh_result
                )

                st.rerun()

    # ========================================================
    # CHANGED
    # ========================================================

    if changed_vessels:

        st.info(
            f"🔵 Ada {len(changed_vessels)} "
            "jadwal kapal yang berubah."
        )

        with st.expander(
            "Lihat perubahan jadwal"
        ):

            for vessel in changed_vessels:

                st.markdown(
                    f"""
                    <div class="changed-vessel">

                    🚢 <b>
                    {vessel.get("nama_kapal", "-")}
                    </b>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                for change in vessel.get(
                    "changes",
                    []
                ):

                    st.write(
                        f"**{change['field']}**"
                    )

                    st.write(
                        f"{change['old']} "
                        f"→ "
                        f"{change['new']}"
                    )

    # ========================================================
    # ERRORS
    # ========================================================

    if errors:

        with st.expander(
            f"⚠️ {len(errors)} data gagal diproses"
        ):

            for error in errors:

                st.error(error)


# ============================================================
# DASHBOARD
# ============================================================

if menu == "🏠 Dashboard":

    st.markdown(
        """
        <div class="main-title">
        Dashboard
        </div>

        <div class="sub-title">
        Monitoring Manual RORO
        </div>
        """,
        unsafe_allow_html=True
    )

    try:

        schedule_result = (
            supabase
            .table(
                "schedule_voyages"
            )
            .select(
                "id"
            )
            .execute()
        )

        total_schedule = len(
            schedule_result.data or []
        )

    except Exception:

        total_schedule = 0

    try:

        trx_result = (
            supabase
            .table(
                "weighing_transactions"
            )
            .select(
                "id,bruto_kg"
            )
            .eq(
                "status",
                "COMPLETED"
            )
            .execute()
        )

        transactions = (
            trx_result.data or []
        )

    except Exception:

        transactions = []

    total_transaction = len(
        transactions
    )

    total_bruto = sum(
        float(
            row.get(
                "bruto_kg",
                0
            )
        )
        for row in transactions
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Kegiatan Kapal",
            total_schedule
        )

    with col2:

        st.metric(
            "Total Transaksi",
            total_transaction
        )

    with col3:

        st.metric(
            "Total Bruto",
            f"{total_bruto:,.0f} Kg"
        )

    st.divider()

    # ========================================================
    # SYNC CARD
    # ========================================================

    st.markdown(
        "### Status ScheduleBoard"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            <div class="sync-card">

            🟢 <b>ScheduleBoard API</b>

            <br><br>

            Auto synchronization:
            <b>10 menit</b>

            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        if st.session_state.last_sync_time:

            sync_time = (
                st.session_state
                .last_sync_time
                .astimezone()
                .strftime(
                    "%d-%m-%Y %H:%M:%S"
                )
            )

            st.markdown(
                f"""
                <div class="sync-card">

                🕒 <b>Sinkronisasi terakhir</b>

                <br><br>

                {sync_time}

                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

    st.info(
        "Gunakan menu **Input Kendaraan** "
        "untuk melakukan pencatatan kendaraan."
    )


# ============================================================
# KEGIATAN KAPAL
# ============================================================

elif menu == "🚢 Kegiatan Kapal":

    st.markdown(
        """
        <div class="main-title">
        Kegiatan Kapal
        </div>

        <div class="sub-title">
        Data ScheduleBoard
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🔄 Sinkron Sekarang",
        type="primary"
    ):

        with st.spinner(
            "Mengambil data API..."
        ):

            result = (
                perform_schedule_sync(
                    initial=False
                )
            )

        st.session_state.last_sync_result = (
            result
        )

        st.rerun()

    st.divider()

    try:

        schedule_result = (
            supabase
            .table(
                "schedule_voyages"
            )
            .select("*")
            .order(
                "eta",
                desc=False
            )
            .limit(300)
            .execute()
        )

        schedule_data = (
            schedule_result.data or []
        )

    except Exception as e:

        st.error(
            f"Gagal mengambil jadwal: {e}"
        )

        schedule_data = []

    if not schedule_data:

        st.info(
            "Belum ada jadwal kapal."
        )

    else:

        for vessel in schedule_data:

            with st.container(
                border=True
            ):

                col1, col2, col3 = (
                    st.columns(
                        [2, 2, 1]
                    )
                )

                with col1:

                    st.markdown(
                        f"""
                        ### 🚢
                        {vessel.get(
                            "nama_kapal",
                            "-"
                        )}
                        """
                    )

                    st.caption(
                        f"Voyage: "
                        f"{vessel.get(
                            'voyage_no',
                            '-'
                        )}"
                    )

                with col2:

                    st.write(
                        f"**Rute:** "
                        f"{vessel.get(
                            'nm_port_asal',
                            '-'
                        )}"
                        f" → "
                        f"{vessel.get(
                            'nm_port_dest',
                            '-'
                        )}"
                    )

                    st.write(
                        f"**Dermaga:** "
                        f"{vessel.get(
                            'nm_dermaga',
                            '-'
                        )}"
                    )

                with col3:

                    st.write(
                        f"**Source:** "
                        f"{vessel.get(
                            'source',
                            '-'
                        )}"
                    )

                    st.write(
                        f"**Status:** "
                        f"{vessel.get(
                            'vesops_status',
                            '-'
                        )}"
                    )


# ============================================================
# INPUT KENDARAAN
# ============================================================

elif menu == "🚛 Input Kendaraan":

    st.markdown(
        """
        <div class="main-title">
        Input Kendaraan
        </div>

        <div class="sub-title">
        Pencatatan kendaraan masuk pelabuhan
        </div>
        """,
        unsafe_allow_html=True
    )

    try:

        result = (
            supabase
            .table(
                "schedule_voyages"
            )
            .select("*")
            .order(
                "eta",
                desc=False
            )
            .limit(300)
            .execute()
        )

        schedule_data = (
            result.data or []
        )

    except Exception as e:

        st.error(
            str(e)
        )

        st.stop()

    if not schedule_data:

        st.warning(
            "Belum ada kegiatan kapal."
        )

        st.stop()

    # ========================================================
    # VESSEL
    # ========================================================

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

    selected = st.selectbox(
        "Pilih kegiatan kapal",
        list(
            vessel_map.keys()
        )
    )

    vessel = vessel_map[selected]

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

        <b>Source:</b>
        {vessel.get("source", "-")}

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # QR
    # ========================================================

    st.markdown(
        "### 2️⃣ QR Tiket"
    )

    qr_ticket = st.text_input(
        "Scan QR tiket",
        placeholder=(
            "Scan QR menggunakan scanner..."
        )
    )

    # ========================================================
    # GROUP
    # ========================================================

    st.markdown(
        "### 3️⃣ Golongan Kendaraan"
    )

    vehicle_group = st.radio(
        "Golongan",
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

    # ========================================================
    # BRUTO
    # ========================================================

    st.markdown(
        "### 4️⃣ Berat Bruto"
    )

    bruto = st.number_input(
        "Bruto (Kg)",
        min_value=0.0,
        step=10.0,
        format="%.2f"
    )

    st.divider()

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
                "Bruto harus lebih dari 0 Kg."
            )

        if errors:

            for error in errors:

                st.error(error)

        else:

            with st.spinner(
                "Menyimpan transaksi..."
            ):

                success, message, trx = (
                    save_transaction(
                        vessel,
                        qr_ticket,
                        vehicle_group,
                        bruto,
                        profile
                    )
                )

            if success:

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
                    {trx["transaction_no"]}
                    </div>

                    <br>

                    <b>Kapal:</b>
                    {vessel.get(
                        "nama_kapal",
                        "-"
                    )}

                    <br>

                    <b>Golongan:</b>
                    {vehicle_group}

                    <br>

                    <b>Bruto:</b>
                    {bruto:,.2f} Kg

                    <br>

                    <b>Dermaga:</b>
                    {vessel.get(
                        "nm_dermaga",
                        "-"
                    )}

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.error(
                    message
                )


# ============================================================
# REPRINT
# ============================================================

elif menu == "🖨️ Reprint":

    st.markdown(
        """
        <div class="main-title">
        Reprint
        </div>

        <div class="sub-title">
        Cari transaksi
        </div>
        """,
        unsafe_allow_html=True
    )

    search = st.text_input(
        "Nomor Transaksi / QR Tiket"
    )

    if st.button(
        "🔎 Cari",
        type="primary"
    ):

        if not search.strip():

            st.warning(
                "Masukkan nomor transaksi "
                "atau QR tiket."
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

                    trx = (
                        result.data[0]
                    )

                    vessel = (
                        trx.get(
                            "schedule_voyages"
                        )
                        or {}
                    )

                    st.success(
                        "Transaksi ditemukan."
                    )

                    st.write(
                        f"**Nomor:** "
                        f"{trx.get(
                            'transaction_no'
                        )}"
                    )

                    st.write(
                        f"**QR:** "
                        f"{trx.get(
                            'qr_ticket'
                        )}"
                    )

                    st.write(
                        f"**Kapal:** "
                        f"{vessel.get(
                            'nama_kapal',
                            '-'
                        )}"
                    )

                    st.write(
                        f"**Golongan:** "
                        f"{trx.get(
                            'vehicle_group'
                        )}"
                    )

                    st.write(
                        f"**Bruto:** "
                        f"{float(
                            trx.get(
                                'bruto_kg',
                                0
                            )
                        ):,.2f} Kg"
                    )

                    st.write(
                        f"**Dermaga:** "
                        f"{trx.get(
                            'destination_berth_name',
                            '-'
                        )}"
                    )

                    st.divider()

                    st.info(
                        "Template cetak tiket akan "
                        "kita buat pada tahap berikutnya."
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
        """
        <div class="main-title">
        Laporan
        </div>

        <div class="sub-title">
        Log data timbangan
        </div>
        """,
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

    st.write(
        f"**{len(data)} transaksi ditemukan.**"
    )

    if data:

        rows = []

        for trx in data:

            vessel = (
                trx.get(
                    "schedule_voyages"
                )
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

        df = pd.DataFrame(
            rows
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        csv = df.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        )

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
