import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from auth import generate_otp, send_otp_whatsapp

st.set_page_config(page_title="Sistem Timbangan RORO", layout="centered", page_icon="🚢")

# --- INISIALISASI SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'otp_terkirim' not in st.session_state:
    st.session_state['otp_terkirim'] = False
if 'otp_saat_ini' not in st.session_state:
    st.session_state['otp_saat_ini'] = ""
if 'temp_no_wa' not in st.session_state:
    st.session_state['temp_no_wa'] = ""
if 'user_aktif' not in st.session_state:
    st.session_state['user_aktif'] = ""

# --- FUNGSI AMBIL DATA API (Di-cache agar tidak lambat) ---
@st.cache_data(ttl=300) # Data di-cache selama 5 menit
def fetch_data_jadwal():
    url_api = "https://ptosr.pelindo.co.id/ScheduleBoard/GetData?kd_cabang=61&kd_terminal=601"
    try:
        response = requests.get(url_api, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.sidebar.error(f"Gagal koneksi ke API: {e}")
    return None

# --- HALAMAN LOGIN ---
def show_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #1E88E5;'>🔐 LOGIN PETUGAS</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Sistem Timbangan Manual RORO</p>", unsafe_allow_html=True)
            st.divider()

            no_wa = st.text_input("Nomor WhatsApp", placeholder="Contoh: 081234567890")
            
            # Ambil dictionary USERS dari secrets
            users_dict = st.secrets.get("USERS", {})
            
            if not st.session_state['otp_terkirim']:
                if st.button("Kirim OTP 📲", use_container_width=True):
                    if no_wa:
                        if no_wa in users_dict:
                            with st.spinner("Mengirim OTP..."):
                                otp = generate_otp()
                                sukses, pesan = send_otp_whatsapp(no_wa, otp)
                                
                                if sukses:
                                    st.session_state['otp_saat_ini'] = otp
                                    st.session_state['otp_terkirim'] = True
                                    st.session_state['temp_no_wa'] = no_wa 
                                    st.rerun()
                                else:
                                    st.error(pesan)
                        else:
                            st.error("⛔ Akses Ditolak: Nomor Anda tidak terdaftar!")
                    else:
                        st.warning("Masukkan nomor WhatsApp terlebih dahulu!")
            
            if st.session_state['otp_terkirim']:
                st.success("OTP telah dikirim ke WhatsApp Anda!")
                input_otp = st.text_input("Masukkan 6 Digit OTP", type="password", max_chars=6)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Verifikasi & Login ✅", type="primary", use_container_width=True):
                        if input_otp == st.session_state['otp_saat_ini']:
                            st.session_state['authenticated'] = True
                            st.session_state['user_aktif'] = users_dict[st.session_state['temp_no_wa']]
                            st.rerun()
                        else:
                            st.error("Kode OTP Salah!")
                with col_b:
                    if st.button("Batal", use_container_width=True):
                        st.session_state['otp_terkirim'] = False
                        st.session_state['otp_saat_ini'] = ""
                        st.session_state['temp_no_wa'] = ""
                        st.rerun()

# --- HALAMAN UTAMA ---
def show_main_app():
    if 'welcome_shown' not in st.session_state:
        st.toast(f"Selamat datang, {st.session_state['user_aktif']}! 👋", icon="✅")
        st.session_state['welcome_shown'] = True

    with st.sidebar:
        st.info(f"👤 **Petugas Aktif:**\n\n{st.session_state['user_aktif']}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['authenticated'] = False
            st.session_state['otp_terkirim'] = False
            st.session_state['user_aktif'] = ""
            if 'welcome_shown' in st.session_state:
                del st.session_state['welcome_shown']
            st.rerun()
            
    st.header("CETAK TIMBANGAN MANUAL RORO")
    st.subheader("Pelabuhan Tanjung Perak Surabaya")
    st.divider()
    
    # PENGOLAHAN DATA API
    data_api = fetch_data_jadwal()
    mapping_kapal = {} # Dictionary untuk menyimpan pasangan Kapal -> Pelabuhan
    
    if data_api and isinstance(data_api, list):
        for item in data_api:
            nama = item.get("NAMA_KAPAL")
            destinasi = item.get("NM_PORT_DEST")
            
            # Jika ada nama kapal, masukkan ke dalam dictionary
            if nama:
                # Jika NM_PORT_DEST kosong dari API, beri nilai default
                mapping_kapal[nama] = destinasi if destinasi else "Tidak diketahui"

    # Buat list untuk dropdown opsi Kapal
    list_opsi_kapal = ["Pilih Kapal..."] + list(mapping_kapal.keys())

    # Tabs
    tab_input, tab_reprint, tab_rekap = st.tabs(["✍️ INPUT", "🖨️ REPRINT", "📊 REKAP"])

    with tab_input:
        st.write("### Form Input Kendaraan")
        
        # Dropdown Kapal
        kapal_terpilih = st.selectbox("KAPAL BEROPERASI", list_opsi_kapal)
        
        # Logika pengisian otomatis NM_PORT_DEST
        if kapal_terpilih == "Pilih Kapal...":
            default_pelabuhan = "Otomatis terisi..."
        else:
            default_pelabuhan = mapping_kapal.get(kapal_terpilih, "Tidak diketahui")
            
        # Field Pelabuhan (Disabled agar tidak bisa diedit manual)
        pelabuhan = st.text_input("PELABUHAN TUJUAN", value=default_pelabuhan, disabled=True)
        
        plat_nomor = st.text_input("PLAT NOMOR KENDARAAN", placeholder="Contoh: L 1234 XY")
        golongan = st.selectbox("GOLONGAN / JENIS", ["Golongan I", "Golongan II", "Golongan III"])
        tipe_timbangan = st.radio("BERAT / TONASE (KG)", ["Manual", "Otomatis"], horizontal=True)
        berat = st.number_input("Input Berat", min_value=0)
        
        if st.button("🖨️ SIMPAN & CETAK TIKET", type="primary", use_container_width=True):
            if kapal_terpilih != "Pilih Kapal..." and plat_nomor:
                st.success(f"Data tiket {plat_nomor} untuk {kapal_terpilih} ({default_pelabuhan}) berhasil disimpan! (Dicatat oleh: **{st.session_state['user_aktif']}**)")
            else:
                st.error("Pastikan Kapal dan Plat Nomor sudah diisi.")

    with tab_reprint:
        st.write("### Cetak Ulang Tiket")
        search_plat = st.text_input("Cari Plat Nomor (Reprint)")
        if st.button("Cari & Reprint"):
            st.info(f"Mencari data historis untuk {search_plat}...")

    with tab_rekap:
        st.write("### Rekapitulasi Kegiatan Kapal")
        col1, col2 = st.columns(2)
        with col1:
            tanggal_kegiatan = st.date_input("Tanggal Kegiatan", datetime.today())
        with col2:
            nama_kapal_filter = st.selectbox("Filter Kapal Berkegiatan", ["Semua Kapal"] + list(mapping_kapal.keys()))

        st.info("Fitur rekap aktif. Integrasikan dengan database Anda untuk melihat data historis.")

# --- ROUTING ---
if st.session_state['authenticated']:
    show_main_app()
else:
    show_login_page()
