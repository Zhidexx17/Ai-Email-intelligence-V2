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
       - Bahasa Indonesia, ringkas, padat.
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

    try:
    
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Request JSON Mode
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"} 
        )
        
        # Bersihkan hasil jika ada markdown ```json
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        
        parsed_json = json.loads(clean_text)
        return parsed_json

    except Exception as e:
        print(f"❌ Error AI: {e}")
        # Return fallback biar gak crash
        return {
            "category": "ERROR",
            "deadline_date": None,
            "priority_score": 0,
            "summary_text": "Gagal memproses AI",
            "action_items": []
        }