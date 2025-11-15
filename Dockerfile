# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV and EasyOCR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and set longer timeout for large packages
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt .

# Install lightweight dependencies first (for better layer caching)
RUN pip install --default-timeout=1000 \
    fastapi \
    uvicorn[standard] \
    python-multipart

# Install PyTorch CPU version (large package, ~200MB)
# Using CPU version is smaller and sufficient for Heroku
RUN pip install --default-timeout=1000 \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Install EasyOCR last (depends on torch, very large with all dependencies)
RUN pip install --default-timeout=1000 easyocr

# Copy application code
COPY main.py .

# Expose port (Heroku will set PORT env variable)
EXPOSE 8000

# Run the application
# Heroku sets PORT environment variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

