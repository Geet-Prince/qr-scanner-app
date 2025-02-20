FROM python:3.11-slim-buster  # Or a recent Python slim image

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install system dependencies for pyzbar (CRUCIAL):
RUN apt-get update && apt-get install -y libzbar0

CMD ["streamlit", "run", "qr_scanner.py"]
