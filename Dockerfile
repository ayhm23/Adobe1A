FROM --platform=linux/amd64 python:3.9-slim

# Install minimal system dependencies including OpenGL for headless OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgomp1 \
    libgfortran5 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --upgrade pip

# Install specific OpenCV version that works well in containers
RUN pip install --no-cache-dir opencv-python-headless==4.8.0.76

RUN pip install pillow 
WORKDIR /app

# Copy application files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# # Pre-download the model during build (when network is available)
# RUN python -c "import os; os.makedirs('/root/.paddlex/official_models', exist_ok=True)"

# RUN python -c "from paddleocr import LayoutDetection; LayoutDetection(model_name='PP-DocLayout-M')" || echo "Model download failed, will retry at runtime"

COPY main.py config.json ./
COPY src/ ./src/
# COPY model_cache/official_models /root/.paddlex/official_models
COPY models/PP-DocLayout-M /opt/pp_doclayout_M
# Create I/O directories and model cache
RUN mkdir -p /app/input /app/output /root/.paddlex \
    && chmod 755 /app/input /app/output 

# Environment variables
ENV PADDLEX_HOME=/root/.paddlex

# Force headless mode and disable display
ENV OPENCV_HEADLESS=1
ENV CUDA_VISIBLE_DEVICES=""
ENV OMP_NUM_THREADS=1
ENV DISPLAY=""

# Default command
CMD ["python", "main.py"]
