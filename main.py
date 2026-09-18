from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
import yt_dlp
import tempfile
import os

app = FastAPI(title="yt-dlp API", version="2.0.0")

class InfoRequest(BaseModel):
    url: HttpUrl

class DownloadRequest(BaseModel):
    url: HttpUrl
    quality: int | None = None
    audio_only: bool = False

@app.get("/")
def health():
    return {"status":"online","service":"yt-dlp + FFmpeg API","version":"2.0.0"}

@app.post("/info")
def get_info(request: InfoRequest):
    try:
        opts={"quiet":True,"skip_download":True,"noplaylist":True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info=ydl.extract_info(str(request.url), download=False)
        formats=[]
        seen=set()
        for f in info.get("formats", []):
            if f.get("vcodec")=="none":
                continue
            key=(f.get("height"),f.get("ext"),f.get("fps"),f.get("acodec")!="none")
            if key in seen:
                continue
            seen.add(key)
            formats.append({
                "format_id":f.get("format_id"),
                "ext":f.get("ext"),
                "resolution":f.get("resolution"),
                "height":f.get("height"),
                "fps":f.get("fps"),
                "has_audio":f.get("acodec")!="none",
                "filesize":f.get("filesize")
            })
        formats.sort(key=lambda x:(x["height"] or 0,x["fps"] or 0,1 if x["has_audio"] else 0), reverse=True)
        return {"title":info.get("title"),"thumbnail":info.get("thumbnail"),
                "duration":info.get("duration"),"uploader":info.get("uploader"),
                "formats":formats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/download")
def download(request: DownloadRequest):
    temp_dir=tempfile.mkdtemp(prefix="vach-")
    try:
        if request.audio_only:
            opts={
                "quiet":True,"noplaylist":True,"format":"bestaudio/best",
                "outtmpl":os.path.join(temp_dir,"%(title)s.%(ext)s"),
                "postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
            }
        else:
            if request.quality:
                fmt=f"bestvideo[height={request.quality}]+bestaudio/best[height={request.quality}]/best"
            else:
                fmt="bestvideo+bestaudio/best"
            opts={
                "quiet":True,"noplaylist":True,"format":fmt,
                "merge_output_format":"mp4",
                "outtmpl":os.path.join(temp_dir,"%(title)s.%(ext)s")
            }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info=ydl.extract_info(str(request.url), download=True)
            prepared=ydl.prepare_filename(info)

        candidates=[]
        if os.path.exists(prepared):
            candidates.append(prepared)
        for name in os.listdir(temp_dir):
            path=os.path.join(temp_dir,name)
            if os.path.isfile(path):
                candidates.append(path)
        if not candidates:
            raise HTTPException(status_code=500, detail="Downloaded file was not created")

        final=next((p for p in candidates if p.lower().endswith(".mp4")),None)
        if not final:
            final=next((p for p in candidates if p.lower().endswith(".mp3")),None)
        final=final or candidates[0]

        media="audio/mpeg" if final.lower().endswith(".mp3") else "video/mp4"
        return FileResponse(final, media_type=media, filename=os.path.basename(final))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
