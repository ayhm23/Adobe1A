FROM python:3.9-slim

# Install system dependencies including git-lfs for HuggingFace model download
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-dev \
    libgl1-mesa-glx \
    git \
    git-lfs \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --upgrade pip
RUN pip install pytesseract pillow

# Install huggingface-hub for model download
RUN pip install -U "huggingface_hub[cli]"

# Initialize git-lfs
RUN git lfs install

# Download PP-DocLayout_plus-L model from HuggingFace using multiple methods
ENV MODEL_DIR=/opt/pp_doclayout

# Method 1: Use huggingface-cli (most reliable)
RUN mkdir -p $MODEL_DIR && \
    huggingface-cli download PaddlePaddle/PP-DocLayout_plus-L \
    --local-dir $MODEL_DIR \
    --local-dir-use-symlinks False

# Method 2: Fallback using git clone (if above fails)
RUN if [ ! -f "$MODEL_DIR/inference.pdiparams" ]; then \
        echo "Trying git clone method..." && \
        rm -rf $MODEL_DIR && \
        git clone https://huggingface.co/PaddlePaddle/PP-DocLayout_plus-L $MODEL_DIR && \
        rm -rf $MODEL_DIR/.git; \
    fi


# Verify model files exist
RUN ls -la $MODEL_DIR/ && \
    echo "Model directory contents:" && \
    find $MODEL_DIR -type f -name "*.pdiparams" -o -name "*.yml" -o -name "*.json" | head -10

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY src/ ./src/
COPY config.json .

# Create directories
RUN mkdir -p /app/input /app/output /app/debug_crops /root/.paddlex/official_models
RUN chmod 755 /app/input /app/output /app/debug_crops

# Set environment variables
ENV MODEL_PATH=/opt/pp_doclayout
ENV PADDLEX_HOME=/root/.paddlex

# Run the main application
CMD ["python", "main.py"]
