from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from web.auth import require_auth
import database as db

router = APIRouter(prefix="/api/bots", tags=["bots"])


class AddBotRequest(BaseModel):
    token: str


@router.get("")
async def list_bots(_=Depends(require_auth)):
    rows = await db.list_bots()
    return [
        {
            "id": r["id"],
            "bot_username": r["bot_username"],
            "bot_name": r["bot_name"],
            "is_active": r["is_active"],
            "added_at": r["added_at"].isoformat() if r["added_at"] else None,
            "last_seen": r["last_seen"].isoformat() if r["last_seen"] else None,
            "token_preview": f"{r['token'][:6]}...{r['token'][-4:]}",
        }
        for r in rows
    ]


@router.post("")
async def add_bot(body: AddBotRequest, _=Depends(require_auth)):
    token = body.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="token is required")
    try:
        # validate format early: bot tokens look like 123456:ABC...
        if ":" not in token:
            raise HTTPException(status_code=400, detail="توکن معتبر نیست (قالب 123456:ABC...)")
        row = await db.add_bot(token)
    except Exception:
        raise HTTPException(status_code=400, detail="خطا در ذخیره توکن")
    if not row:
        raise HTTPException(status_code=409, detail="این توکن قبلاً ثبت شده است")
    return {"ok": True, "id": row["id"]}


@router.delete("/{bot_id}")
async def remove_bot(bot_id: int, _=Depends(require_auth)):
    await db.remove_bot(bot_id)
    return {"ok": True}


@router.post("/{bot_id}/toggle")
async def toggle_bot(bot_id: int, _=Depends(require_auth)):
    rows = await db.list_bots()
    target = next((r for r in rows if r["id"] == bot_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="ربات پیدا نشد")
    await db.toggle_bot(bot_id, not target["is_active"])
    return {"ok": True, "is_active": not target["is_active"]}