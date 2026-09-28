import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from auth import generate_otp, send_otp_whatsapp

# Konfigurasi Halaman (Wajib di baris pertama setelah import)
st.set_page_config(page_title="Sistem Timbangan RORO", layout="centered", page_icon="🚢")

# --- INISIALISASI SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'otp_terkirim' not in st.session_state:
    st.session_state['otp_terkirim'] = False
if 'otp_saat_ini' not in st.session_state:
    st.session_state['otp_saat_ini'] = ""

# --- HALAMAN LOGIN ---
def show_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #1E88E5;'>🔐 LOGIN PETUGAS</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Sistem Timbangan Manual RORO</p>", unsafe_allow_html=True)
            st.divider()

            no_wa = st.text_input("Nomor WhatsApp", placeholder="Contoh: 08123456789")
            
            if not st.session_state['otp_terkirim']:
                if st.button("Kirim OTP 📲", use_container_width=True):
                    if no_wa:
                        with st.spinner("Mengirim OTP..."):
                            otp = generate_otp()
                            sukses, pesan = send_otp_whatsapp(no_wa, otp)
                            
                            if sukses:
                                st.session_state['otp_saat_ini'] = otp
                                st.session_state['otp_terkirim'] = True
                                st.rerun()
                            else:
                                st.error(pesan)
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
                            st.rerun()
                        else:
                            st.error("Kode OTP Salah!")
                with col_b:
                    if st.button("Batal", use_container_width=True):
                        st.session_state['otp_terkirim'] = False
                        st.session_state['otp_saat_ini'] = ""
                        st.rerun()

# --- HALAMAN UTAMA ---
def show_main_app():
    # Header & Logout
    col_t, col_logout = st.columns([4, 1])
    with col_t:
        st.header("CETAK TIMBANGAN MANUAL RORO")
        st.subheader("Pelabuhan Tanjung Perak Surabaya")
    with col_logout:
        if st.button("🚪 Logout"):
            st.session_state['authenticated'] = False
            st.session_state['otp_terkirim'] = False
            st.rerun()
            
    st.divider()
    
    # Inisialisasi list kapal dari API (dengan fallback jika error)
    list_kapal = ["Pilih Kapal..."]
    try:
        url_api = "https://ptosr.pelindo.co.id/ScheduleBoard/GetData?kd_cabang=61&kd_terminal=601"
        response = requests.get(url_api, timeout=5)
        if response.status_code == 200:
            # Sesuaikan parsing JSON ini dengan struktur asli dari API Pelindo
            data_api = response.json() 
            # Contoh jika API merespon list: [{"NAMA_KAPAL": "KM A"}, {"NAMA_KAPAL": "KM B"}]
            if isinstance(data_api, list):
                kapal_dari_api = [item.get("NAMA_KAPAL", "") for item in data_api if "NAMA_KAPAL" in item]
                list_kapal.extend(list(set(kapal_dari_api)))
    except Exception:
        # Fallback jika WAF memblokir atau API mati
        list_kapal.extend(["KM Dharma Rucitra", "KM Kumala (Mock Data)"])

    # Tabs
    tab_input, tab_reprint, tab_rekap = st.tabs(["✍️ INPUT", "🖨️ REPRINT", "📊 REKAP"])

    # TAB 1: INPUT
    with tab_input:
        st.write("### Form Input Kendaraan")
        kapal = st.selectbox("KAPAL BEROPERASI", list_kapal)
        pelabuhan = st.text_input("PELABUHAN TUJUAN", value="Otomatis terisi...", disabled=True)
        plat_nomor = st.text_input("PLAT NOMOR KENDARAAN", placeholder="Contoh: L 1234 XY")
        golongan = st.selectbox("GOLONGAN / JENIS", ["Golongan I", "Golongan II", "Golongan III"])
        tipe_timbangan = st.radio("BERAT / TONASE (KG)", ["Manual", "Otomatis"], horizontal=True)
        berat = st.number_input("Input Berat", min_value=0)
        
        if st.button("🖨️ SIMPAN & CETAK TIKET", type="primary", use_container_width=True):
            if kapal != "Pilih Kapal..." and plat_nomor:
                st.success(f"Data tiket {plat_nomor} untuk {kapal} berhasil disimpan!")
                # Nantinya, logika INSERT ke backend (misalnya ke Supabase) diletakkan di sini
            else:
                st.error("Pastikan Kapal dan Plat Nomor sudah diisi.")

    # TAB 2: REPRINT
    with tab_reprint:
        st.write("### Cetak Ulang Tiket")
        search_plat = st.text_input("Cari Plat Nomor (Reprint)")
        if st.button("Cari & Reprint"):
            st.info(f"Mencari data historis untuk {search_plat}...")

    # TAB 3: REKAP
    with tab_rekap:
        st.write("### Rekapitulasi Kegiatan Kapal")
        col1, col2 = st.columns(2)
        with col1:
            tanggal_kegiatan = st.date_input("Tanggal Kegiatan", datetime.today())
        with col2:
            filter_opsi = ["Semua Kapal"] + [k for k in list_kapal if k != "Pilih Kapal..."]
            nama_kapal_filter = st.selectbox("Filter Kapal Berkegiatan", filter_opsi)

        # Mock Data (Nanti diganti dengan fetch (SELECT) dari database Supabase/MySQL Anda)
        data_mock = {
            "KD_JADWAL": ["JDW001", "JDW001", "JDW002"],
            "NAMA_KAPAL": ["KM Dharma Rucitra", "KM Dharma Rucitra", "KM Kumala (Mock Data)"],
            "TANGGAL": ["2026-09-28", "2026-09-28", "2026-09-28"],
            "PLAT_NOMOR": ["L 1234 XY", "W 5678 Z", "B 9999 AA"],
            "GOLONGAN": ["Golongan I", "Golongan II", "Golongan I"],
            "BERAT_KG": [1200, 2500, 1100]
        }
        df_rekap = pd.DataFrame(data_mock)
        
        # Logika Filter
        if nama_kapal_filter != "Semua Kapal":
            df_rekap = df_rekap[df_rekap["NAMA_KAPAL"] == nama_kapal_filter]
        
        st.dataframe(df_rekap, use_container_width=True, hide_index=True)
        
        # Ekspor CSV
        st.download_button(
            label="📥 Download Rekap (CSV)",
            data=df_rekap.to_csv(index=False).encode('utf-8'),
            file_name=f"Rekap_{tanggal_kegiatan.strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )

# --- ROUTING ---
if st.session_state['authenticated']:
    show_main_app()
else:
    show_login_page()
