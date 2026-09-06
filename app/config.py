"""
RukiaApiPro - High Performance Config (Paid Heroku Optimized)
Developer: @flexyy
"""

import os
from pathlib import Path

# ==================== APP INFO ====================
APP_NAME = "RukiaApiPro"
VERSION = "2.0.0-PRO"
DEVELOPER = "@flexyy"
GITHUB = "https://github.com/EuthleXO/RukiaAPI-Pro"
CONTACT = "https://t.me/flexyy"
HEROKU_DEPLOY = "https://dashboard.heroku.com/new?template=https://github.com/EuthleXO/RukiaAPI-Pro"

# ==================== PATHS ====================
BASE_DIR = Path(__file__).resolve().parent.parent
COOKIES_FILE = BASE_DIR / "cookies.txt"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# ==================== CACHE (Aggressive for speed) ====================
CACHE_TTL = 600          # 10 minutes
MAX_CACHE_SIZE = 800

# ==================== YT-DLP (Strongest practical clients 2026) ====================
YDL_BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "skip_download": True,
    "nocheckcertificate": True,
    "geo_bypass": True,
    "force_ipv4": True,
    "socket_timeout": 10,
    "retries": 3,
    "fragment_retries": 3,
    "ignoreerrors": False,
    "noplaylist": True,
    # Strong client rotation for current YouTube challenges
    "extractor_args": {
        "youtube": {
            "player_client": [
                "tv",
                "web_embedded",
                "mweb",
                "android",
                "ios",
                "web",
            ],
            "player_skip": ["webpage", "configs"],
        }
    },
}

if COOKIES_FILE.exists():
    YDL_BASE_OPTS["cookiefile"] = str(COOKIES_FILE)

# ==================== SERVER ====================
PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

# Paid dyno friendly
WORKERS = int(os.environ.get("WEB_CONCURRENCY", 2))
