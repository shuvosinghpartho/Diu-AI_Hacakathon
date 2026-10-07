FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for OpenCV and EasyOCR
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ocr.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-ocr.txt

COPY . .

# Expose port and run Gunicorn with Uvicorn workers for high concurrency
EXPOSE 8000
CMD ["gunicorn", "backend.app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
