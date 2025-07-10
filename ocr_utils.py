import pytesseract
from PIL import Image

def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='eng')
        return text.strip()
    except Exception as e:
        return "❌ Gagal membaca gambar. Pastikan ia jelas dan sah."
