# Start with a base Python image
FROM python:3.10-slim

# Install system dependencies including Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean

# Set the working directory inside the container
WORKDIR /app

# Copy the entire project into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the app will run on
EXPOSE 8000

# Start the FastAPI application using Uvicorn
CMD ["uvicorn", "lab_api:app", "--host", "0.0.0.0", "--port", "8000"]
