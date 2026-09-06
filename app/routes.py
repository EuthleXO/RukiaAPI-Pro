"""
API Routes for RukiaApiPro
"""

import time
from typing import Optional

import aiohttp
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import (
    APP_NAME, VERSION, DEVELOPER, GITHUB, CONTACT, HEROKU_DEPLOY,
    TEMPLATES_DIR, COOKIES_FILE,
)
from app import ytdl_helper as yt

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR)) if TEMPLATES_DIR.exists() else None


# -------------------- Home / Docs --------------------

@router.get("/")
async def home(request: Request):
    if templates:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "app_name": APP_NAME,
            "version": VERSION,
            "developer": DEVELOPER,
            "github": GITHUB,
            "contact": CONTACT,
            "heroku_deploy": HEROKU_DEPLOY,
        })
    return JSONResponse({"name": APP_NAME, "version": VERSION, "status": "ok"})


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": VERSION,
        "cookies_loaded": COOKIES_FILE.exists(),
        "cache": yt.cache_stats(),
        "developer": DEVELOPER,
    }


# -------------------- Info --------------------

@router.get("/info/{video_id}")
async def get_info(video_id: str):
    if not video_id or len(video_id) < 5 or len(video_id) > 20:
        raise HTTPException(400, "Invalid video_id")

    start = time.time()
    try:
        info = await yt.extract_info(video_id)
    except Exception as e:
        raise HTTPException(400, {
            "error": "extraction_failed",
            "message": str(e)[:300],
            "tip": "Add valid cookies.txt for age-restricted / blocked videos",
        })

    elapsed = round((time.time() - start) * 1000, 1)
    return {
        "status": "success",
        "id": info.get("id"),
        "title": info.get("title"),
        "duration": info.get("duration"),
        "duration_string": info.get("duration_string") or str(info.get("duration") or 0),
        "uploader": info.get("uploader") or info.get("channel"),
        "channel": info.get("channel") or info.get("uploader"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "thumbnail": info.get("thumbnail"),
        "description": (info.get("description") or "")[:400],
        "webpage_url": info.get("webpage_url"),
        "is_live": bool(info.get("is_live")),
        "extraction_time_ms": elapsed,
    }


# -------------------- Stream --------------------

@router.get("/stream/{video_id}")
async def stream(
    video_id: str,
    type: str = Query("audio", pattern="^(audio|video)$"),
    redirect: bool = Query(True, description="302 to CDN (fastest)"),
    max_height: int = Query(720, ge=144, le=1080),
):
    if not video_id or len(video_id) < 5:
        raise HTTPException(400, "Invalid video_id")

    start = time.time()
    try:
        info = await yt.extract_info(video_id)
    except Exception as e:
        raise HTTPException(400, f"Extraction failed: {str(e)[:250]}")

    if type == "audio":
        fmt = yt.pick_best_audio(info)
    else:
        fmt = yt.pick_best_video(info, max_height=max_height)

    if not fmt or not fmt.get("url"):
        raise HTTPException(404, "No suitable format found. Try cookies.txt")

    stream_url = fmt["url"]
    ext = fmt.get("ext") or ("m4a" if type == "audio" else "mp4")
    title = (info.get("title") or video_id).replace('"', "").replace("\n", " ")[:120]
    elapsed = round((time.time() - start) * 1000, 1)

    headers = {
        "X-Extraction-Time-Ms": str(elapsed),
        "X-Format-Ext": ext,
        "X-Powered-By": APP_NAME,
        "Cache-Control": "public, max-age=1800",
    }

    if redirect:
        return RedirectResponse(url=stream_url, status_code=302, headers=headers)

    # Proxy mode
    async def generate():
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=12, sock_read=45)
        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
        }
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(stream_url, headers=req_headers) as resp:
                if resp.status >= 400:
                    raise HTTPException(502, "Upstream CDN error")
                async for chunk in resp.content.iter_chunked(128 * 1024):
                    yield chunk

    media_type = (
        "audio/mp4" if ext in ("m4a", "mp4")
        else f"audio/{ext}" if type == "audio"
        else f"video/{ext}"
    )

    return StreamingResponse(
        generate(),
        media_type=media_type,
        headers={
            **headers,
            "Content-Disposition": f'inline; filename="{title}.{ext}"',
            "Accept-Ranges": "bytes",
        },
    )


# -------------------- Search --------------------

@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(6, ge=1, le=15),
):
    try:
        tracks = await yt.search_tracks(q, limit=limit)
        return {"status": "success", "query": q, "count": len(tracks), "results": tracks}
    except Exception as e:
        raise HTTPException(500, f"Search failed: {str(e)[:200]}")


# -------------------- Formats (debug) --------------------

@router.get("/formats/{video_id}")
async def formats(video_id: str):
    info = await yt.extract_info(video_id)
    out = []
    for f in info.get("formats") or []:
        if f.get("url"):
            out.append({
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution"),
                "height": f.get("height"),
                "abr": f.get("abr"),
                "tbr": f.get("tbr"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
                "filesize": f.get("filesize") or f.get("filesize_approx"),
            })
    return {"id": info.get("id"), "title": info.get("title"), "formats": out}


# -------------------- Speed Test --------------------

@router.get("/speedtest/{video_id}")
async def speedtest(video_id: str, type: str = Query("audio", pattern="^(audio|video)$")):
    info = await yt.extract_info(video_id)
    fmt = yt.pick_best_audio(info) if type == "audio" else yt.pick_best_video(info)
    if not fmt or not fmt.get("url"):
        raise HTTPException(404, "No format")

    stream_url = fmt["url"]
    test_size = 2 * 1024 * 1024  # 2 MB

    start = time.time()
    downloaded = 0
    timeout = aiohttp.ClientTimeout(total=25, sock_connect=10)
    headers = {"User-Agent": "Mozilla/5.0", "Range": f"bytes=0-{test_size-1}"}

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(stream_url, headers=headers) as resp:
            async for chunk in resp.content.iter_chunked(64 * 1024):
                downloaded += len(chunk)
                if downloaded >= test_size:
                    break

    elapsed = time.time() - start
    speed_mbs = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0

    return {
        "status": "success",
        "video_id": video_id,
        "type": type,
        "tested_bytes": downloaded,
        "time_seconds": round(elapsed, 3),
        "speed_MBps": round(speed_mbs, 2),
        "speed_Mbps": round(speed_mbs * 8, 2),
        "note": "Speed from YouTube CDN → this server. With redirect=true real clients get even higher speed.",
    }
