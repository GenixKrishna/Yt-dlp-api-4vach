import os
import shutil
import tempfile
from pathlib import Path

import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="VaCh yt-dlp + FFmpeg API",
    version="2.2.0",
)

# The VaCh frontend normally calls this API through its Vercel /api proxy.
# CORS is also enabled so direct browser/API testing works.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MediaRequest(BaseModel):
    url: HttpUrl
    quality: str = "best"
    audio_only: bool = False


def base_ydl_opts() -> dict:
    """
    Current yt-dlp YouTube setup:
    - yt-dlp[default] supplies yt-dlp-ejs
    - Docker supplies Node 22 as the JS runtime
    - bgutil-ytdlp-pot-provider supplies per-video PO tokens
    """
    return {
        "quiet": True,
        "no_warnings": True,
        "js_runtimes": {"node": {}},
        # Keep EJS scripts current when the bundled package is not enough.
        "remote_components": {"ejs": ["github"]},
        # Current bgutil provider listens privately inside this container.
        "extractor_args": {
            "youtubepot-bgutilhttp": {"base_url": "http://127.0.0.1:4416"},
            "youtube": {"player_client": ["mweb"]},
        },
        "retries": 3,
        "fragment_retries": 3,
        "noplaylist": True,
    }


@app.get("/")
def health():
    return {
        "status": "online",
        "service": "yt-dlp + FFmpeg API",
        "version": "2.1.0",
        "youtube_js_runtime": "node",
        "youtube_ejs": True,
        "youtube_po_token_provider": "bgutil-http",
    }


@app.post("/info")
def get_info(request: MediaRequest):
    opts = base_ydl_opts()
    opts["skip_download"] = True

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(str(request.url), download=False)

        formats = []
        for f in info.get("formats", []):
            height = f.get("height")
            if not height:
                continue

            formats.append(
                {
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "height": height,
                    "width": f.get("width"),
                    "fps": f.get("fps"),
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                    "vcodec": f.get("vcodec"),
                    "acodec": f.get("acodec"),
                    "format_note": f.get("format_note"),
                }
            )

        # Remove duplicate format entries while preserving order.
        seen = set()
        unique_formats = []
        for item in formats:
            key = (
                item["height"],
                item["ext"],
                item["vcodec"],
                item["acodec"],
            )
            if key not in seen:
                seen.add(key)
                unique_formats.append(item)

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "webpage_url": info.get("webpage_url"),
            "formats": unique_formats,
        }

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"ERROR: {exc}") from exc


@app.post("/download")
def download_media(request: MediaRequest):
    temp_dir = Path(tempfile.mkdtemp(prefix="vach_"))
    output_template = str(temp_dir / "%(title).150s.%(ext)s")

    opts = base_ydl_opts()
    opts.update(
        {
            "outtmpl": output_template,
            "restrictfilenames": True,
        }
    )

    if request.audio_only:
        opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )
    else:
        quality = str(request.quality).lower().strip()

        if quality.isdigit():
            height = int(quality)
            # Prefer requested height; fall back to the closest lower
            # available height, then best available video+audio.
            opts["format"] = (
                f"bestvideo[height<={height}]+bestaudio/"
                f"best[height<={height}]/best"
            )
        else:
            opts["format"] = "bestvideo+bestaudio/best"

        opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(str(request.url), download=True)
            prepared = Path(ydl.prepare_filename(info))

        if request.audio_only:
            candidates = list(temp_dir.glob("*"))
        else:
            candidates = list(temp_dir.glob("*.mp4"))

        if not candidates:
            candidates = list(temp_dir.glob("*"))

        if not candidates:
            raise RuntimeError("Downloaded file was not created.")

        file_path = max(candidates, key=lambda p: p.stat().st_mtime)

        media_type = "audio/mpeg" if request.audio_only else "video/mp4"
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_path.name,
            background=None,
        )

    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"ERROR: {exc}") from exc
