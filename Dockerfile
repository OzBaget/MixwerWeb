FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-heb poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# זו התיקייה הנכונה בחבילות Tesseract 5 בדביאן/אובונטו
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["bash","-lc","gunicorn --timeout 300 --graceful-timeout 300 --workers 1 --threads 2 --access-logfile - --error-logfile - -b 0.0.0.0:${PORT:-8000} app:app"]
