# VaCh yt-dlp + FFmpeg API

FastAPI backend for VaCh with YouTube EJS challenge solving and a local bgutil PO-token provider.

## Endpoints

- `GET /` — health
- `POST /info` — metadata and available formats
- `POST /download` — video/audio download

## YouTube runtime

This image includes:

- yt-dlp with the default EJS dependency group
- Node.js 22 LTS for EJS challenge solving
- bgutil-ytdlp-pot-provider 2.0.0 running privately on `127.0.0.1:4416`
- FFmpeg for merging video/audio and MP3 extraction

No YouTube account cookies are required by this setup.

## Railway

Deploy this repository with the included Dockerfile. Railway should provide `PORT` automatically.

The PO-token provider is intentionally bound to localhost and is not exposed as a public Railway port.

## Important limitation

YouTube changes anti-bot protections continuously. PO-token providers are designed to help with current YouTube bot checks, but no third-party downloader can guarantee that every YouTube URL, region, IP, age/consent gate, live stream, or future YouTube change will always work. If YouTube changes its attestation system, the backend may need a later yt-dlp/provider update.
