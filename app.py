import streamlit as st
import requests
from supabase import create_client
from datetime import datetime
import pandas as pd
import time

# ========================
# CONFIG
# ========================

SUPABASE_URL = st.secrets["SUPABASE_URL"]

SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

SUPABASE_SECRET_KEY = st.secrets["SUPABASE_SECRET_KEY"]

PTOSR_API = st.secrets["PTOSR_API"]

# client biasa (login)
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# client khusus sync
supabase_admin = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)

# ========================
# FORMAT DATETIME
# ========================

def parse_datetime(dt):

    if not dt:
        return None

    try:
        return datetime.strptime(
            dt,
            "%Y/%m/%d %H:%M"
        ).isoformat()
    except:
        return None


# ========================
# SYNC API
# ========================

def sync_schedule():

    result = requests.get(
        PTOSR_API,
        timeout=30
    )

    if result.status_code != 200:
        st.error("API gagal")
        return

    data = result.json()

    total = 0

    for kapal in data:

        try:

            payload = {

                "kd_jadwal":
                    kapal.get("KD_JADWAL"),

                "voyage_no":
                    kapal.get("VOYAGE_NO"),

                "nama_kapal":
                    kapal.get("NAMA_KAPAL"),

                "nm_operator":
                    kapal.get("NM_OPERATOR"),

                "kd_dermaga":
                    kapal.get("KD_DERMAGA"),

                "nm_dermaga":
                    kapal.get("NM_DERMAGA"),

                "port_asal":
                    kapal.get("NM_PORT_ASAL"),

                "port_tujuan":
                    kapal.get("NM_PORT_DEST"),

                "eta":
                    parse_datetime(
                        kapal.get("ETA")
                    ),

                "etd":
                    parse_datetime(
                        kapal.get("ETD")
                    ),

                "open_date":
                    parse_datetime(
                        kapal.get("OPEN_DATE")
                    ),

                "vesops_status":
                    kapal.get(
                        "VESOPS_STATUS"
                    ),

                "source":
                    "API",

                "updated_at":
                    datetime.now().isoformat()
            }

            # UPSERT
            res = (
                supabase_admin
                .table("schedule_voyages")
                .upsert(
                    payload,
                    on_conflict="kd_jadwal"
                )
                .execute()
            )

            total += 1

        except Exception as e:

            st.warning(
                f"{kapal.get('NAMA_KAPAL')} : {e}"
            )

    st.success(
        f"Berhasil sync {total} kapal"
    )


# ========================
# DASHBOARD
# ========================

st.title("🚢 Jadwal Kapal RORO")

col1,col2 = st.columns(2)

with col1:

    if st.button("🔄 Sinkron Sekarang"):
        sync_schedule()

with col2:

    auto = st.checkbox(
        "Auto Sync 10 Menit"
    )

# ========================
# TAMPILKAN DATA
# ========================

data = (
    supabase_admin
    .table("schedule_voyages")
    .select("*")
    .order(
        "eta",
        desc=False
    )
    .execute()
)

if data.data:

    df = pd.DataFrame(data.data)

    tampil = [
        "nama_kapal",
        "nm_dermaga",
        "eta",
        "etd",
        "vesops_status"
    ]

    st.dataframe(
        df[tampil],
        use_container_width=True
    )

# ========================
# AUTO SYNC
# ========================

if auto:

    st.info(
        "Auto sync aktif"
    )

    while True:

        sync_schedule()

        time.sleep(600)
