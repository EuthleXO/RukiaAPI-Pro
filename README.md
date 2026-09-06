# ⚡ RukiaApiPro v2.0 PRO

**Ultra-Fast YouTube Streaming API**  
**Optimized for Paid Heroku Dynos**

**Developer:** [@flexyy](https://t.me/flexyy)  
**GitHub:** https://github.com/EuthleXO/RukiaAPI-Pro

---

## 🚀 One-Click Deploy

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://dashboard.heroku.com/new?template=https://github.com/EuthleXO/RukiaAPI-Pro)

---

## ✨ PRO Features

- ⚡ **Maximum Speed** — Direct 302 to YouTube CDN (200–1000+ MB/s possible)
- 🔥 **2 Workers + uvloop + httptools** (Paid dyno optimized)
- 🍪 **Cookies support** (strongly recommended)
- 🧪 **Live Docs + Speed Tester** at `/`
- 📱 Perfect for Telegram Music Bots
- 🛡️ Strong multi-client yt-dlp config
- ❌ No API Key required

---

## 📡 Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Docs + Live Tester |
| `GET /stream/{video_id}?type=audio` | Fastest stream (redirect) |
| `GET /info/{video_id}` | Metadata |
| `GET /search?q=...` | Search |
| `GET /speedtest/{video_id}` | Real speed test |
| `GET /formats/{video_id}` | Formats |
| `GET /health` | Health |

**Best practice for bots:**
```
/stream/VIDEO_ID?type=audio          → 302 redirect (fastest)
/stream/VIDEO_ID?type=audio&redirect=false  → proxy mode
```

---

## 🍪 Cookies (Very Important)

1. Rename `cookies.txt.example` → `cookies.txt`
2. Paste valid Netscape YouTube cookies
3. Redeploy

This dramatically improves success rate.

---

## 📁 Structure

```
RukiaApiPro/
├── main.py
├── app/
│   ├── config.py
│   ├── ytdl_helper.py
│   └── routes.py
├── templates/index.html
├── app.json
├── Procfile          ← 2 workers + uvloop
├── requirements.txt
└── ...
```

---

## 🤖 Music Bot Usage

```python
stream_url = f"{API}/stream/{videoid}?type=audio"
# Use this URL directly in PyTgCalls / GroupCall / FFmpeg
```

---

**Made with ⚡ by @flexyy**
