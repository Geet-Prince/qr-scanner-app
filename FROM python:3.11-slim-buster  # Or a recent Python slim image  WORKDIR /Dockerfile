FROM python:3.11-slim-buster

WORKDIR /app

# Install system dependencies (including build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    zbar-tools \
    build-essential \
    cmake \
    git \
    pkg-config \
    libtool \
    autoconf \
    libzbar-dev  # Development files (often needed)

# Install Rust (required for some pyzbar builds)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "qr_scanner.py"]
