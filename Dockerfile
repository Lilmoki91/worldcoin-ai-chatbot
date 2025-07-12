# Gunakan base image Python yang sesuai
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy semua fail ke dalam container
COPY . .

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 libsm6 libxext6 tesseract-ocr && \
    apt-get clean

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Port untuk Flask
EXPOSE 5000

# Command untuk jalankan bot + flask
CMD ["python", "app.py"]
