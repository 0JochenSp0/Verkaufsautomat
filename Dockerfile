# Dependencies only. The project folder is bind-mounted to /app (see docker-compose.yml),
# so code changes need no rebuild.
FROM python:3.13-slim-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends gpiod curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pyserial==3.5 \
    esptool==5.6.0 \
    mpremote==1.29.0 \
    ruff==0.17.6

WORKDIR /app/software
ENV PYTHONPATH=src:firmware/esp32:../cad/lib \
    PYTHONDONTWRITEBYTECODE=1
