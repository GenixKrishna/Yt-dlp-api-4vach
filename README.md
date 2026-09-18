# yt-dlp API — VaCh

FastAPI backend using yt-dlp and FFmpeg.

## Endpoints

GET `/` — health check.

POST `/info`:
```json
{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}
```

POST `/download` for video:
```json
{"url":"https://www.youtube.com/watch?v=VIDEO_ID","quality":1080,"audio_only":false}
```

POST `/download` for audio:
```json
{"url":"https://www.youtube.com/watch?v=VIDEO_ID","audio_only":true}
```

Railway uses the Dockerfile and installs FFmpeg automatically.

For a public deployment, add rate limiting, download limits, concurrency controls, robust temporary-file cleanup and monitoring. Use only for content you are authorized to download and in accordance with applicable platform terms and copyright law.
