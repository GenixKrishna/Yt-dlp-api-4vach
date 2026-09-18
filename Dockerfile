FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NODE_VERSION=22.22.2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg curl ca-certificates xz-utils git build-essential \
    && rm -rf /var/lib/apt/lists/*

# Node 22 LTS: required by the current yt-dlp EJS runtime support.
RUN curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
    | tar -xJ --strip-components=1 -C /usr/local \
    && node --version \
    && npm --version

# Build the current bgutil PO-token HTTP provider. Version 2.0.0 is the
# current release and contains important security fixes.
RUN git clone --depth 1 --branch 2.0.0 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /opt/bgutil \
    && cd /opt/bgutil/server \
    && npm ci \
    && npx tsc

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY main.py .
COPY start.sh .
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
