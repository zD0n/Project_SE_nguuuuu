FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libxcb1 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p model && gdown --id 1zgJoWaLNq5r7ZbFpgun4yZKJoJFkqKyS -O ./model/checkpoint_best_ema.pth

EXPOSE 5001

CMD ["gunicorn", "-b", "0.0.0.0:5001", "app:app"]