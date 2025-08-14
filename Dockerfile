FROM python:3.11-slim

# התקנות מערכת ל־OCR ו־PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-heb poppler-utils \
    && rm -rf /var/lib/apt/lists/*

ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
# ספקים כמו Render מזריקים PORT; נשתמש בו אם קיים
CMD ["bash", "-lc", "gunicorn -b 0.0.0.0:${PORT:-8000} app:app"]
