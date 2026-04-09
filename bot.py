import os
import datetime
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
GOOGLE_SHEET_NAME = os.environ["GOOGLE_SHEET_NAME"]
GOOGLE_CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    GOOGLE_CREDENTIALS_FILE,
    scopes=SCOPES
)
gc = gspread.authorize(creds)
sheet = gc.open(GOOGLE_SHEET_NAME).sheet1

user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kütüphane botuna hoş geldin 📚\n/ekle /liste /ara")

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

        sheet.append_row([
            str(int(datetime.datetime.now().timestamp())),
            state["kitap"],
            state["yazar"],
            state["kategori"],
            "Evde",
            "",
            "",
            datetime.datetime.now().strftime("%Y-%m-%d")
        ])

        await update.message.reply_text("Kitap eklendi ✅")
        user_state.pop(user_id, None)

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

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ekle", ekle))
app.add_handler(CommandHandler("liste", liste))
app.add_handler(CommandHandler("ara", ara))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
