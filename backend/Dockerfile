# 1. Utiliser une image Python légère
FROM python:3.9-slim

# 2. Installer les dépendances système (Tesseract et OpenCV)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Définir le dossier de travail
WORKDIR /app

# 4. Copier et installer les bibliothèques Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copier le reste du code (FastAPI + AI logic)
COPY . .

# 6. Lancer le serveur FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]