from fastapi import APIRouter, Depends
from pydantic import BaseModel
from web.auth import require_auth
import database as db

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/platforms")
async def get_platforms(_=Depends(require_auth)):
    return await db.get_platform_settings()


@router.post("/platforms/{platform}/toggle")
async def toggle_platform(platform: str, _=Depends(require_auth)):
    settings = await db.get_platform_settings()
    current = settings.get(platform, True)
    await db.toggle_platform(platform, not current)
    return {"platform": platform, "enabled": not current}


class DefaultsRequest(BaseModel):
    default_max_file_mb: int | None = None
    default_daily_limit_mb: int | None = None
    default_queue_limit: int | None = None


@router.get("/defaults")
async def get_defaults(_=Depends(require_auth)):
    keys = ["default_max_file_mb", "default_daily_limit_mb", "default_queue_limit"]
    result = {}
    for k in keys:
        result[k] = await db.get_bot_setting(k)
    return result


@router.put("/defaults")
async def update_defaults(body: DefaultsRequest, _=Depends(require_auth)):
    if body.default_max_file_mb is not None:
        await db.set_bot_setting("default_max_file_mb", str(body.default_max_file_mb))
    if body.default_daily_limit_mb is not None:
        await db.set_bot_setting("default_daily_limit_mb", str(body.default_daily_limit_mb))
    if body.default_queue_limit is not None:
        await db.set_bot_setting("default_queue_limit", str(body.default_queue_limit))
    return {"ok": True}
