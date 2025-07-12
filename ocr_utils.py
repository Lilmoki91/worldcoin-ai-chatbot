import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

def extract_text_from_image(image_path):
    try:
        # Buka gambar dan convert ke grayscale
        img = Image.open(image_path).convert("L")

        # Tajamkan imej supaya lebih jelas untuk OCR
        img = img.filter(ImageFilter.SHARPEN)

        # Jalankan OCR dengan sokongan Bahasa Inggeris + Melayu
        text = pytesseract.image_to_string(img, lang='eng+msa').strip()

        # Jika tiada teks dikesan, pulangkan mesej amaran
        if not text:
            return "⚠️ Tiada teks dikesan dalam gambar. Sila pastikan gambar jelas dan terang."

        return text

    except Exception as e:
        return f"❌ Gagal membaca gambar. Ralat: {str(e)}"
