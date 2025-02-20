FROM python:3.11-slim-buster

WORKDIR /app

# Install system dependencies (including build tools)
RUN apt-get update && apt-get install -y \
    libzbar0 \
    zbar-tools \  # For potential command-line tools
    build-essential \ # For compiling dependencies
    cmake \
    git \
    pkg-config

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "qr_scanner.py"]
