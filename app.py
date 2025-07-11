import os
import telebot
import requests
from ocr_utils import extract_text_from_image

# Ambil nilai dari environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
REFERRAL_LINK = os.getenv("REFERRAL_LINK", "https://worldcoin.org/join/4RH0OTE")
HATA_WALLET_LINK = os.getenv("HATA_WALLET_LINK", "https://hata.io/signup?ref=HDX8778")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, (
        "👋 Selamat datang ke AI Worldcoin Helper!\n\n"
        "📲 Bot ini bantu anda:\n"
        "✅ Claim Worldcoin dengan mudah\n"
        "✅ Pindahkan ke Wallet Hata (Malaysia)\n"
        "✅ Cashout ke bank tempatan 🇲🇾\n\n"
        f"🌐 Daftar Worldcoin (guna kod rujukan saya):\n👉 {REFERRAL_LINK}\n\n"
        f"💼 Daftar Wallet Hata (untuk withdraw):\n👉 {HATA_WALLET_LINK}\n\n"
        "📷 Hantar gambar wallet / teks jika anda perlukan bantuan!"
    ))

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
            {"role": "system", "content": "Kamu adalah pembantu AI pakar dalam bantu pengguna claim dan withdraw Worldcoin ke wallet tempatan Malaysia."},
            {"role": "user", "content": user_input}
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        reply = response.json()['choices'][0]['message']['content']
    except Exception as e:
        reply = "⚠️ Maaf, AI gagal membalas buat masa ini. Sila cuba lagi nanti."

    bot.reply_to(message, reply)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.jpg", 'wb') as f:
        f.write(downloaded_file)

    extracted_text = extract_text_from_image("temp.jpg")
    bot.reply_to(message, f"📷 Gambar telah dibaca. Ini teks yang dijumpai:\n\n{extracted_text}")

bot.polling()
