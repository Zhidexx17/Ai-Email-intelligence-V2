import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load Environment
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Konfigurasi Gemini (Pakai Library Stabil)
if API_KEY:
    genai.configure(api_key=API_KEY)

# DAFTAR PRIORITAS MODEL (Berdasarkan screenshot kamu)
# Bot akan mencoba urutan dari atas ke bawah
MODELS_TO_TRY = [
    "gemini-2.5-flash",       # 1. Paling Pas (Limit 20/hari)
    "gemini-2.5-flash-lite",  # 2. Cadangan Ringan (Biasanya lebih hemat)
    "gemini-3-flash",         # 3. Cadangan Canggih
    "gemma-3-27b-it"          # 4. Cadangan Open Source (Jika ada)
]

def ask_ai_json(sender, subject, body_text):
    """
    Versi INTEGRASI DATABASE (JSON OUTPUT)
    Menggunakan logika prompt kamu, tapi outputnya Data yang bisa disimpan.
    """
    if not API_KEY:
        print("❌ Error: GEMINI_API_KEY belum di-set di .env")
        return None

    # Prompt yang sudah disesuaikan dengan keinginanmu tapi format JSON
    prompt = f"""
    Kamu adalah asisten mahasiswa UMN yang cerdas. Tugasmu mengekstrak informasi email.
    
    DATA EMAIL:
    - Pengirim: {sender}
    - Subjek: {subject}
    - Isi: {body_text}

    TUGAS ANALISIS (Cari Detail Ini):
    1. KLASIFIKASI (Category):
       - 'URGENT': Perubahan jadwal dadakan, pembatalan kelas, wajib hadir besok.
       - 'BENEFIT': Open Recruitment, Info SKKM, Lomba, Beasiswa, Magang.
       - 'TASK': Tugas kuliah, pengumpulan assignment.
       - 'NOISE': Berita umum, seminar tanpa benefit jelas, spam.
    
    2. DEADLINE: Cari tanggal tenggat waktu format YYYY-MM-DD. Jika tidak ada, null.
    
    3. RANGKUMAN (Summary):
       - Bahasa Indonesia, ringkas, singkat, padat.
       - Fokus: Apa untungnya buat mahasiswa? (SKKM/Honor/Sertifikat).
       - Sebutkan Syarat (Angkatan/Prodi) jika ada.
    
    4. ACTION ITEMS:
       - Langkah konkret: "Daftar di link...", "Kumpul tugas...", "Abaikan".

    OUTPUT WAJIB JSON (Jangan markdown):
    {{
        "category": "URGENT/BENEFIT/TASK/NOISE",
        "deadline_date": "YYYY-MM-DD" atau null,
        "priority_score": 1-5,
        "summary_text": "...",
        "action_items": ["...", "..."]
    }}
    """

    # --- LOOPING COBA MODEL ---
    for model_name in MODELS_TO_TRY:
        try:
            # print(f"   🤖 Mencoba model: {model_name}...") 
            # (Print dimatikan biar gak spam, nyalakan kalau mau debug)
            
            model = genai.GenerativeModel(model_name)
            
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"} 
            )
            
            # Jika berhasil sampai sini, berarti tidak error
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)

        except Exception as e:
            # Jika Error 429 (Limit Habis) atau lainnya, lanjut ke model berikutnya
            if "429" in str(e):
                print(f"   ⚠️ Kuota {model_name} HABIS! Mengalihkan ke cadangan...")
            else:
                print(f"   ⚠️ {model_name} Error: {e}. Mencoba cadangan...")
            
            # Lanjut ke iterasi loop berikutnya (Model selanjutnya)
            continue

    # --- JIKA SEMUA MODEL GAGAL ---
    print("❌ SEMUA MODEL GAGAL MERESPON.")
    return {
        "category": "ERROR",
        "deadline_date": None,
        "priority_score": 0,
        "summary_text": "Gagal memproses AI (Semua kuota habis)",
        "action_items": []
    }
