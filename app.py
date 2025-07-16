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

# ─── Setup Logging ─────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worldcoin-bot")

# ─── Env Variables ─────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
REFERRAL_LINK = os.getenv("REFERRAL_LINK", "https://worldcoin.org/join/4RH0OTE")
HATA_WALLET_LINK = os.getenv("HATA_WALLET_LINK", "https://hata.io/signup?ref=HDX8778")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/cucikripto")
ADMIN_LINK = os.getenv("ADMIN_LINK", "https://t.me/JohanSetia")

# ─── Init App ──────────────────────────────────────────────
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
translator = Translator()

# ─── AI Characters ─────────────────────────────────────────
characters = {
    "Luna": {"desc": "comel bantu daftar dan claim Worldcoin", "model": "cypher-alpha:free"},
    "Azura": {"desc": "profesional urus Hata Wallet & transfer WLD", "model": "qwen/qwen3-30b-a3b:free"},
    "Pika": {"desc": "tegas bantu cashout ke bank tempatan", "model": "deepseek-chimera:free"},
    "Sophia": {"desc": "penasihat kripto global & Web3", "model": "google/gemma-7b-it:free"},
}

context_memory = {}

# ─── Flask Route ───────────────────────────────────────────
@app.route("/")
def home():
    return "✅ AiRoute-4X Worldcoin Chatbot is live."

@app.route("/health")
def health():
    return "ok"

# ─── NLP Detection ─────────────────────────────────────────
def detect_mood(text):
    if any(word in text.lower() for word in ["marah", "geram", "sakit hati"]):
        return "angry"
    elif any(word in text.lower() for word in ["sedih", "kecewa", "down"]):
        return "sad"
    elif any(word in text.lower() for word in ["gembira", "happy", "best"]):
        return "happy"
    return "neutral"

def detect_gender(text):
    if any(word in text.lower() for word in ["abang", "bro", "saya lelaki"]):
        return "male"
    elif any(word in text.lower() for word in ["kakak", "sis", "saya perempuan"]):
        return "female"
    return "unknown"

def detect_language(text):
    try:
        lang = detect(text)
        logger.info(f"[LogLang] Input language detected: {lang}")
        return lang
    except:
        return "ms"

def detect_character(text):
    text = text.lower()
    if any(w in text for w in ["claim", "daftar", "orbs", "worldcoin", "incentive"]):
        return "Luna"
    elif any(w in text for w in ["transfer", "wallet", "hata", "wld", "pindah"]):
        return "Azura"
    elif any(w in text for w in ["cashout", "bank", "keluar", "masuk", "myr", "duit"]):
        return "Pika"
    elif any(w in text for w in ["market", "harga", "pasaran", "bitcoin", "token"]):
        return "Sophia"
    return "Luna"

def reroute_if_needed(user_input, requested_char):
    detected = detect_character(user_input)
    if requested_char and requested_char != detected:
        return detected, f"🤖 Topik ini sesuai untuk {detected}. Saya serahkan kepada {detected} untuk membantu.\n"
    return detected, ""

# ─── AI Response ───────────────────────────────────────────
def get_ai_reply(user_input, character_name, user_id):
    char = characters.get(character_name)
    if not char:
        return "⚠️ Karakter tidak dijumpai."

    lang = detect_language(user_input)
    mood = detect_mood(user_input)
    gender = detect_gender(user_input)

    emoji = {"angry": "😠", "sad": "😢", "happy": "😊", "neutral": "🙂"}.get(mood, "🙂")
    gender_icon = {"male": "👦", "female": "👧", "unknown": "🧑"}.get(gender, "🧑")

    base_style = f"Kamu adalah {character_name}, AI {char['desc']} {gender_icon}."
    tone = f"Jawab ikut emosi pengguna {emoji}, ringkas & guna emoji."

    if character_name == "Pika" and mood == "angry":
        tone = "Jawab dengan tegas dan padat 💢"
    elif character_name == "Luna" and mood == "sad":
        tone = "Jawab lembut dan tenangkan pengguna 😢"
    elif character_name == "Azura" and gender == "female":
        tone = "Gaya sopan dan profesional 💼"

    system_msg = f"{base_style} {tone} Jangan sebut ** atau emoji secara lisan."

    if lang == "en":
        system_msg = translator.translate(system_msg, dest='en').text

    messages = [{"role": "system", "content": system_msg}]
    if user_id in context_memory:
        messages += context_memory[user_id][-2:]
    messages.append({"role": "user", "content": user_input})

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    data = {"model": f"openrouter/{char['model']}", "messages": messages}

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        reply = res.json()['choices'][0]['message']['content']
        context_memory[user_id] = messages[-1:]
        return reply
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "⚠️ Maaf, AI gagal menjawab. Cuba semula."

# ─── Text & Voice Balasan ─────────────────────────────────
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

# ─── Telegram Handlers ────────────────────────────────────
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("💰 Claim"),
        types.KeyboardButton("💸 Cashout"),
        types.KeyboardButton("📢 Channel"),
        types.KeyboardButton("👩‍💻 Admin"),
        types.KeyboardButton("👧 Luna"),
        types.KeyboardButton("🧕 Azura"),
        types.KeyboardButton("👮 Pika"),
        types.KeyboardButton("👩‍🏫 Sophia"),
        types.KeyboardButton("/reset")
    )
    welcome = (
        "🌟 Selamat datang ke *AiRoute-4X Worldcoin Chatbot*\n\n"
        "Saya terdiri daripada 4 AiBot wanita pintar:\n"
        "1. 👧 *Luna* – Daftar & Claim Worldcoin\n"
        "2. 🧕 *Azura* – Urus Wallet & Pindah\n"
        "3. 👮 *Pika* – Cashout ke Bank\n"
        "4. 👩‍🏫 *Sophia* – Pasaran Kripto\n\n"
        "Hantar teks, gambar, atau suara untuk mula."
    )
    bot.send_message(message.chat.id, welcome, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['reset'])
def reset_context(message):
    context_memory.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "🧹 Memori perbualan dibersihkan.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()

    quick_responses = {
        "👧 Luna": "👧 Saya *Luna*, AI comel bantu anda daftar dan claim Worldcoin ✨\nTanya saya sekarang!",
        "🧕 Azura": "🧕 Saya *Azura*, AI profesional urus wallet & transfer 💼",
        "👮 Pika": "👮 Saya *Pika*, AI tegas bantu cashout ke bank 💸",
        "👩‍🏫 Sophia": "👩‍🏫 Saya *Sophia*, penasihat kripto global 🌐",
        "💰 Claim": f"🪪 Daftar Worldcoin di sini:\n{REFERRAL_LINK}",
        "💸 Cashout": f"💸 Cashout WLD ke Hata:\n{HATA_WALLET_LINK}",
        "📢 Channel": f"📢 Sertai channel:\n{CHANNEL_LINK}",
        "👩‍💻 Admin": f"📬 Hubungi admin:\n{ADMIN_LINK}"
    }

    if text in quick_responses:
        bot.send_message(message.chat.id, quick_responses[text], parse_mode="Markdown")
        return

    # CoinGecko Price Checker
    if "harga" in text.lower() or "price" in text.lower():
        try:
            coins = ["bitcoin", "ethereum", "worldcoin"]
            res = requests.get(COINGECKO_API_URL, params={"ids": ",".join(coins), "vs_currencies": "myr"})
            data = res.json()
            harga = "\n".join([f"{coin.capitalize()}: RM {data[coin]['myr']}" for coin in coins])
            bot.send_message(message.chat.id, f"💹 Harga Pasaran:\n{harga}")
            return
        except Exception as e:
            logger.warning(f"[PriceError] {e}")
            bot.send_message(message.chat.id, "⚠️ Gagal semak harga kripto.")
            return

    detected_char, reroute_msg = reroute_if_needed(text, None)
    reply = get_ai_reply(text, detected_char, user_id)
    send_text_and_voice(message.chat.id, reroute_msg + reply)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        user_id = message.from_user.id
        file_info = bot.get_file(message.voice.file_id)
        voice_data = bot.download_file(file_info.file_path)
        ogg_path = f"voice_{uuid.uuid4()}.ogg"
        wav_path = ogg_path.replace(".ogg", ".wav")

        with open(ogg_path, 'wb') as f:
            f.write(voice_data)
        AudioSegment.from_ogg(ogg_path).export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="ms-MY")

        os.remove(ogg_path)
        os.remove(wav_path)

        detected_char, reroute_msg = reroute_if_needed(text, None)
        reply = get_ai_reply(text, detected_char, user_id)
        send_text_and_voice(message.chat.id, reroute_msg + reply)

    except Exception as e:
        logger.error(f"Voice error: {e}")
        bot.send_message(message.chat.id, "⚠️ Suara gagal diproses.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        user_id = message.from_user.id
        file_info = bot.get_file(message.photo[-1].file_id)
        photo_data = bot.download_file(file_info.file_path)
        img_path = f"img_{uuid.uuid4()}.jpg"

        with open(img_path, 'wb') as f:
            f.write(photo_data)

        with open(img_path, "rb") as img_file:
            headers = {"Authorization": f"Bearer {HF_API_KEY}"}
            res = requests.post("https://api-inference.huggingface.co/models/Salesforce/blip2-opt-2.7b", headers=headers, data=img_file)

        os.remove(img_path)
        result = res.json()
        caption = result[0]["generated_text"] if isinstance(result, list) else "Gambar tidak dapat dianalisis."
        lang = detect(caption)
        caption_ms = translator.translate(caption, dest='ms').text if lang != 'ms' else caption

        detected_char, reroute_msg = reroute_if_needed(caption_ms, None)
        reply = get_ai_reply(caption_ms, detected_char, user_id)
        send_text_and_voice(message.chat.id, reroute_msg + reply)

    except Exception as e:
        logger.error(f"Photo error: {e}")
        bot.send_message(message.chat.id, "⚠️ Gagal baca gambar.")

# ─── Main ──────────────────────────────────────────────────
if __name__ == "__main__":
    bot.remove_webhook()
    import threading
    def start_polling():
        try:
            logger.info("🤖 Telegram polling dimulakan...")
            bot.polling(non_stop=True, timeout=30)
        except Exception as e:
            logger.error(f"[PollingError] {e}")

    polling_thread = threading.Thread(target=start_polling)
    polling_thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
