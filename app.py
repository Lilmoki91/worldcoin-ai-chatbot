import os
import uuid
import logging
import telebot
import requests
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from flask import Flask
from telebot import types
from ocr_utils import extract_text_from_image
from langdetect import detect
from googletrans import Translator

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worldcoin-bot")

# Load env variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
REFERRAL_LINK = os.getenv("REFERRAL_LINK", "https://worldcoin.org/join/4RH0OTE")
HATA_WALLET_LINK = os.getenv("HATA_WALLET_LINK", "https://hata.io/signup?ref=HDX8778")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/cucikripto")
ADMIN_LINK = os.getenv("ADMIN_LINK", "https://t.me/JohanSetia")

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
translator = Translator()

# Character & Model Mapping
characters = {
    "Luna": {
        "desc": "comel bantu daftar dan claim Worldcoin",
        "model": "cypher-alpha:free",
    },
    "Azura": {
        "desc": "profesional urus Hata Wallet & transfer WLD",
        "model": "qwen/qwen3-30b-a3b:free",
    },
    "Pika": {
        "desc": "tegas bantu cashout ke bank tempatan",
        "model": "deepseek-chimera:free",
    },
    "Sophia": {
        "desc": "penasihat kripto global & Web3",
        "model": "google/gemma-7b-it:free",
    },
}

context_memory = {}

@app.route("/")
def home():
    return "✅ Worldcoin AI Multi-Character Bot is alive!"

def detect_language(text):
    try:
        return detect(text)
    except:
        return "ms"

def get_ai_reply(user_input, character_name, user_id):
    char = characters.get(character_name)
    if not char:
        return "⚠️ Karakter tidak dijumpai."

    lang = detect_language(user_input)
    system_msg = f"Kamu adalah {character_name}, AI {char['desc']}. Jawab ringkas, mesra dan gunakan emoji. Jangan sebut ** atau emoji secara lisan."
    if lang == "en":
        system_msg = system_msg.replace("Jawab ringkas, mesra dan gunakan emoji", "Reply friendly and short with helpful tone and emojis")

    messages = [
        {"role": "system", "content": system_msg},
    ]

    if user_id in context_memory:
        messages += context_memory[user_id][-2:]

    messages.append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": f"openrouter/{char['model']}",
        "messages": messages,
    }

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        reply = res.json()['choices'][0]['message']['content']
        context_memory[user_id] = messages[-1:]
        return reply
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "⚠️ Maaf, AI gagal menjawab. Cuba semula."

def send_text_and_voice(chat_id, text):
    bot.send_message(chat_id, text)
    try:
        filename = f"reply_{uuid.uuid4()}.mp3"
        tts = gTTS(text=text, lang='ms')
        tts.save(filename)
        with open(filename, 'rb') as audio:
            bot.send_voice(chat_id, audio)
        os.remove(filename)
    except Exception as e:
        logger.warning(f"Voice error: {e}")
        bot.send_message(chat_id, "(Audio tidak dapat dihantar.)")

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🟣 Luna", "🔵 Azura")
    markup.row("🟡 Pika", "🟢 Sophia")
    markup.row("💰 Claim", "💸 Cashout")
    markup.row("📚 Rujukan", "📞 Bantuan Admin")
    bot.send_message(message.chat.id, "👋 Hai! Pilih pembantu AI anda atau tekan butang.", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "❓ Guna butang untuk pilih AI. Boleh taip atau hantar suara/gambar.")

@bot.message_handler(commands=['reset'])
def reset_context(message):
    context_memory.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ Konteks AI telah direset.")

@bot.message_handler(func=lambda msg: msg.text in ["💰 Claim"])
def claim_btn(message):
    bot.send_message(message.chat.id, f"🌐 Link daftar Worldcoin: {REFERRAL_LINK}")

@bot.message_handler(func=lambda msg: msg.text in ["💸 Cashout"])
def cashout_btn(message):
    bot.send_message(message.chat.id, f"💼 Daftar Hata Wallet: {HATA_WALLET_LINK}")

@bot.message_handler(func=lambda msg: msg.text == "📚 Rujukan")
def channel_info(message):
    bot.send_message(message.chat.id, f"📢 Channel Telegram: {CHANNEL_LINK}")

@bot.message_handler(func=lambda msg: msg.text == "📞 Bantuan Admin")
def contact_admin(message):
    bot.send_message(message.chat.id, f"🆘 Hubungi admin: {ADMIN_LINK}")

@bot.message_handler(func=lambda msg: msg.text and any(name.lower() in msg.text.lower() for name in characters))
def handle_character(message):
    for name in characters:
        if name.lower() in message.text.lower():
            reply = get_ai_reply(message.text, name, message.from_user.id)
            send_text_and_voice(message.chat.id, reply)
            break

@bot.message_handler(content_types=['text'])
def handle_text(message):
    reply = get_ai_reply(message.text, "Luna", message.from_user.id)
    send_text_and_voice(message.chat.id, reply)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded = bot.download_file(file_info.file_path)
        voice_file = f"voice_{uuid.uuid4()}.ogg"
        with open(voice_file, 'wb') as f:
            f.write(downloaded)
        wav_file = voice_file.replace(".ogg", ".wav")
        AudioSegment.from_ogg(voice_file).export(wav_file, format="wav")
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_file) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="ms-MY")
        os.remove(voice_file)
        os.remove(wav_file)
        handle_text(message)
    except Exception as e:
        logger.error(f"Voice error: {e}")
        bot.send_message(message.chat.id, "⚠️ Suara gagal diproses.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = f"img_{uuid.uuid4()}.jpg"
        with open(filename, 'wb') as f:
            f.write(downloaded)

        with open(filename, "rb") as img_file:
            headers = {
                "Authorization": f"Bearer {HF_API_KEY}"
            }
            res = requests.post(
                "https://api-inference.huggingface.co/models/Salesforce/blip2-opt-2.7b",
                headers=headers,
                data=img_file
            )

        os.remove(filename)

        result = res.json()
        caption = result[0]["generated_text"] if isinstance(result, list) else "Gambar tidak dapat dianalisis."

        detected_lang = detect(caption)
        caption_ms = translator.translate(caption, dest='ms').text if detected_lang != 'ms' else caption

        character = "Luna"
        if any(k in caption_ms.lower() for k in ["wallet hata", "transfer", "pindah"]):
            character = "Azura"
        elif any(k in caption_ms.lower() for k in ["cashout", "keluar", "bank"]):
            character = "Pika"
        elif any(k in caption_ms.lower() for k in ["market", "harga", "pasaran"]):
            character = "Sophia"

        reply = get_ai_reply(caption_ms, character, message.from_user.id)
        send_text_and_voice(message.chat.id, reply)

    except Exception as e:
        logger.error(f"BLIP2 Photo error: {e}")
        bot.send_message(message.chat.id, "⚠️ Gagal baca gambar atau sambungan BLIP2 gagal.")

@bot.message_handler(func=lambda msg: msg.text and "harga wld" in msg.text.lower())
def get_price(message):
    try:
        params = {
            "ids": "worldcoin",
            "vs_currencies": "myr"
        }
        res = requests.get(COINGECKO_API_URL, params=params)
        data = res.json()
        price = data['worldcoin']['myr']
        bot.send_message(message.chat.id, f"💰 Harga semasa Worldcoin (WLD): RM {price:.2f}")
    except Exception as e:
        logger.error(f"CoinGecko error: {e}")
        bot.send_message(message.chat.id, "⚠️ Gagal dapatkan harga semasa.")

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    bot.remove_webhook()
    import threading
    threading.Thread(target=bot.polling, kwargs={"timeout": 30, "non_stop": True}).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
