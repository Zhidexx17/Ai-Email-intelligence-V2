import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from ai_engine import ask_ai_json

# Setup
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: Kunci Supabase hilang.")
    exit()

supabase: Client = create_client(url, key)

def process_pending_emails():
    print("🤖 Memulai AI Processing...")
    
    # Ambil 10 email antrian
    response = supabase.table("emails") \
        .select("*") \
        .eq("category", "PENDING_AI") \
        .limit(10) \
        .execute()
    
    emails_to_process = response.data
    
    if not emails_to_process:
        print("✅ Tidak ada email antrian (Semua sudah bersih).")
        return

    print(f"📦 Ditemukan {len(emails_to_process)} email antrian.")

    # Loop Processing
    for email in emails_to_process:
        print(f"\n⚙️ Memproses: {email['subject'][:40]}...")
        
        # Panggil AI
        ai_result = ask_ai_json(
            sender=email['sender'], 
            subject=email['subject'], 
            body_text=email['body_snippet']
        )
        
        # Cek jika result kosong/error/limit habis
        if not ai_result or ai_result.get("category") == "ERROR":
            print("   ⚠️ Skip dulu (Error AI).")
            continue

        print(f"   🏷️ Kategori: {ai_result.get('category')}")
        print(f"   📝 Summary : {ai_result.get('summary_text')}")
        
        # Update Database
        update_data = {
            "category": ai_result.get("category", "Uncategorized"),
            "deadline_date": ai_result.get("deadline_date"),
            "priority_score": ai_result.get("priority_score", 1),
            "summary_text": ai_result.get("summary_text", "-"),
            "action_items": ai_result.get("action_items", [])
        }
        
        try:
            supabase.table("emails") \
                .update(update_data) \
                .eq("id", email['id']) \
                .execute()
            print("   ✅ Database Updated!")
        except Exception as e:
            print(f"   ❌ Gagal Update DB: {e}")
            
        # --- PENTING: JEDA DIPERLAMBAT ---
        # Limit Google: 5 Request / Menit = 1 request tiap 12 detik.
        print("   ⏳ Cooling down 20 detik...")
        time.sleep(20)

if __name__ == "__main__":
    process_pending_emails()
