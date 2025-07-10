import os
import telebot
import requests
from ocr_utils import extract_text_from_image

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hai! Saya adalah AI Worldcoin Helper.\n\nHantar soalan atau gambar wallet awak, saya akan bantu claim & cashout ke Hata.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_input = message.text
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
        reply = "Maaf, sistem AI gagal balas. Sila cuba lagi nanti."

    bot.reply_to(message, reply)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.jpg", 'wb') as f:
        f.write(downloaded_file)

    extracted_text = extract_text_from_image("temp.jpg")
    bot.reply_to(message, f"📷 Gambar dibaca, teks ditemui:\n\n{extracted_text}")

bot.polling()
