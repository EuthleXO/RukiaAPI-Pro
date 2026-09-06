"""
RukiaApiPro - Configuration
Developer: @flexyy
"""

import os
from pathlib import Path

# ==================== APP INFO ====================
APP_NAME = "RukiaApiPro"
VERSION = "1.3.0"
DEVELOPER = "@flexyy"
GITHUB = "https://github.com/EuthleXO/RukiaAPI-Pro"
CONTACT = "https://t.me/flexyy"
HEROKU_DEPLOY = "https://dashboard.heroku.com/new?template=https://github.com/EuthleXO/RukiaAPI-Pro"

# ==================== PATHS ====================
BASE_DIR = Path(__file__).resolve().parent.parent
COOKIES_FILE = BASE_DIR / "cookies.txt"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# ==================== CACHE ====================
CACHE_TTL = 300          # seconds
MAX_CACHE_SIZE = 400

# ==================== YT-DLP ====================
# Optimized for 2026 YouTube challenges
YDL_BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "skip_download": True,
    "nocheckcertificate": True,
    "geo_bypass": True,
    "force_ipv4": True,
    "socket_timeout": 12,
    "retries": 2,
    "fragment_retries": 2,
    "ignoreerrors": False,
    "noplaylist": True,
    # Best client combination for current YouTube (JS challenge / SABR / PoW bypass)
    "extractor_args": {
        "youtube": {
            "player_client": ["tv", "web_embedded", "mweb", "android", "web"],
            "player_skip": ["webpage", "configs"],
        }
    },
}

# Load cookies if present
if COOKIES_FILE.exists():
    YDL_BASE_OPTS["cookiefile"] = str(COOKIES_FILE)

# ==================== SERVER ====================
PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"
