"""
RukiaApiPro v2.0 PRO
Ultra Fast YouTube Streaming API
Developer : @flexyy
GitHub    : https://github.com/EuthleXO/RukiaAPI-Pro
Optimized for Paid Heroku Dynos
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import (
    APP_NAME, VERSION, DEVELOPER, STATIC_DIR, COOKIES_FILE, PORT, HOST
)
from app.routes import router

app = FastAPI(
    title=APP_NAME,
    description="Ultra-fast YouTube Streaming API | PRO Edition | No API Key",
    version=VERSION,
    docs_url="/swagger",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(router)


@app.on_event("startup")
async def startup():
    print(f"🚀 {APP_NAME} {VERSION} started")
    print(f"👨‍💻 Developer: {DEVELOPER}")
    print(f"🍪 Cookies: {'Loaded ✅' if COOKIES_FILE.exists() else 'Missing ⚠️  (add cookies.txt for best results)'}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, workers=1)
