FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    libpcap-dev \
    python3-tk \
    tk \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libxcb1 \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3","Main.py"]