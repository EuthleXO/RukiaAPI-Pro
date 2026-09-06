"""
yt-dlp helper with caching + best format selection
Handles current YouTube challenges as much as possible without external JS runtime.
"""

import asyncio
import time
from typing import Optional, Dict, Any

import yt_dlp
from app.config import YDL_BASE_OPTS, CACHE_TTL, MAX_CACHE_SIZE

# Simple in-memory cache
_INFO_CACHE: Dict[str, Dict[str, Any]] = {}


def _get_ydl(extra: dict = None):
    opts = YDL_BASE_OPTS.copy()
    if extra:
        opts.update(extra)
    return yt_dlp.YoutubeDL(opts)


def _cache_get(video_id: str) -> Optional[dict]:
    entry = _INFO_CACHE.get(video_id)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["info"]
    return None


def _cache_set(video_id: str, info: dict):
    _INFO_CACHE[video_id] = {"info": info, "ts": time.time()}
    if len(_INFO_CACHE) > MAX_CACHE_SIZE:
        # remove oldest 50
        oldest = sorted(_INFO_CACHE.items(), key=lambda x: x[1]["ts"])[:50]
        for k, _ in oldest:
            _INFO_CACHE.pop(k, None)


def build_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


async def extract_info(video_id: str) -> dict:
    """Extract video info with cache."""
    cached = _cache_get(video_id)
    if cached:
        return cached

    url = build_url(video_id)

    def _run():
        with _get_ydl() as ydl:
            return ydl.extract_info(url, download=False)

    info = await asyncio.to_thread(_run)
    if not info:
        raise ValueError("No info returned from yt-dlp")
    _cache_set(video_id, info)
    return info


def pick_best_audio(info: dict) -> Optional[dict]:
    """Prefer high-quality m4a / aac, then opus/webm."""
    formats = info.get("formats") or []
    candidates = []

    for f in formats:
        if not f.get("url"):
            continue
        if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none"):
            abr = f.get("abr") or f.get("tbr") or 0
            ext = (f.get("ext") or "").lower()
            acodec = str(f.get("acodec") or "")
            score = float(abr)

            if ext == "m4a" or "mp4a" in acodec:
                score += 2500
            elif ext == "webm" or "opus" in acodec:
                score += 900
            candidates.append((score, f))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    # progressive fallback
    for f in formats:
        if f.get("url") and f.get("acodec") not in (None, "none"):
            return f
    return None


def pick_best_video(info: dict, max_height: int = 720) -> Optional[dict]:
    """Prefer progressive mp4 ≤ max_height."""
    formats = info.get("formats") or []
    progressive = []

    for f in formats:
        if not f.get("url"):
            continue
        height = f.get("height") or 0
        if height > max_height or height == 0:
            continue
        if f.get("vcodec") not in (None, "none") and f.get("acodec") not in (None, "none"):
            tbr = f.get("tbr") or 0
            progressive.append((height, tbr, f))

    if progressive:
        progressive.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return progressive[0][2]

    # video-only fallback
    video_only = []
    for f in formats:
        if not f.get("url"):
            continue
        height = f.get("height") or 0
        if 0 < height <= max_height and f.get("vcodec") not in (None, "none"):
            video_only.append((height, f.get("tbr") or 0, f))

    if video_only:
        video_only.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return video_only[0][2]
    return None


async def search_tracks(query: str, limit: int = 6) -> list:
    ydl_opts = {
        **YDL_BASE_OPTS,
        "extract_flat": "in_playlist",
        "default_search": f"ytsearch{limit}",
    }

    def _run():
        with _get_ydl(ydl_opts) as ydl:
            return ydl.extract_info(query, download=False)

    results = await asyncio.to_thread(_run)
    entries = results.get("entries") or []
    tracks = []
    for e in entries[:limit]:
        if not e:
            continue
        vid = e.get("id")
        tracks.append({
            "id": vid,
            "title": e.get("title"),
            "duration": e.get("duration"),
            "url": f"https://www.youtube.com/watch?v={vid}",
            "channel": e.get("channel") or e.get("uploader"),
            "thumbnail": e.get("thumbnail") or (e.get("thumbnails") or [{}])[-1].get("url"),
        })
    return tracks


def cache_stats() -> dict:
    return {
        "size": len(_INFO_CACHE),
        "ttl_seconds": CACHE_TTL,
    }
