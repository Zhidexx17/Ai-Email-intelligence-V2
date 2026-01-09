import os
import math
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from supabase import create_client, Client
from dotenv import load_dotenv

# Load Env (Hanya untuk lokal, di PythonAnywhere dibaca via WSGI)
load_dotenv()

app = Flask(__name__)

# Kunci Rahasia
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([LINE_TOKEN, LINE_SECRET, SUPABASE_URL, SUPABASE_KEY]):
    print("Warning: Environment variable")

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. ROUTE WEBHOOK
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 2. LOGIKA JAWAB PESAN
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.lower().strip()
    
    # --- LOGIKA KATEGORI ---
    category_filter = None
    title = ""
    
    # Keyword Mapping
    if user_msg in ["skkm", "benefit", "lomba", "beasiswa", "poin"]:
        category_filter = "BENEFIT"
        title = "🎁 INFO SKKM & BENEFIT"
    elif user_msg in ["tugas", "deadline", "pr", "task", "ujian"]:
        category_filter = "TASK"
        title = "📌 DAFTAR TUGAS & UJIAN"
    elif user_msg in ["urgent", "penting", "darurat", "batal"]:
        category_filter = "URGENT"
        title = "🚨 INFO URGENT/PENTING"
    elif user_msg in ["info", "berita", "news", "kabar", "pengumuman"]:
        category_filter = "NOISE" 
        title = "📰 BERITA & PENGUMUMAN"
    elif user_msg == "help":
        help_text = (
            "🤖 **Menu Bot UMN**\n\n"
            "Ketik kata kunci ini:\n"
            "- 'skkm'   : Info poin & lomba (2 minggu terakhir)\n"
            "- 'tugas'  : Deadline tugas (2 minggu terakhir)\n"
            "- 'urgent' : Info darurat\n"
            "- 'info'   : Berita kampus"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))
        return

    # --- EKSEKUSI DATABASE ---
    if category_filter:
        # 1. Hitung Tanggal 14 Hari Lalu
        two_weeks_ago = (datetime.now() - timedelta(days=14)).isoformat()
        
        # 2. Query dengan Filter Waktu & Limit lebih besar (15)
        response = supabase.table("emails") \
            .select("*") \
            .eq("category", category_filter) \
            .gte("received_at", two_weeks_ago) \
            .order("received_at", desc=True) \
            .limit(15) \
            .execute()
        
        data = response.data
        
        if data:
            # --- LOGIKA BATCHING (Pecah Pesan) ---
            # LINE reply token bisa kirim max 5 balon chat sekaligus.
            # Kita akan pecah: 1 balon chat isi max 5 email.
            messages_to_send = []
            BATCH_SIZE = 5
            
            # Loop per pecahan 5 data
            for i in range(0, len(data), BATCH_SIZE):
                batch = data[i : i + BATCH_SIZE]
                current_part = (i // BATCH_SIZE) + 1
                total_parts = math.ceil(len(data) / BATCH_SIZE)
                
                # Header per balon
                reply_text = f"{title} (Part {current_part}/{total_parts})\n"
                reply_text += "----------------\n"
                
                for idx, email in enumerate(batch, 1):
                    # Nomor urut global (misal 1, 2... lalu 6, 7...)
                    real_idx = i + idx
                    
                    reply_text += f"{real_idx}. {email['subject'][:40]}...\n"
                    reply_text += f"   📝 {email.get('summary_text', '-')}\n"
                    if email.get('deadline_date'):
                        reply_text += f"   📅 {email['deadline_date']}\n"
                    reply_text += "\n"
                
                # Masukkan text yang sudah jadi ke daftar kirim
                messages_to_send.append(TextSendMessage(text=reply_text))
            
            # Kirim semua balon chat sekaligus (Max 5 balon)
            line_bot_api.reply_message(event.reply_token, messages_to_send)
            
        else:
            fallback_msg = f"📭 Tidak ada info {category_filter} dalam 14 hari terakhir."
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=fallback_msg))
    
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Maaf, ketik 'help' untuk menu."))

# Jalankan Server
if __name__ == "__main__":
    app.run()
