# Stage 1: Build zbar from source

FROM ubuntu:22.04 AS builder

WORKDIR /tmp

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    libtool \
    autoconf \
    libzbar-dev \
    libzbar0 # Install libzbar for linking

# Download and build zbar
RUN git clone https://github.com/zbar/zbar.git
WORKDIR /tmp/zbar
RUN ./autogen.sh && ./configure --prefix=/usr/local --enable-video --without-qt && make -j$(nproc) && make install

# Stage 2: Final Streamlit image

FROM python:3.11-slim-buster

WORKDIR /app

# Copy built zbar library
COPY --from=builder /usr/local/lib/libzbar.so.0 /usr/local/lib/
COPY --from=builder /usr/local/include/zbar.h /usr/local/include/

# Set up the environment to find the library
ENV LD_LIBRARY_PATH /usr/local/lib:$LD_LIBRARY_PATH

# Copy built zbar tools (if needed by pyzbar)
COPY --from=builder /usr/local/bin/zbar-config /usr/local/bin/
COPY --from=builder /usr/local/bin/zbarimg /usr/local/bin/
COPY --from=builder /usr/local/bin/zbarcam /usr/local/bin/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["streamlit", "run", "qr_scanner.py"]
