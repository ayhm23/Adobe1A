FROM --platform=linux/amd64 python:3.9-slim

# Install system dependencies for PaddleOCR and PyMuPDF


RUN apt-get update && apt-get install -y tesseract-ocr
RUN pip install pytesseract pillow

# ...existing code...
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*
# ...existing code...

WORKDIR /app

# Copy requirements first for better caching
RUN pip install --upgrade pip



COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY src/ ./src/
COPY config.json .

# Ensure the app can write to output directory
RUN mkdir -p /app/input /app/output /app/debug_crops
RUN chmod 755 /app/input /app/output /app/debug_crops

# Run the main application
CMD ["python", "main.py"]
