import os
import logging
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from ocr_utils import extract_text_from_image
from telegram import Update
from telegram.ext.callbackcontext import CallbackContext

# Logging (untuk debug bila deploy)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# API Keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Hai! Saya adalah AI Worldcoin Helper.\n\nHantar soalan atau gambar wallet awak, saya akan bantu claim & cashout ke Hata.")

def handle_text(update: Update, context: CallbackContext):
    user_input = update.message.text
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openrouter/cypher-alpha:free",
        "messages": [
            {"role": "system", "content": "Kamu adalah pembantu AI pakar dalam membantu pengguna claim dan withdraw Worldcoin ke wallet tempatan Malaysia."},
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        reply = response.json()['choices'][0]['message']['content']
    except Exception as e:
        reply = "⚠️ Maaf, sistem AI gagal balas. Sila cuba lagi nanti."

    update.message.reply_text(reply)

def handle_photo(update: Update, context: CallbackContext):
    photo = update.message.photo[-1]
    file = photo.get_file()
    file.download("temp.jpg")

    extracted_text = extract_text_from_image("temp.jpg")
    update.message.reply_text(f"📷 Gambar dibaca, teks ditemui:\n\n{extracted_text}")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
