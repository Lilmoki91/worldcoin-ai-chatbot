import os
import telebot
import requests
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from flask import Flask
from telebot import types
from ocr_utils import extract_text_from_image

# Ambil data dari environment variable
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
REFERRAL_LINK = os.getenv("REFERRAL_LINK", "https://worldcoin.org/join/4RH0OTE")
HATA_WALLET_LINK = os.getenv("HATA_WALLET_LINK", "https://hata.io/signup?ref=HDX8778")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Worldcoin AI Bot is alive!"

def get_ai_reply(user_input):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen/qwen3-30b-a3b:free",
        "messages": [
            {
                "role": "system",
                "content": "Kamu pembantu AI comel dan mesra. Bantu pengguna claim dan cashout Worldcoin ke wallet Hata Malaysia. Tambah emoji bila sesuai, tapi jangan guna ** atau sebut emoji."
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    }
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return res.json()['choices'][0]['message']['content']
    except:
        return "⚠️ Maaf, AI gagal menjawab. Sila cuba sebentar lagi."

def send_text_and_voice(chat_id, text):
    bot.send_message(chat_id, text)
    try:
        tts = gTTS(text=text, lang='ms')
        tts.save("reply.mp3")
        with open("reply.mp3", 'rb') as audio:
            bot.send_voice(chat_id, audio)
    except:
        bot.send_message(chat_id, "⚠️ Gagal hantar suara, hanya hantar teks sahaja.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💰 Claim", "💸 Cashout")
    markup.row("📚 Channel Info", "📞 Hubungi Admin")

    welcome = (
        "👋 Hai! Saya AI Worldcoin Helper comel anda ✨\n\n"
        "📷 Hantar gambar wallet, 🎤 mesej suara, atau 💬 taip soalan.\n"
        "Saya bantu anda claim & cashout Worldcoin ke Hata Wallet 🇲🇾.\n\n"
        f"🌐 Daftar Worldcoin: 👉 {REFERRAL_LINK}\n"
        f"💼 Daftar Wallet Hata: 👉 {HATA_WALLET_LINK}"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "💰 Claim")
def handle_claim(message):
    bot.send_message(message.chat.id, "🪪 Untuk claim Worldcoin:\n1. Buka app World App.\n2. Tekan 'Verify now'.\n3. Imbas iris mata di orb station berdekatan.\n\n🌐 Link daftar: " + REFERRAL_LINK)

@bot.message_handler(func=lambda msg: msg.text == "💸 Cashout")
def handle_cashout(message):
    bot.send_message(message.chat.id, "💸 Untuk cashout ke Malaysia:\n1. Buka World App.\n2. Transfer WLD ke wallet Hata.\n3. Tukar ke MYR dan pindah ke bank anda.\n\n🔗 Daftar Hata Wallet: " + HATA_WALLET_LINK)

@bot.message_handler(func=lambda msg: msg.text == "📚 Channel Info")
def handle_info(message):
    bot.send_message(message.chat.id, "📢 Channel info & tips:\n👉 https://t.me/cucikripto")

@bot.message_handler(func=lambda msg: msg.text == "📞 Hubungi Admin")
def handle_admin(message):
    bot.send_message(message.chat.id, "📞 Anda boleh hubungi admin bot di Telegram: @JohanSetia")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    ai_reply = get_ai_reply(message.text)
    send_text_and_voice(message.chat.id, ai_reply)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("voice.ogg", 'wb') as f:
            f.write(downloaded_file)

        AudioSegment.from_ogg("voice.ogg").export("voice.wav", format="wav")
        recognizer = sr.Recognizer()
        with sr.AudioFile("voice.wav") as source:
            audio = recognizer.record(source)
            user_input = recognizer.recognize_google(audio, language="ms-MY")

        ai_reply = get_ai_reply(user_input)
        send_text_and_voice(message.chat.id, ai_reply)
    except:
        bot.send_message(message.chat.id, "⚠️ Gagal proses suara. Sila cuba semula.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("screenshot.jpg", 'wb') as f:
            f.write(downloaded_file)

        extracted = extract_text_from_image("screenshot.jpg")
        bot.send_message(message.chat.id, f"📸 Gambar dibaca. Teks dijumpai:\n\n{extracted}")
        ai_reply = get_ai_reply(extracted)
        send_text_and_voice(message.chat.id, ai_reply)
    except:
        bot.send_message(message.chat.id, "⚠️ Gagal baca gambar. Sila cuba lagi.")

# Mulakan polling bot di thread berasingan supaya Gunicorn tetap berjalan
import threading
bot.remove_webhook()
threading.Thread(target=bot.polling, kwargs={"timeout": 30, "non_stop": True}).start()
