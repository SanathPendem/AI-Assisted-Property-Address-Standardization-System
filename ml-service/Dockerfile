FROM python:3.10-slim

# Install system dependencies for compiling libpostal
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libtool \
    pkg-config \
    autoconf \
    automake \
    && rm -rf /var/lib/apt/lists/*

# Clone and install libpostal
RUN git clone https://github.com/openvenues/libpostal /usr/src/libpostal
WORKDIR /usr/src/libpostal
RUN ./bootstrap.sh \
    && ./configure --datadir=/var/lib/libpostal \
    && make -j$(nproc) \
    && make install \
    && ldconfig

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cache sentence-transformers model during build phase
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
