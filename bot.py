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

client = gspread.authorize(creds)
sheet = client.open(GOOGLE_SHEET_NAME).sheet1

user_state = {}


def ensure_header():
    rows = sheet.get_all_values()
    if not rows:
        sheet.append_row([
            "ID",
            "Kitap Adı",
            "Yazar",
            "Kategori",
            "Durum",
            "Raf",
            "Not",
            "Tarih"
        ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kütüphane botuna hoş geldin 📚\n\n"
        "Komutlar:\n"
        "/ekle\n"
        "/liste\n"
        "/ara kitap_adi"
    )


async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = {"step": "kitap"}
    await update.message.reply_text("Kitap adı?")


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sheet.get_all_values()

    if len(rows) <= 1:
        await update.message.reply_text("Kütüphane boş.")
        return

    data = rows[1:]
    mesajlar = []

    for row in data[:20]:
        kitap = row[1] if len(row) > 1 else ""
        yazar = row[2] if len(row) > 2 else ""
        durum = row[4] if len(row) > 4 else ""
        mesajlar.append(f"📖 {kitap} - {yazar} [{durum}]")

    await update.message.reply_text("\n".join(mesajlar))


async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip().lower()

    if not query:
        await update.message.reply_text("Örnek kullanım:\n/ara simyacı")
        return

    rows = sheet.get_all_values()

    if len(rows) <= 1:
        await update.message.reply_text("Kayıt yok.")
        return

    data = rows[1:]
    sonuc = []

    for row in data:
        kitap = row[1] if len(row) > 1 else ""
        yazar = row[2] if len(row) > 2 else ""

        if query in kitap.lower() or query in yazar.lower():
            sonuc.append(f"📖 {kitap} - {yazar}")

    if not sonuc:
        await update.message.reply_text("Bulunamadı.")
        return

    await update.message.reply_text("\n".join(sonuc[:20]))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_state:
        return

    state = user_state[user_id]
    text = update.message.text.strip()

    if state["step"] == "kitap":
        state["kitap"] = text
        state["step"] = "yazar"
        await update.message.reply_text("Yazar?")
        return

    if state["step"] == "yazar":
        state["yazar"] = text
        state["step"] = "kategori"
        await update.message.reply_text("Kategori?")
        return

    if state["step"] == "kategori":
        state["kategori"] = text

        yeni_id = str(int(datetime.datetime.now().timestamp()))
        tarih = datetime.datetime.now().strftime("%Y-%m-%d")

        sheet.append_row([
            yeni_id,
            state["kitap"],
            state["yazar"],
            state["kategori"],
            "Evde",
            "",
            "",
            tarih
        ])

        await update.message.reply_text("Kitap eklendi ✅")
        user_state.pop(user_id, None)


def main():
    ensure_header()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
