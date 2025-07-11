# Base image Python ringan
FROM python:3.10-slim

# Install sistem dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set direktori kerja
WORKDIR /app

# Salin semua fail projek ke dalam container
COPY . .

# Install dependencies projek
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Dedahkan port Flask (untuk Render)
EXPOSE 5000

# Jalankan aplikasi
CMD ["python", "app.py"]
