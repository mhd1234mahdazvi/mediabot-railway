from fastapi import APIRouter, Depends
from web.auth import require_auth
import database as db

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats(_=Depends(require_auth)):
    return await db.get_stats()


@router.get("/bot-status")
async def bot_status(_=Depends(require_auth)):
    paused = await db.is_bot_paused()
    return {"paused": paused}


@router.post("/bot-pause")
async def pause_bot(_=Depends(require_auth)):
    await db.set_bot_paused(True)
    return {"ok": True, "paused": True}


@router.post("/bot-resume")
async def resume_bot(_=Depends(require_auth)):
    await db.set_bot_paused(False)
    return {"ok": True, "paused": False}
