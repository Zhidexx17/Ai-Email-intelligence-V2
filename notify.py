import os
import sys
import math
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

# --- KONFIGURASI TESTING ---
# Ubah ke True jika ingin memaksa kirim Rekap Benefit/Task SEKARANG (walau bukan tanggal 5/10/15)
# Jangan lupa ubah ke False lagi nanti saat deploy!
FORCE_RECAP = True 

# 1. Load Environment
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

if not all([SUPABASE_URL, SUPABASE_KEY, LINE_TOKEN, LINE_USER_ID]):
    print("❌ Error: Pastikan kunci SUPABASE dan LINE lengkap di .env")
    sys.exit()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
line_bot_api = LineBotApi(LINE_TOKEN)

def get_indo_date():
    """Helper untuk format tanggal Indonesia (Contoh: 8 Januari 2026)"""
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    now = datetime.now()
    return f"{now.day} {months[now.month - 1]} {now.year}"

def mark_as_notified(email_ids):
    if not email_ids: return
    try:
        supabase.table("emails").update({"is_notified": True}).in_("id", email_ids).execute()
        print(f"   💾 DB Updated: {len(email_ids)} email ditandai 'sent'.")
    except Exception as e:
        print(f"   ⚠️ Gagal update DB: {e}")

def send_batched_messages(email_list, title_prefix="REKAP"):
    BATCH_SIZE = 5
    total_emails = len(email_list)
    total_batches = math.ceil(total_emails / BATCH_SIZE)
    date_str = get_indo_date() # Ambil tanggal format Indo

    print(f"   📦 Mengirim {total_emails} email dalam {total_batches} batch...")

    final_summary_msg = f"📋 **DAFTAR JUDUL & DEADLINE**\n📅 {date_str}\n"
    final_summary_msg += "----------------------------\n"

    for i in range(0, total_emails, BATCH_SIZE):
        batch = email_list[i : i + BATCH_SIZE]
        current_batch_num = (i // BATCH_SIZE) + 1
        
        # --- REVISI HEADER ---
        # Menambahkan Tanggal di bawah Judul
        message_text = f"📢 **{title_prefix} (Bagian {current_batch_num}/{total_batches})**\n"
        message_text += f"🗓️ {date_str}\n\n"
        
        batch_ids = []

        for idx, email in enumerate(batch, 1):
            real_number = i + idx
            
            icon = "🎁" if email['category'] == 'BENEFIT' else "📌"
            if email['category'] == 'URGENT': icon = "🚨"

            actions = email.get('action_items')
            saran_text = "-"
            if actions and isinstance(actions, list) and len(actions) > 0:
                saran_text = actions[0]
            
            # Format Pesan
            message_text += f"{real_number}. {icon} **{email['subject'][:40]}...**\n"
            message_text += f"   📝 {email.get('summary_text', '-')}\n"
            message_text += f"   👉 **Saran:** {saran_text}\n\n"
            
            # Susun Pesan Terakhir
            final_summary_msg += f"{real_number}. {email['subject'][:50]}\n"
            if email.get('deadline_date'):
                final_summary_msg += f"   📅 Deadline: {email['deadline_date']}\n"
            
            batch_ids.append(email['id'])

        try:
            line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message_text))
            print(f"   ✅ Batch {current_batch_num} terkirim.")
            mark_as_notified(batch_ids)
            time.sleep(1) 
        except LineBotApiError as e:
            print(f"   ❌ Gagal kirim Batch {current_batch_num}: {e}")

    # Kirim Pesan Terakhir
    try:
        final_summary_msg += "\nSemangat Rafly! 🔥"
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=final_summary_msg))
        print("   ✅ Pesan Ringkasan Akhir terkirim.")
    except LineBotApiError as e:
        print(f"   ❌ Gagal kirim Ringkasan Akhir: {e}")

def process_notifications():
    print("📢 Memulai Script Notifikasi...")
    today_date = datetime.now().day

    # 1. HANDLING URGENT (Selalu dicek tiap hari)
    urgents = supabase.table("emails") \
        .select("*") \
        .eq("category", "URGENT") \
        .eq("is_notified", False) \
        .execute().data

    if urgents:
        print(f"\n🚨 Ditemukan {len(urgents)} URGENT!")
        send_batched_messages(urgents, title_prefix="PERINGATAN URGENT")
    else:
        print("\n✅ Tidak ada info urgent baru.")

    # 2. HANDLING REKAP (BENEFIT & TASK)
    # Cek tanggal kelipatan 5 ATAU jika dipaksa pakai FORCE_RECAP
    is_recap_day = (today_date % 5 == 0) or FORCE_RECAP

    if is_recap_day:
        if FORCE_RECAP:
            print(f"\n⚠️ MODE TESTING AKTIF: Memaksa kirim rekap hari ini.")
        else:
            print(f"\n🎁 Hari ini tanggal {today_date} (Jadwal Rekap).")
        
        recaps = supabase.table("emails") \
            .select("*") \
            .in_("category", ["BENEFIT", "TASK"]) \
            .eq("is_notified", False) \
            .order("priority_score", desc=True) \
            .execute().data
            
        if recaps:
            send_batched_messages(recaps, title_prefix="REKAP INFO KAMPUS")
        else:
            print("   💤 Database kosong atau semua email sudah pernah dikirim (is_notified=True).")
            print("   💡 Tips: Set 'is_notified' jadi FALSE di Supabase kalau mau test kirim ulang.")
    else:
        print(f"\n🗓️ Hari ini tgl {today_date}. Bukan jadwal rekap (Tunggu tgl 5/10/15/..).")
        print("   Info BENEFIT/TASK disimpan di database dulu.")

if __name__ == "__main__":
    process_notifications()