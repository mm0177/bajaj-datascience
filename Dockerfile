FROM python:3.10-slim

# Install system dependencies including Tesseract OCR
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr \
       libglib2.0-0 \
       libsm6 \
       libxext6 \
       libxrender-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose default port (for documentation; actual port comes from env)
EXPOSE 8000

# Use shell form for CMD so that $PORT is expanded at runtime
# If PORT is not set by the environment, default to 8000
CMD uvicorn lab_api:app --host 0.0.0.0 --port ${PORT:-8000}
