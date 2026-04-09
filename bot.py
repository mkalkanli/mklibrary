from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from google.oauth2.service_account import Credentials
import datetime

# Google Sheets bağlantı
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Kutuphane").sheet1

# Geçici kullanıcı state
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kütüphane botuna hoş geldin 📚\n/ekle /ara /liste")

async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = {"step": "kitap"}
    await update.message.reply_text("Kitap adı?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_state:
        return

    state = user_state[user_id]

    if state["step"] == "kitap":
        state["kitap"] = update.message.text
        state["step"] = "yazar"
        await update.message.reply_text("Yazar?")
        return

    if state["step"] == "yazar":
        state["yazar"] = update.message.text
        state["step"] = "kategori"
        await update.message.reply_text("Kategori?")
        return

    if state["step"] == "kategori":
        state["kategori"] = update.message.text

        # Google Sheets'e ekle
        sheet.append_row([
            str(datetime.datetime.now().timestamp()),
            state["kitap"],
            state["yazar"],
            state["kategori"],
            "Evde",
            "",
            "",
            datetime.datetime.now().strftime("%Y-%m-%d")
        ])

        await update.message.reply_text("Kitap eklendi ✅")
        user_state.pop(user_id)

async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sheet.get_all_values()[1:]

    if not rows:
        await update.message.reply_text("Kütüphane boş")
        return

    mesaj = ""
    for r in rows[:10]:
        mesaj += f"📖 {r[1]} - {r[2]}\n"

    await update.message.reply_text(mesaj)

async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).lower()
    rows = sheet.get_all_values()[1:]

    sonuc = [r for r in rows if query in r[1].lower()]

    if not sonuc:
        await update.message.reply_text("Bulunamadı")
        return

    mesaj = ""
    for r in sonuc:
        mesaj += f"📖 {r[1]} - {r[2]}\n"

    await update.message.reply_text(mesaj)

app = ApplicationBuilder().token("BOT_TOKEN").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ekle", ekle))
app.add_handler(CommandHandler("liste", liste))
app.add_handler(CommandHandler("ara", ara))
app.add_handler(MessageHandler(filters.TEXT, handle_message))

app.run_polling()
