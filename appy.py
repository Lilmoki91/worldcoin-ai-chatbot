import os
import telebot
import requests
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from ocr_utils import extract_text_from_image

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Teks permulaan
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, (
        "👋 Hai! Saya AI Worldcoin Helper.\n\n"
        "📷 Hantar gambar wallet, 🎤 hantar mesej suara, atau 💬 taip soalan.\n"
        "Saya bantu anda claim dan cashout Worldcoin ke Hata Wallet 🇲🇾.\n\n"
        "🌐 Daftar Worldcoin:\n👉 https://worldcoin.org/join/4RH0OTE\n"
        "💼 Daftar Hata Wallet:\n👉 https://hata.io/signup?ref=HDX8778"
    ))

# Mesej Teks
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_input = message.text
    ai_reply = get_ai_reply(user_input)
    send_text_and_voice(message.chat.id, ai_reply)

# Mesej Suara
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

    except Exception as e:
        bot.reply_to(message, "⚠️ Gagal proses mesej suara. Sila cuba semula.")

# Gambar
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.jpg", 'wb') as f:
        f.write(downloaded_file)

    extracted_text = extract_text_from_image("temp.jpg")
    bot.reply_to(message, f"📷 Gambar dibaca. Ini teks dijumpai:\n\n{extracted_text}")

# Fungsi AI OpenRouter
def get_ai_reply(user_input):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openrouter/cypher-alpha:free",
        "messages": [
            {"role": "system", "content": "Kamu pembantu AI untuk bantu pengguna claim & withdraw Worldcoin ke wallet Malaysia (Hata)."},
            {"role": "user", "content": user_input}
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception:
        return "⚠️ Maaf, AI gagal menjawab. Sila cuba sebentar lagi."

# Fungsi balas suara & teks
def send_text_and_voice(chat_id, text):
    bot.send_message(chat_id, text)
    tts = gTTS(text=text, lang='ms')
    tts.save("reply.mp3")
    audio = open("reply.mp3", 'rb')
    bot.send_voice(chat_id, audio)
    audio.close()

bot.polling()
