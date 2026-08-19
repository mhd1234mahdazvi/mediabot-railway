import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from web.auth import verify_credentials, create_token
from web.routes import logs as logs_route
from web.routes import users as users_route
from web.routes import stats as stats_route
from web.routes import links as links_route
from web.routes import settings as settings_route
from web.routes import bots as bots_route
from logger import set_ws_broadcaster

app = FastAPI(title="MediaBot Panel", docs_url=None, redoc_url=None)

# wire WebSocket broadcaster from logs route into logger
set_ws_broadcaster(logs_route.broadcast_log)

# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
async def login(body: LoginRequest):
    if not verify_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_token(body.username)}


# ─── API routes ───────────────────────────────────────────────────────────────

app.include_router(logs_route.router)
app.include_router(users_route.router)
app.include_router(stats_route.router)
app.include_router(links_route.router)
app.include_router(settings_route.router)
app.include_router(bots_route.router)


# ─── React frontend ───────────────────────────────────────────────────────────

_FRONTEND = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(_FRONTEND):
    app.mount("/assets", StaticFiles(directory=os.path.join(_FRONTEND, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        # API routes are handled above; everything else → index.html
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        index = os.path.join(_FRONTEND, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        raise HTTPException(status_code=404)
else:
    @app.get("/")
    async def no_frontend():
        return JSONResponse({"status": "API running. Frontend not built yet."})
