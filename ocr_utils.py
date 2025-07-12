import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

def extract_text_from_image(image_path):
    try:
        # Buka dan preprocess gambar
        img = Image.open(image_path)
        img = img.convert("L")  # Tukar ke grayscale
        img = img.filter(ImageFilter.SHARPEN)  # Tajamkan imej (lebih jelas)

        # OCR: gabungan English + Malay (msa)
        text = pytesseract.image_to_string(img, lang='eng+msa')
        text = text.strip()

        if not text:
            return "⚠️ Tiada teks dikesan dalam gambar. Pastikan gambar jelas dan terang."
        
        return text

    except Exception as e:
        return f"❌ Gagal membaca gambar. Ralat: {str(e)}"
