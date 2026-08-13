import streamlit as st
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


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Manual RORO",
    page_icon="⚓",
    layout="wide"
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


# ============================================================
# RESTORE SESSION
# ============================================================

if (
    st.session_state.access_token
    and st.session_state.refresh_token
):

    try:
        supabase.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )
    except Exception:
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.profile = None


# ============================================================
# LOGIN FUNCTION
# ============================================================

def login(email, password):

    try:

        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not response.session:
            return False, "Session login tidak ditemukan."

        # Simpan session
        st.session_state.access_token = response.session.access_token
        st.session_state.refresh_token = response.session.refresh_token

        # ====================================================
        # AMBIL PROFILE DARI DATABASE
        # ====================================================

        profile_response = supabase.rpc(
            "get_my_profile"
        ).execute()

        if not profile_response.data:

            supabase.auth.sign_out()

            st.session_state.access_token = None
            st.session_state.refresh_token = None

            return False, (
                "Akun berhasil login tetapi profile "
                "tidak ditemukan di public.users."
            )

        profile = profile_response.data[0]

        # ====================================================
        # CEK STATUS
        # ====================================================

        if profile["status"] != "ACTIVE":

            supabase.auth.sign_out()

            st.session_state.access_token = None
            st.session_state.refresh_token = None

            return False, (
                "Akun Anda tidak aktif. "
                "Hubungi Administrator."
            )

        # Simpan profile
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
# LOGIN PAGE
# ============================================================

if st.session_state.profile is None:

    st.title("⚓ Manual RORO")

    st.subheader("Login Administrator")

    st.write(
        "Sistem Input Manual Kendaraan Masuk Pelabuhan"
    )

    st.divider()

    email = st.text_input(
        "Email",
        placeholder="Masukkan email Admin"
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Masukkan password"
    )

    if st.button(
        "LOGIN",
        type="primary",
        use_container_width=True
    ):

        if not email or not password:

            st.error(
                "Email dan password wajib diisi."
            )

        else:

            with st.spinner("Memproses login..."):

                success, message = login(
                    email,
                    password
                )

            if success:

                st.success(message)

                st.rerun()

            else:

                st.error(message)


# ============================================================
# DASHBOARD
# ============================================================

else:

    profile = st.session_state.profile

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    with st.sidebar:

        st.title("⚓ Manual RORO")

        st.divider()

        st.write("**Pengguna**")

        st.write(profile["name"])

        st.write(
            f"NIPP: `{profile['nipp']}`"
        )

        st.write(
            f"Role: `{profile['role_code']}`"
        )

        st.write(
            f"Status: `{profile['status']}`"
        )

        st.divider()

        if st.button(
            "Logout",
            use_container_width=True
        ):

            logout()


    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.title("Dashboard")

    st.write(
        f"Selamat datang, **{profile['name']}**."
    )

    st.divider()


    # --------------------------------------------------------
    # ADMIN DASHBOARD
    # --------------------------------------------------------

    if profile["role_code"] == "ADMIN":

        st.subheader("Administrator")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.info(
                "👤\n\n"
                "**Manajemen User**\n\n"
                "Kelola user, role dan status."
            )

        with col2:

            st.info(
                "🚛\n\n"
                "**Transaksi Kendaraan**\n\n"
                "Input dan monitoring kendaraan."
            )

        with col3:

            st.info(
                "📊\n\n"
                "**Laporan**\n\n"
                "Download data transaksi."
            )


    # --------------------------------------------------------
    # MANAGER DASHBOARD
    # --------------------------------------------------------

    elif profile["role_code"] == "MANAGER":

        st.subheader("Manager")

        col1, col2 = st.columns(2)

        with col1:

            st.info(
                "🚛\n\n"
                "**Monitoring Transaksi**"
            )

        with col2:

            st.info(
                "📊\n\n"
                "**Laporan Timbangan**"
            )


    # --------------------------------------------------------
    # OPERATOR DASHBOARD
    # --------------------------------------------------------

    elif profile["role_code"] == "OPERATOR":

        st.subheader("Operator")

        st.info(
            "🚛\n\n"
            "**Input Kendaraan**"
        )

        st.info(
            "🧾\n\n"
            "**Reprint Tiket**"
        )
