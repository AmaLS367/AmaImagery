FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates git python3.11 python3.11-distutils python3.11-venv \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py \
 && python3.11 /tmp/get-pip.py \
 && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
 && ln -sf /usr/local/bin/pip3 /usr/bin/pip3 \
 && python3 --version && pip3 --version

WORKDIR /app
COPY requirements.txt ./
RUN pip3 install -U pip && pip3 install -r requirements.txt

RUN addgroup --system app && adduser --system --ingroup app --home /app app \
 && mkdir -p /app/outputs /app/logs /app/.cache \
 && chown -R app:app /app

COPY . .
EXPOSE 8000

USER app

CMD ["python3", "run.py"]
