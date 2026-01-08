import os
import sys
from datetime import date, timedelta
from dotenv import load_dotenv
from imap_tools import MailBox, AND
from supabase import create_client, Client
from bs4 import BeautifulSoup  # Library pembersih HTML

# 1. Load Environment Variables
load_dotenv()

email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("EMAIL_PASS")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not all([email_user, email_pass, supabase_url, supabase_key]):
    print("❌ Error: Pastikan semua kunci di .env sudah diisi!")
    sys.exit()

print("🔌 Menghubungkan ke Supabase...")
supabase: Client = create_client(supabase_url, supabase_key)

# --- KONFIGURASI ---
# Menambahkan "no-reply" ke daftar blacklist
IGNORED_SENDERS = ["noreply@elearning.umn.ac.id", "do-not-reply", "google-classroom", "no-reply"]
IGNORED_SUBJECTS = ["You have submitted", "Submission receipt", "Attendance"]
FETCH_LIMIT = 12 #Limit Email Reader
DAYS_BACK = 1

def clean_email_body(html_content):
    """Fungsi untuk membuang tag HTML dan menyisakan teks bacaan saja."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    # get_text dengan separator spasi agar kata-kata tidak menempel
    text = soup.get_text(separator="\n", strip=True)
    return text

def process_emails():
    print("📩 Sedang login ke Email...")
    
    # Hitung tanggal batas (Hanya ambil mulai dari 3 hari lalu)
    today = date.today()
    start_date = today - timedelta(days=DAYS_BACK)
    
    try:
        with MailBox('imap.gmail.com').login(email_user, email_pass) as mailbox:
            print(f"🔎 Mencari email sejak {start_date} (Max {FETCH_LIMIT} email)...")
            
            # Kriteria Filter Server:
            # 1. date_gte = Tanggal lebih besar atau sama dengan start_date (3 hari lalu)
            criteria = AND(date_gte=start_date)
            
            # Fetch email
            emails = mailbox.fetch(criteria, reverse=True, limit=FETCH_LIMIT, mark_seen=True)
            
            count_processed = 0
            count_skipped_db = 0
            count_skipped_spam = 0
            
            for msg in emails:
                email_uid = msg.uid
                subject = msg.subject
                sender = msg.from_

                # --- 1. FILTER BLACKLIST ---
                if any(blocked in sender.lower() for blocked in IGNORED_SENDERS) or \
                   any(blocked in subject for blocked in IGNORED_SUBJECTS):
                    print(f"   🚫 Skip Blacklist: {subject[:30]}...")
                    count_skipped_spam += 1
                    continue

                # --- 2. CEK DUPLIKAT DB ---
                existing = supabase.table("emails").select("id").eq("email_uid", email_uid).execute()
                if existing.data:
                    print(f"   ⏩ Skip Duplikat DB: {subject[:30]}...")
                    count_skipped_db += 1
                    continue
                
                # --- 3. PEMBERSIHAN DATA (HTML CLEANING) ---
                # Prioritas 1: Ambil msg.text (Biasanya sudah polos)
                # Prioritas 2: Ambil msg.html lalu bersihkan pakai BeautifulSoup
                raw_body = msg.text if msg.text else clean_email_body(msg.html)
                
                # Bersihkan spasi ganda & enter berlebihan
                clean_body = " ".join(raw_body.split()) 
                
                # Potong max 2500 karakter
                body_final = clean_body[:2500]
                
                new_email = {
                    "email_uid": email_uid,
                    "sender": sender,
                    "subject": subject,
                    "body_snippet": body_final, 
                    "received_at": msg.date.isoformat(),
                    "category": "PENDING_AI",
                    "summary_text": "Menunggu antrian AI..."
                }
                
                # --- 4. INSERT ---
                try:
                    supabase.table("emails").insert(new_email).execute()
                    print(f"   ✅ INSERT: {subject[:30]}...")
                    count_processed += 1
                except Exception as e:
                    print(f"   ❌ Gagal simpan DB: {e}")

            print("\n" + "="*30)
            print(f"📊 Laporan Selesai:")
            print(f"   - Masuk DB (Bersih) : {count_processed}")
            print(f"   - Dibuang (Spam)    : {count_skipped_spam}")
            print(f"   - Dibuang (Duplikat): {count_skipped_db}")
            print("="*30)

    except Exception as e:
        print(f"❌ Error IMAP: {e}")

if __name__ == "__main__":
    process_emails()