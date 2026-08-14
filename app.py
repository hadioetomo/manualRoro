import streamlit as st
import requests
import pandas as pd
from supabase import create_client
from datetime import datetime
from dateutil import parser
import time

# =====================================================
# CONFIG
# =====================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]

# untuk login user
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# untuk sync API
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]

PTOSR_API = st.secrets["PTOSR_API"]

# client login
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# client admin
supabase_admin = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)

# =====================================================
# LOGIN
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:

    st.title("🚢 RORO Gate System")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        try:

            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            st.session_state.login = True
            st.session_state.user = res.user

            st.rerun()

        except Exception as e:
            st.error(str(e))

    st.stop()

# =====================================================
# DASHBOARD
# =====================================================

st.title("🚢 Dashboard Admin")

# =====================================================
# SYNC API
# =====================================================

def parse_date(value):

    if not value:
        return None

    try:
        return parser.parse(value).isoformat()
    except:
        return None


def sync_api():

    try:

        response = requests.get(
            PTOSR_API,
            timeout=30
        )

        data = response.json()

        success = 0
        failed = 0

        for kapal in data:

            try:

                row = {

                    "voyage_no":
                        kapal.get("VOYAGE_NO"),

                    "kd_jadwal":
                        kapal.get("KD_JADWAL"),

                    "nama_kapal":
                        kapal.get("NAMA_KAPAL"),

                    "nm_dermaga":
                        kapal.get("NM_DERMAGA"),

                    "eta":
                        parse_date(
                            kapal.get("ETA")
                        ),

                    "etd":
                        parse_date(
                            kapal.get("ETD")
                        ),

                    "kd_operator":
                        kapal.get("KD_OPERATOR"),

                    "nm_operator":
                        kapal.get("NM_OPERATOR"),

                    "vesops_status":
                        kapal.get("VESOPS_STATUS"),

                    "source":
                        "API",

                    "updated_at":
                        datetime.now().isoformat()
                }

                # cek existing
                old = supabase_admin.table(
                    "schedule_voyages"
                ).select(
                    "id"
                ).eq(
                    "voyage_no",
                    kapal.get("VOYAGE_NO")
                ).execute()

                if old.data:

                    supabase_admin.table(
                        "schedule_voyages"
                    ).update(
                        row
                    ).eq(
                        "voyage_no",
                        kapal.get("VOYAGE_NO")
                    ).execute()

                else:

                    row["created_at"] = datetime.now().isoformat()

                    supabase_admin.table(
                        "schedule_voyages"
                    ).insert(
                        row
                    ).execute()

                success += 1

            except Exception as e:

                failed += 1

                st.error(
                    f"{kapal.get('NAMA_KAPAL')} : {e}"
                )

        st.success(
            f"Berhasil : {success}"
        )

        if failed > 0:
            st.warning(
                f"Gagal : {failed}"
            )

    except Exception as e:
        st.error(str(e))

# =====================================================
# BUTTON
# =====================================================

col1, col2 = st.columns(2)

with col1:

    if st.button("🔄 Sinkron Sekarang"):

        sync_api()

with col2:

    if st.button("📋 Lihat Jadwal"):

        data = supabase_admin.table(
            "schedule_voyages"
        ).select("*").order(
            "eta"
        ).execute()

        if data.data:

            df = pd.DataFrame(data.data)

            st.dataframe(
                df,
                use_container_width=True
            )

# =====================================================
# AUTO SYNC
# =====================================================

if "last_sync" not in st.session_state:
    st.session_state.last_sync = 0

now = time.time()

if now - st.session_state.last_sync > 600:

    sync_api()

    st.session_state.last_sync = now
