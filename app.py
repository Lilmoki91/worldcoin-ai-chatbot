import os
import telebot
import requests
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from flask import Flask
from ocr_utils import extract_text_from_image

# Dapatkan token dari environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Flask app untuk UptimeRobot
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Worldcoin AI Bot is alive!"

# Fungsi utama AI dari OpenRouter
def get_ai_reply(user_input):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openrouter/cypher-alpha:free",
        "messages": [
            {
                "role": "system",
                "content": "Kamu pembantu AI untuk bantu pengguna claim dan withdraw Worldcoin ke wallet Malaysia seperti Hata."
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception:
        return "⚠️ Maaf, AI gagal menjawab. Sila cuba sebentar lagi."

# Fungsi TTS balas suara
def send_text_and_voice(chat_id, text):
    bot.send_message(chat_id, text)
    try:
        tts = gTTS(text=text, lang='ms')
        tts.save("reply.mp3")
        audio = open("reply.mp3", 'rb')
        bot.send_voice(chat_id, audio)
        audio.close()
    except Exception:
        bot.send_message(chat_id, "⚠️ Gagal hantar suara, hanya hantar teks sahaja.")

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, (
        "👋 Hai! Saya AI Worldcoin Helper.\n\n"
        "📷 Hantar gambar wallet, 🎤 mesej suara, atau 💬 taip soalan.\n"
        "Saya bantu anda claim & cashout Worldcoin ke Hata Wallet 🇲🇾.\n\n"
        "🌐 Daftar Worldcoin:\n👉 https://worldcoin.org/join/4RH0OTE\n"
        "💼 Daftar Wallet Hata:\n👉 https://hata.io/signup?ref=HDX8778"
    ))

# Teks biasa
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_input = message.text
    ai_reply = get_ai_reply(user_input)
    send_text_and_voice(message.chat.id, ai_reply)

# Mesej suara
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        ogg_path = "voice.ogg"
        wav_path = "voice.wav"

        with open(ogg_path, 'wb') as f:
            f.write(downloaded_file)

        sound = AudioSegment.from_ogg(ogg_path)
        sound.export(wav_path, format="wav")

        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
            user_input = r.recognize_google(audio, language="ms-MY")

        ai_reply = get_ai_reply(user_input)
        send_text_and_voice(message.chat.id, ai_reply)

    except Exception:
        bot.send_message(message.chat.id, "⚠️ Gagal proses suara. Sila hantar semula.")

# Mesej gambar
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp.jpg", 'wb') as f:
            f.write(downloaded_file)

        extracted_text = extract_text_from_image("temp.jpg")
        bot.send_message(message.chat.id, f"📷 Gambar dibaca. Teks dijumpai:\n\n{extracted_text}")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Gagal baca gambar. Sila cuba lagi.")

# Jalankan Flask + Bot serentak
if __name__ == "__main__":
    import threading
    bot_thread = threading.Thread(target=bot.polling)
    bot_thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
