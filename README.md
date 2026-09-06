# ⚡ RukiaApiPro

**Ultra-Fast YouTube Streaming API**

**Developer:** [@flexyy](https://t.me/flexyy)  
**GitHub:** https://github.com/EuthleXO/RukiaAPI-Pro

---

## 🚀 One-Click Deploy on Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://dashboard.heroku.com/new?template=https://github.com/EuthleXO/RukiaAPI-Pro)

---

## ✨ Features

- 🚀 Single-Call Streaming (No token exchange)
- ⚡ Ultra Low Latency — Direct 302 redirect to YouTube CDN
- 🔥 200+ MB/s possible (CDN dependent)
- 🍪 Cookies support ready
- 🧪 Live Docs + Speed Tester at `/`
- 📱 Perfect for Telegram Music Bots (Yukki, AnonX, Fallen…)
- ❌ No API Key required currently
- 🛡️ Multiple player clients for better YouTube challenge handling

---

## 📡 Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Public docs + live tester |
| `GET /stream/{video_id}?type=audio` | Direct stream (redirect by default) |
| `GET /info/{video_id}` | Track metadata |
| `GET /search?q=...` | Search |
| `GET /speedtest/{video_id}` | Live speed test |
| `GET /formats/{video_id}` | List formats |
| `GET /health` | Health check |

### Stream Options
- `type=audio` (default) or `type=video`
- `redirect=true` (default) → 302 to CDN (fastest)
- `redirect=false` → Proxy through API

---

## 🍪 Cookies (Recommended)

1. Rename `cookies.txt.example` → `cookies.txt`
2. Paste Netscape-format YouTube cookies
3. Restart / Redeploy

---

## 📁 Project Structure

```
RukiaApiPro/
├── main.py                 # Entry point
├── app/
│   ├── __init__.py
│   ├── config.py           # Settings
│   ├── ytdl_helper.py      # yt-dlp + cache + format selection
│   └── routes.py           # All API routes
├── templates/
│   └── index.html          # Public docs + tester
├── app.json                # Heroku one-click deploy
├── Procfile
├── runtime.txt
├── requirements.txt
├── cookies.txt.example
└── README.md
```

---

## 🐍 Quick Usage

```python
import aiohttp

BASE = "https://your-app.herokuapp.com"
VIDEO_ID = "Zi_XLOBDo_Y"

async with aiohttp.ClientSession() as session:
    async with session.get(f"{BASE}/stream/{VIDEO_ID}?type=audio", allow_redirects=False) as r:
        if r.status in (301, 302, 307, 308):
            print(r.headers["Location"])  # Direct CDN URL
```

---

**Made with ⚡ by @flexyy**
