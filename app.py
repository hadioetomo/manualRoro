import streamlit as st
import requests
import pandas as pd
import io
import time
from datetime import datetime, timezone

from supabase import create_client
from postgrest.exceptions import APIError


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="RORO Gate & Weighing",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONSTANT
# ============================================================

PTOSR_API = (
    "https://ptosr.pelindo.co.id/"
    "ScheduleBoard/GetData"
    "?kd_cabang=61"
    "&kd_terminal=601"
)

AUTO_SYNC_SECONDS = 600


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    .main-title {
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .sub-title {
        color: #6b7280;
        margin-bottom: 20px;
    }

    .status-card {
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        background: white;
    }

    .ship-card {
        padding: 18px;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        background: white;
        margin-bottom: 10px;
    }

    .ship-name {
        font-size: 20px;
        font-weight: 700;
    }

    .small-text {
        font-size: 13px;
        color: #6b7280;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SUPABASE
# ============================================================

try:

    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

except Exception:

    st.error(
        """
        Secrets Supabase belum ditemukan.

        Pastikan Streamlit Cloud → Settings → Secrets berisi:

        SUPABASE_URL="https://xxxxx.supabase.co"
        SUPABASE_KEY="sb_publishable_xxxxx"
        """
    )

    st.stop()


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "profile" not in st.session_state:
    st.session_state.profile = None

if "last_sync" not in st.session_state:
    st.session_state.last_sync = None

if "new_vessels" not in st.session_state:
    st.session_state.new_vessels = []

if "sync_message" not in st.session_state:
    st.session_state.sync_message = None


# ============================================================
# UTILITY
# ============================================================

def parse_datetime(value):

    if value is None:
        return None

    if value == "":
        return None

    try:

        if isinstance(value, datetime):

            return value.isoformat()

        value = str(value).strip()

        formats = [
            "%Y/%m/%d %H:%M",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:

            try:

                dt = datetime.strptime(
                    value,
                    fmt
                )

                return dt.isoformat()

            except ValueError:
                continue

        return value

    except Exception:
        return None


def now_iso():

    return datetime.now(
        timezone.utc
    ).isoformat()


def safe_value(value):

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.isoformat()

    return value


def get_api_data():

    response = requests.get(
        PTOSR_API,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict):

        # beberapa API membungkus data
        for key in ["data", "Data", "result", "Result"]:

            if key in data:
                data = data[key]
                break

    if not isinstance(data, list):

        raise ValueError(
            "Format response API PTOSR bukan list."
        )

    return data


# ============================================================
# AUTH
# ============================================================

def login_user(email, password):

    try:

        result = supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

        if not result.user:

            return False, "Login gagal."

        st.session_state.logged_in = True
        st.session_state.user = result.user

        load_profile(result.user.id)

        return True, "Login berhasil."

    except Exception as e:

        return False, str(e)


def load_profile(auth_user_id):

    try:

        result = (
            supabase
            .table("users")
            .select(
                "id,auth_user_id,nipp,name,whatsapp,role_id,status,"
                "roles(id,code,name)"
            )
            .eq(
                "auth_user_id",
                auth_user_id
            )
            .limit(1)
            .execute()
        )

        if result.data:

            st.session_state.profile = result.data[0]

            return result.data[0]

        return None

    except Exception as e:

        st.warning(
            f"Profile user tidak dapat dibaca: {e}"
        )

        return None


def logout():

    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.profile = None

    st.rerun()


# ============================================================
# ROLE
# ============================================================

def get_role():

    profile = st.session_state.profile

    if not profile:
        return None

    role = profile.get("roles")

    if isinstance(role, list):

        if len(role) > 0:
            role = role[0]

    if isinstance(role, dict):

        return role.get("code")

    return None


def is_admin():

    return get_role() == "ADMIN"


def is_manager():

    return get_role() == "MANAGER"


def can_manage_schedule():

    return get_role() in [
        "ADMIN",
        "MANAGER"
    ]


# ============================================================
# LOGIN PAGE
# ============================================================

def show_login():

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:30px 0 10px 0;
        ">
            <div style="font-size:50px;">🚢</div>
            <div class="main-title">
                RORO Gate & Weighing
            </div>
            <div class="sub-title">
                Pelindo Sub Regional Jawa
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        st.subheader("Login")

        email = st.text_input(
            "Email",
            placeholder="Email akun Supabase"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "🔐 Login",
            use_container_width=True,
            type="primary"
        ):

            if not email or not password:

                st.warning(
                    "Email dan password wajib diisi."
                )

            else:

                success, message = login_user(
                    email,
                    password
                )

                if success:

                    st.success(message)

                    time.sleep(0.5)

                    st.rerun()

                else:

                    st.error(message)


# ============================================================
# BUILD SCHEDULE PAYLOAD
# ============================================================

def build_schedule_payload(kapal):

    return {

        "kd_jadwal":
            kapal.get("KD_JADWAL"),

        "voyage_no":
            kapal.get("VOYAGE_NO"),

        "kd_kapal":
            kapal.get("KD_KAPAL"),

        "nama_kapal":
            kapal.get("NAMA_KAPAL"),

        "kd_operator":
            kapal.get("KD_OPERATOR"),

        "nm_operator":
            kapal.get("NM_OPERATOR"),

        "kd_port_asal":
            kapal.get("KD_PORT_ASAL"),

        "nm_port_asal":
            kapal.get("NM_PORT_ASAL"),

        "kd_port_dest":
            kapal.get("KD_PORT_DEST"),

        "nm_port_dest":
            kapal.get("NM_PORT_DEST"),

        "kd_dermaga":
            kapal.get("KD_DERMAGA"),

        "nm_dermaga":
            kapal.get("NM_DERMAGA"),

        "eta":
            parse_datetime(
                kapal.get("ETA")
            ),

        "et_berthing":
            parse_datetime(
                kapal.get("ET_BERTHING")
            ),

        "etd":
            parse_datetime(
                kapal.get("ETD")
            ),

        "open_date":
            parse_datetime(
                kapal.get("OPEN_DATE")
            ),

        "closing_date":
            parse_datetime(
                kapal.get("CLOSING_DATE")
            ),

        "is_open_checkin":
            kapal.get("IS_OPEN_CHECKIN"),

        "is_open_gate":
            kapal.get("IS_OPEN_GATE"),

        "kd_route":
            kapal.get("KD_ROUTE"),

        "ves_stat":
            kapal.get("VES_STAT"),

        "rec_stat":
            kapal.get("REC_STAT"),

        "sts_go":
            kapal.get("STS_GO"),

        "vesops_status":
            kapal.get("VESOPS_STATUS"),

        "onschedule_status":
            kapal.get("ONSCHEDULE_STATUS"),

        "source":
            "API",

        "updated_at":
            now_iso()
    }


# ============================================================
# GET EXISTING SCHEDULE
# ============================================================

def get_existing_schedule(kd_jadwal):

    try:

        result = (
            supabase
            .table("schedule_voyages")
            .select("id,kd_jadwal,nama_kapal")
            .eq(
                "kd_jadwal",
                kd_jadwal
            )
            .limit(1)
            .execute()
        )

        if result.data:
            return result.data[0]

        return None

    except Exception:

        return None


# ============================================================
# SYNC SCHEDULE
# ============================================================

def sync_schedule():

    if not can_manage_schedule():

        st.error(
            "Anda tidak memiliki hak untuk sinkronisasi jadwal."
        )

        return

    try:

        with st.spinner(
            "Mengambil jadwal kapal dari PTOSR..."
        ):

            data = get_api_data()

        if not data:

            st.warning(
                "API PTOSR tidak mengembalikan data kapal."
            )

            return

        total = len(data)
        success = 0
        failed = 0
        new_vessels = []

        progress = st.progress(0)

        for index, kapal in enumerate(data):

            nama_kapal = (
                kapal.get("NAMA_KAPAL")
                or "UNKNOWN"
            )

            kd_jadwal = (
                kapal.get("KD_JADWAL")
            )

            if not kd_jadwal:

                failed += 1

                progress.progress(
                    (index + 1) / total
                )

                continue

            payload = build_schedule_payload(
                kapal
            )

            try:

                existing = get_existing_schedule(
                    kd_jadwal
                )

                if existing is None:

                    new_vessels.append(
                        nama_kapal
                    )

                (
                    supabase
                    .table("schedule_voyages")
                    .upsert(
                        payload,
                        on_conflict="kd_jadwal"
                    )
                    .execute()
                )

                success += 1

            except Exception as e:

                failed += 1

                st.error(
                    f"{nama_kapal}: {str(e)}"
                )

                with st.expander(
                    f"Detail {nama_kapal}"
                ):

                    st.write(
                        "Payload yang dikirim:"
                    )

                    st.json(payload)

                    st.write(
                        "Error:"
                    )

                    st.code(
                        repr(e)
                    )

            progress.progress(
                (index + 1) / total
            )

        st.session_state.last_sync = (
            datetime.now()
        )

        st.session_state.new_vessels = (
            new_vessels
        )

        st.session_state.sync_message = (
            success,
            failed
        )

        if new_vessels:

            st.success(
                f"Sinkron selesai. "
                f"{len(new_vessels)} jadwal kapal baru ditemukan."
            )

            for vessel in new_vessels:

                st.toast(
                    f"🚢 Jadwal baru: {vessel}",
                    icon="🚢"
                )

        else:

            st.success(
                f"Sinkron selesai. "
                f"Berhasil: {success} | "
                f"Gagal: {failed}"
            )

    except Exception as e:

        st.error(
            f"API PTOSR gagal diakses: {str(e)}"
        )


# ============================================================
# MANUAL VESSEL
# ============================================================

def manual_vessel():

    if not is_admin():

        st.warning(
            "Input kapal manual hanya dapat dilakukan Admin."
        )

        return

    st.subheader(
        "➕ Tambah Kegiatan Kapal Manual"
    )

    st.info(
        "Gunakan menu ini apabila data kapal dari API PTOSR mengalami gangguan."
    )

    with st.form(
        "manual_vessel_form"
    ):

        col1, col2 = st.columns(2)

        with col1:

            kd_jadwal = st.text_input(
                "Kode Jadwal",
                placeholder="MANUAL-2026-001"
            )

            voyage_no = st.text_input(
                "Voyage No"
            )

            nama_kapal = st.text_input(
                "Nama Kapal"
            )

            nm_operator = st.text_input(
                "Nama Operator"
            )

        with col2:

            nm_port_asal = st.text_input(
                "Pelabuhan Asal"
            )

            nm_port_dest = st.text_input(
                "Pelabuhan Tujuan"
            )

            nm_dermaga = st.text_input(
                "Dermaga"
            )

            eta = st.text_input(
                "ETA",
                placeholder="2026/08/14 08:00"
            )

            etd = st.text_input(
                "ETD",
                placeholder="2026/08/14 18:00"
            )

        submit = st.form_submit_button(
            "💾 Simpan Kegiatan Kapal",
            use_container_width=True,
            type="primary"
        )

    if submit:

        if not kd_jadwal:

            st.error(
                "Kode jadwal wajib diisi."
            )

            return

        if not nama_kapal:

            st.error(
                "Nama kapal wajib diisi."
            )

            return

        payload = {

            "kd_jadwal":
                kd_jadwal,

            "voyage_no":
                voyage_no,

            "nama_kapal":
                nama_kapal,

            "nm_operator":
                nm_operator,

            "nm_port_asal":
                nm_port_asal,

            "nm_port_dest":
                nm_port_dest,

            "nm_dermaga":
                nm_dermaga,

            "eta":
                parse_datetime(eta),

            "etd":
                parse_datetime(etd),

            "source":
                "MANUAL",

            "updated_at":
                now_iso()
        }

        try:

            (
                supabase
                .table("schedule_voyages")
                .upsert(
                    payload,
                    on_conflict="kd_jadwal"
                )
                .execute()
            )

            st.success(
                f"Kegiatan kapal {nama_kapal} berhasil disimpan."
            )

        except Exception as e:

            st.error(
                f"Gagal menyimpan kapal: {str(e)}"
            )

            with st.expander(
                "Detail error"
            ):

                st.json(payload)

                st.code(
                    repr(e)
                )


# ============================================================
# GET SCHEDULE
# ============================================================

def get_schedule():

    try:

        result = (
            supabase
            .table("schedule_voyages")
            .select("*")
            .order(
                "eta",
                desc=False
            )
            .execute()
        )

        return result.data or []

    except Exception as e:

        st.error(
            f"Gagal mengambil jadwal kapal: {str(e)}"
        )

        return []


# ============================================================
# SCHEDULE PAGE
# ============================================================

def show_schedule():

    st.subheader(
        "🚢 Kegiatan Kapal"
    )

    col1, col2, col3 = st.columns(
        [2, 1, 1]
    )

    with col1:

        st.caption(
            "Jadwal kapal dari API PTOSR"
        )

    with col2:

        if st.button(
            "🔄 Sinkron Sekarang",
            use_container_width=True
        ):

            sync_schedule()

            st.rerun()

    with col3:

        if is_admin():

            if st.button(
                "➕ Kapal Manual",
                use_container_width=True
            ):

                st.session_state.menu = (
                    "Kapal Manual"
                )

                st.rerun()

    schedules = get_schedule()

    if not schedules:

        st.info(
            "Belum ada data jadwal kapal."
        )

        return

    df = pd.DataFrame(
        schedules
    )

    search = st.text_input(
        "🔎 Cari nama kapal",
        placeholder="Contoh: SINABUNG"
    )

    if search:

        df = df[
            df["nama_kapal"]
            .fillna("")
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    st.write(
        f"Jumlah kegiatan: **{len(df)}**"
    )

    for _, row in df.iterrows():

        nama = row.get(
            "nama_kapal",
            "-"
        )

        dermaga = row.get(
            "nm_dermaga",
            "-"
        )

        tujuan = row.get(
            "nm_port_dest",
            "-"
        )

        eta = row.get(
            "eta",
            "-"
        )

        etd = row.get(
            "etd",
            "-"
        )

        source = row.get(
            "source",
            "-"
        )

        st.markdown(
            f"""
            <div class="ship-card">

                <div class="ship-name">
                    🚢 {nama}
                </div>

                <div class="small-text">
                    Dermaga: {dermaga}
                    &nbsp;&nbsp; | &nbsp;&nbsp;
                    Tujuan: {tujuan}
                </div>

                <div class="small-text">
                    ETA: {eta}
                    &nbsp;&nbsp; | &nbsp;&nbsp;
                    ETD: {etd}
                    &nbsp;&nbsp; | &nbsp;&nbsp;
                    Source: {source}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# WEIGHING INPUT
# ============================================================

def show_weighing():

    st.subheader(
        "⚖️ Input Timbangan"
    )

    schedules = get_schedule()

    if not schedules:

        st.warning(
            "Belum ada kegiatan kapal."
        )

        return

    schedule_options = {}

    for row in schedules:

        label = (
            f"{row.get('nama_kapal', '-')}"
            f" | {row.get('nm_dermaga', '-')}"
            f" | {row.get('nm_port_dest', '-')}"
        )

        schedule_options[label] = row

    selected_label = st.selectbox(
        "Kegiatan Kapal",
        list(schedule_options.keys())
    )

    selected = schedule_options[
        selected_label
    ]

    st.info(
        f"""
        **Kapal:** {selected.get('nama_kapal', '-')}
        
        **Dermaga:** {selected.get('nm_dermaga', '-')}
        
        **Tujuan:** {selected.get('nm_port_dest', '-')}
        """
    )

    col1, col2 = st.columns(2)

    with col1:

        qr_ticket = st.text_input(
            "🎫 QR / Kode Tiket",
            placeholder="Scan QR tiket"
        )

        vehicle_class = st.selectbox(
            "Golongan Kendaraan",
            [
                "Golongan 1",
                "Golongan 2",
                "Golongan 3",
                "Golongan 4",
                "Golongan 5",
                "Golongan 6",
            ]
        )

    with col2:

        bruto = st.number_input(
            "⚖️ Berat Bruto (kg)",
            min_value=0.0,
            step=1.0
        )

    if st.button(
        "💾 Simpan Timbangan",
        use_container_width=True,
        type="primary"
    ):

        if not qr_ticket:

            st.error(
                "QR / kode tiket wajib diisi."
            )

            return

        if bruto <= 0:

            st.error(
                "Berat bruto harus lebih dari 0."
            )

            return

        payload = {

            "schedule_voyage_id":
                selected.get("id"),

            "ticket_code":
                qr_ticket,

            "vehicle_class":
                vehicle_class,

            "gross_weight":
                bruto,

            "nama_kapal":
                selected.get("nama_kapal"),

            "nm_dermaga":
                selected.get("nm_dermaga"),

            "created_at":
                now_iso()
        }

        try:

            (
                supabase
                .table("weighing_transactions")
                .insert(payload)
                .execute()
            )

            st.success(
                "Data timbangan berhasil disimpan."
            )

        except Exception as e:

            st.error(
                f"Gagal menyimpan data timbangan: {str(e)}"
            )

            with st.expander(
                "Detail error"
            ):

                st.json(payload)

                st.code(
                    repr(e)
                )


# ============================================================
# WEIGHING LOG
# ============================================================

def show_weighing_log():

    st.subheader(
        "📋 Log Timbangan"
    )

    start_date = st.date_input(
        "Tanggal"
    )

    kapal_filter = st.text_input(
        "Nama Kapal",
        placeholder="Kosongkan jika semua kapal"
    )

    try:

        result = (
            supabase
            .table("weighing_transactions")
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        data = result.data or []

    except Exception as e:

        st.error(
            f"Gagal mengambil log: {str(e)}"
        )

        return

    if not data:

        st.info(
            "Belum ada data timbangan."
        )

        return

    df = pd.DataFrame(
        data
    )

    if "created_at" in df.columns:

        df["created_at"] = pd.to_datetime(
            df["created_at"],
            errors="coerce"
        )

        df = df[
            df["created_at"]
            .dt.date
            == start_date
        ]

    if kapal_filter and "nama_kapal" in df.columns:

        df = df[
            df["nama_kapal"]
            .fillna("")
            .str.contains(
                kapal_filter,
                case=False,
                na=False
            )
        ]

    st.write(
        f"Jumlah transaksi: **{len(df)}**"
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if not df.empty:

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download CSV",
            data=csv,
            file_name=(
                f"log_timbangan_"
                f"{start_date}.csv"
            ),
            mime="text/csv",
            use_container_width=True
        )


# ============================================================
# MANUAL VESSEL PAGE
# ============================================================

def show_manual_vessel():

    manual_vessel()


# ============================================================
# SIDEBAR
# ============================================================

def show_sidebar():

    profile = st.session_state.profile

    with st.sidebar:

        st.markdown(
            "## 🚢 RORO System"
        )

        st.divider()

        if profile:

            st.write(
                f"**{profile.get('name', '-') }**"
            )

            st.caption(
                f"NIPP: {profile.get('nipp', '-')}"
            )

            st.caption(
                f"Role: {get_role() or '-'}"
            )

        st.divider()

        menu_items = [
            "Dashboard",
            "Kegiatan Kapal",
            "Input Timbangan",
            "Log Timbangan",
        ]

        if is_admin():

            menu_items.append(
                "Kapal Manual"
            )

        selected = st.radio(
            "Menu",
            menu_items
        )

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            logout()

        return selected


# ============================================================
# DASHBOARD
# ============================================================

def show_dashboard():

    schedules = get_schedule()

    total = len(schedules)

    source_api = sum(
        1
        for x in schedules
        if x.get("source") == "API"
    )

    source_manual = sum(
        1
        for x in schedules
        if x.get("source") == "MANUAL"
    )

    st.markdown(
        """
        <div class="main-title">
            Dashboard
        </div>

        <div class="sub-title">
            Monitoring kegiatan kapal dan timbangan
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "🚢 Total Kegiatan",
            total
        )

    with c2:

        st.metric(
            "🔄 Dari API",
            source_api
        )

    with c3:

        st.metric(
            "📝 Manual",
            source_manual
        )

    st.divider()

    if st.session_state.last_sync:

        st.caption(
            "Sinkronisasi terakhir: "
            + st.session_state.last_sync.strftime(
                "%d-%m-%Y %H:%M:%S"
            )
        )

    if st.session_state.new_vessels:

        st.success(
            "🚢 Ditemukan jadwal kapal baru:"
        )

        for vessel in st.session_state.new_vessels:

            st.write(
                f"• {vessel}"
            )


# ============================================================
# AUTO SYNC
# ============================================================

def auto_sync_check():

    if not st.session_state.logged_in:
        return

    if not can_manage_schedule():
        return

    last = st.session_state.last_sync

    if last is None:

        sync_schedule()

        return

    elapsed = (
        datetime.now() - last
    ).total_seconds()

    if elapsed >= AUTO_SYNC_SECONDS:

        sync_schedule()


# ============================================================
# MAIN
# ============================================================

if not st.session_state.logged_in:

    show_login()

    st.stop()


# ============================================================
# LOAD USER PROFILE
# ============================================================

if (
    st.session_state.user
    and not st.session_state.profile
):

    load_profile(
        st.session_state.user.id
    )


# ============================================================
# PROFILE CHECK
# ============================================================

if not st.session_state.profile:

    st.error(
        """
        Akun berhasil login, tetapi profile
        tidak ditemukan pada tabel public.users.
        """
    )

    if st.button("Logout"):

        logout()

    st.stop()


# ============================================================
# AUTO INITIAL SYNC
# ============================================================

if (
    can_manage_schedule()
    and st.session_state.last_sync is None
):

    sync_schedule()


# ============================================================
# SIDEBAR
# ============================================================

menu = show_sidebar()


# ============================================================
# PAGE
# ============================================================

if menu == "Dashboard":

    show_dashboard()

elif menu == "Kegiatan Kapal":

    show_schedule()

elif menu == "Input Timbangan":

    show_weighing()

elif menu == "Log Timbangan":

    show_weighing_log()

elif menu == "Kapal Manual":

    show_manual_vessel()
