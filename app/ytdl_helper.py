"""
High-performance yt-dlp helper with multi-strategy fallback
Handles Error 152 / unavailable / age-gate as much as possible
"""

import asyncio
import time
from typing import Optional, Dict, Any, List

import yt_dlp
from app.config import YDL_BASE_OPTS, CACHE_TTL, MAX_CACHE_SIZE, COOKIES_FILE

_INFO_CACHE: Dict[str, Dict[str, Any]] = {}


def _base_opts() -> dict:
    opts = dict(YDL_BASE_OPTS)  # shallow copy
    if COOKIES_FILE.exists():
        opts["cookiefile"] = str(COOKIES_FILE)
    return opts


def _get_ydl(extra: dict = None):
    opts = _base_opts()
    if extra:
        if "extractor_args" in extra:
            opts["extractor_args"] = extra["extractor_args"]
            extra = {k: v for k, v in extra.items() if k != "extractor_args"}
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
        oldest = sorted(_INFO_CACHE.items(), key=lambda x: x[1]["ts"])[:80]
        for k, _ in oldest:
            _INFO_CACHE.pop(k, None)


def build_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


# Ordered strategies — try until one works (Error 152 mitigation)
CLIENT_STRATEGIES = [
    # 1. Most reliable currently for many restricted videos
    {
        "extractor_args": {
            "youtube": {
                "player_client": ["tv", "tv_embedded", "web_embedded"],
                "player_skip": ["webpage", "configs"],
            }
        }
    },
    # 2. Mobile web + android
    {
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "android", "ios"],
                "player_skip": ["webpage", "configs"],
            }
        }
    },
    # 3. Web creator + web
    {
        "extractor_args": {
            "youtube": {
                "player_client": ["web_creator", "web", "mweb"],
                "player_skip": ["configs"],
            }
        }
    },
    # 4. Minimal / last resort
    {
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "player_skip": ["webpage", "configs", "js"],
            }
        }
    },
]


def _try_extract(url: str, extra: dict = None) -> dict:
    with _get_ydl(extra) as ydl:
        return ydl.extract_info(url, download=False)


async def extract_info(video_id: str) -> dict:
    """
    Try multiple player-client strategies until one succeeds.
    """
    cached = _cache_get(video_id)
    if cached:
        return cached

    url = build_url(video_id)
    last_error = None

    # Default first
    try:
        info = await asyncio.to_thread(_try_extract, url)
        if info and info.get("id"):
            _cache_set(video_id, info)
            return info
    except Exception as e:
        last_error = e

    # Fallback strategies
    for strategy in CLIENT_STRATEGIES:
        try:
            info = await asyncio.to_thread(_try_extract, url, strategy)
            if info and info.get("id"):
                _cache_set(video_id, info)
                return info
        except Exception as e:
            last_error = e
            continue

    msg = str(last_error) if last_error else "Unknown extraction error"
    if "ERROR: " in msg:
        msg = msg.split("ERROR: ", 1)[-1]
    # Make message cleaner for API consumers
    if "Error code: 152" in msg or "unavailable" in msg.lower():
        msg = (
            "Video unavailable (YouTube Error 152). "
            "This usually means region lock, age-restriction, or temporary YouTube block. "
            "Try another video or refresh cookies.txt."
        )
    raise ValueError(msg[:450])


def pick_best_audio(info: dict) -> Optional[dict]:
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
                score += 3000
            elif ext == "webm" or "opus" in acodec:
                score += 1200
            elif ext == "mp3":
                score += 400

            candidates.append((score, f))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    for f in formats:
        if f.get("url") and f.get("acodec") not in (None, "none"):
            return f
    return None


def pick_best_video(info: dict, max_height: int = 720) -> Optional[dict]:
    formats = info.get("formats") or []
    progressive = []

    for f in formats:
        if not f.get("url"):
            continue
        height = f.get("height") or 0
        if height == 0 or height > max_height:
            continue
        if f.get("vcodec") not in (None, "none") and f.get("acodec") not in (None, "none"):
            tbr = f.get("tbr") or 0
            progressive.append((height, tbr, f))

    if progressive:
        progressive.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return progressive[0][2]

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


async def search_tracks(query: str, limit: int = 8) -> List[dict]:
    ydl_opts = {
        **_base_opts(),
        "extract_flat": "in_playlist",
        "default_search": f"ytsearch{limit}",
    }

    def _run():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
    return {"size": len(_INFO_CACHE), "ttl_seconds": CACHE_TTL}
