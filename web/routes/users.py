from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from web.auth import require_auth
import database as db

router = APIRouter(prefix="/api/users", tags=["users"])


class AddUserRequest(BaseModel):
    telegram_id: int
    username: Optional[str] = ""
    display_name: Optional[str] = ""


class BanRequest(BaseModel):
    message: str


class LimitsRequest(BaseModel):
    max_file_mb: Optional[int] = None
    daily_limit_mb: Optional[int] = None
    queue_limit: Optional[int] = None


@router.get("")
async def list_users(_=Depends(require_auth)):
    users = await db.list_users()
    return [
        {
            "telegram_id": u["telegram_id"],
            "username": u["username"],
            "display_name": u["display_name"],
            "is_active": u["is_active"],
            "is_banned": u["is_banned"],
            "ban_message": u["ban_message"],
            "max_file_mb": u["max_file_mb"],
            "daily_limit_mb": u["daily_limit_mb"],
            "queue_limit": u["queue_limit"],
            "added_at": u["added_at"].isoformat() if u["added_at"] else None,
            "last_seen": u["last_seen"].isoformat() if u["last_seen"] else None,
        }
        for u in users
    ]


@router.post("")
async def add_user(body: AddUserRequest, _=Depends(require_auth)):
    import config
    await db.add_user(
        telegram_id=body.telegram_id,
        username=body.username or "",
        display_name=body.display_name or str(body.telegram_id),
        added_by=config.ADMIN_ID,
    )
    return {"ok": True}


@router.delete("/{telegram_id}")
async def remove_user(telegram_id: int, _=Depends(require_auth)):
    await db.remove_user(telegram_id)
    return {"ok": True}


@router.post("/{telegram_id}/ban")
async def ban_user(telegram_id: int, body: BanRequest, _=Depends(require_auth)):
    await db.ban_user(telegram_id, body.message)
    return {"ok": True}


@router.post("/{telegram_id}/unban")
async def unban_user(telegram_id: int, _=Depends(require_auth)):
    await db.unban_user(telegram_id)
    return {"ok": True}


@router.put("/{telegram_id}/limits")
async def set_limits(telegram_id: int, body: LimitsRequest, _=Depends(require_auth)):
    await db.set_user_limit(
        telegram_id,
        body.max_file_mb,
        body.daily_limit_mb,
        body.queue_limit,
    )
    return {"ok": True}


@router.get("/{telegram_id}/usage")
async def get_usage(telegram_id: int, _=Depends(require_auth)):
    used = await db.get_daily_usage_mb(telegram_id)
    limits = await db.get_user_limits(telegram_id)
    return {"used_mb": round(used, 2), **limits}
