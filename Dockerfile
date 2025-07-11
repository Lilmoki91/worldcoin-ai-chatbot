# Guna Python 3.10 (slim = ringan)
FROM python:3.10-slim

# Install system dependencies termasuk tesseract dan ffmpeg untuk suara
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Tetapkan direktori kerja
WORKDIR /app

# Salin semua fail ke dalam container
COPY . .

# Install pip dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port Flask (5000)
EXPOSE 5000

# Jalankan app
CMD ["python", "app.py"]
