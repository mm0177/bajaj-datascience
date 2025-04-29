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

# Copy and make the startup script executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose default port (documentation only)
EXPOSE 8000

# Run the startup script
CMD ["/app/start.sh"]