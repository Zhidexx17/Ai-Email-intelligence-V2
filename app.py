import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from supabase import create_client, Client
from dotenv import load_dotenv

# Load Env (Hanya untuk lokal, nanti di Render diset di dashboard)
load_dotenv()

app = Flask(__name__)

# Kunci Rahasia
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET") # <--- KITA BUTUH INI BARU
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([LINE_TOKEN, LINE_SECRET, SUPABASE_URL, SUPABASE_KEY]):
    print("⚠️ Warning: Environment variable belum lengkap.")

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. ROUTE WEBHOOK (Pintu Masuk LINE)
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
    reply_text = ""

    # --- LOGIKA QUERY SUPABASE ---
    category_filter = None
    title = ""
    
    # 1. INFO SKKM & BENEFIT
    if user_msg in ["skkm", "benefit", "lomba", "beasiswa", "poin"]:
        category_filter = "BENEFIT"
        title = "🎁 INFO SKKM & BENEFIT"

    # 2. TUGAS & DEADLINE
    elif user_msg in ["tugas", "deadline", "pr", "task", "ujian"]:
        category_filter = "TASK"
        title = "📌 DAFTAR TUGAS & UJIAN"

    # 3. INFO URGENT (Wajib Lapor/Hadir)
    elif user_msg in ["urgent", "penting", "darurat", "batal"]:
        category_filter = "URGENT"
        title = "🚨 INFO URGENT/PENTING"

    # 4. BERITA UMUM (Update Baru Disini!) 
    # Menangkap kata "info", "berita", "pengumuman", "kabar"
    # Mengambil kategori 'NOISE' (Berita Kampus/Umum)
    elif user_msg in ["info", "berita", "news", "kabar", "pengumuman"]:
        category_filter = "NOISE" 
        title = "📰 BERITA & PENGUMUMAN KAMPUS"

    # 5. MENU BANTUAN
    elif user_msg == "help":
        reply_text = (
            "🤖 **Menu Bot UMN**\n\n"
            "Ketik kata kunci ini:\n"
            "- 'skkm'   : Cari info poin, lomba, beasiswa\n"
            "- 'tugas'  : Cek tugas & deadline\n"
            "- 'urgent' : Cek perubahan jadwal/info darurat\n"
            "- 'info'   : Cek berita kampus & pengumuman umum"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    # EKSEKUSI DATABASE
    if category_filter:
        # Ambil 5 email terbaru dari kategori tersebut
        data = supabase.table("emails") \
            .select("*") \
            .eq("category", category_filter) \
            .order("received_at", desc=True) \
            .limit(5) \
            .execute().data
        
        if data:
            reply_text = f"{title}\n----------------\n"
            for i, email in enumerate(data, 1):
                # Judul
                reply_text += f"{i}. {email['subject'][:50]}...\n"
                # Summary
                reply_text += f"   📝 {email.get('summary_text', 'Cek email')}\n"
                # Tanggal (Jika ada deadline/acara)
                if email.get('deadline_date'):
                    reply_text += f"   📅 Tgl: {email['deadline_date']}\n"
                reply_text += "\n"
            
            # Footer manis
            reply_text += "Ketik 'help' untuk menu lain."
        else:
            reply_text = f"📭 Belum ada email terbaru di kategori: {title}."
    
    else:
        # Default response jika tidak mengerti
        reply_text = "Maaf, saya tidak mengerti. Ketik 'help' untuk melihat menu."

    # Kirim Balasan
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# Jalankan Server (Hanya utk lokal)
if __name__ == "__main__":
    app.run(port=5000)