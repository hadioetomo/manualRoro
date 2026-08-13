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
    page_title="Vehicle Weighing System",
    page_icon="⚓",
    layout="centered"
)


# ============================================================
# SESSION
# ============================================================

if "user" not in st.session_state:
    st.session_state.user = None


# ============================================================
# LOGIN
# ============================================================

if st.session_state.user is None:

    st.title("⚓ Vehicle Weighing System")

    st.subheader("Login Administrator")

    email = st.text_input(
        "Email"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
        "LOGIN",
        use_container_width=True
    ):

        if not email or not password:

            st.error(
                "Email dan password wajib diisi."
            )

        else:

            try:

                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                st.session_state.user = response.user

                st.success(
                    "Login berhasil."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Login gagal: {str(e)}"
                )


# ============================================================
# DASHBOARD
# ============================================================

else:

    user = st.session_state.user

    st.title("Dashboard")

    st.success(
        "Login berhasil."
    )

    st.write(
        "Supabase Auth User ID:"
    )

    st.code(
        user.id
    )

    st.write(
        "Email:"
    )

    st.write(
        user.email
    )

    if st.button(
        "LOGOUT"
    ):

        supabase.auth.sign_out()

        st.session_state.user = None

        st.rerun()
