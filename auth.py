import requests
import random
import streamlit as st

def generate_otp():
    """Menghasilkan 6 digit angka acak untuk OTP"""
    return str(random.randint(100000, 999999))

def send_otp_whatsapp(phone_number, otp_code):
    """Mengirim pesan OTP ke nomor WhatsApp menggunakan API Watzap"""
    
    # Format nomor: memastikan menggunakan kode negara 62
    if phone_number.startswith("0"):
        phone_number = "62" + phone_number[1:]
        
    payload = {
        "api_key": st.secrets["WATZAP_API_KEY"],
        "number_key": st.secrets["WATZAP_NUMBER_KEY"],
        "phone_no": phone_number,
        "message": f"*[SISTEM TIMBANGAN RORO]*\n\nKode OTP Anda adalah: *{otp_code}*\n\n_Harap tidak memberikan kode ini kepada siapapun._"
    }
    
    try:
        response = requests.post(st.secrets["WATZAP_API_URL"], json=payload)
        
        # Validasi respon API
        if response.status_code == 200:
            return True, "OTP berhasil dikirim."
        else:
            return False, f"Gagal mengirim. Respon API: {response.text}"
    except Exception as e:
        return False, f"Terjadi kesalahan koneksi: {e}"
