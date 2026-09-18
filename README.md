# VaCh yt-dlp + FFmpeg API

FastAPI backend for VaCh.

## Endpoints

- `GET /` health check
- `POST /info` metadata + available formats
- `POST /download` video/audio download

## YouTube support

The container installs:
- latest `yt-dlp[default]`
- `yt-dlp-ejs`
- Deno JavaScript runtime
- FFmpeg

This is the current yt-dlp setup for YouTube JavaScript challenge solving.

Note: YouTube can additionally enforce PO Tokens or other anti-bot measures. EJS does not guarantee access to every video or every server IP.

## Railway

Railway should run the Dockerfile and provide `$PORT`.
