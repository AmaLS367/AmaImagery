FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/models/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    git \
    ffmpeg \
    libgl1 \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-distutils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py \
    && python3 /tmp/get-pip.py \
    && rm /tmp/get-pip.py

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app --home /app app

# Cache dependency installation separately from application code.
COPY pyproject.toml README.md ./
RUN mkdir -p /app/app \
    && printf "__all__ = []\n" > /app/app/__init__.py \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

# Copy only runtime files needed by the API and worker.
COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts
COPY run.py ./run.py
COPY NOTICE.txt ./NOTICE.txt
COPY ATTRIBUTIONS.md ./ATTRIBUTIONS.md
COPY LICENSE ./LICENSE

RUN mkdir -p /app/outputs /app/logs /app/models \
    && chown -R app:app /app

EXPOSE 8000

USER app

CMD ["python3", "run.py"]
