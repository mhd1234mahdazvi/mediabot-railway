from typing import Optional
from fastapi import APIRouter, Depends, Query
from web.auth import require_auth
import database as db

router = APIRouter(prefix="/api/links", tags=["links"])


@router.get("")
async def get_links(
    limit: int = Query(100, le=500),
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    _=Depends(require_auth),
):
    rows = await db.get_link_history(limit=limit, platform=platform, status=status, search=search)
    return [
        {
            "id": r["id"],
            "telegram_id": r["telegram_id"],
            "username": r["username"],
            "display_name": r["display_name"],
            "url": r["url"],
            "title": r["title"],
            "platform": r["platform"],
            "quality": r["quality"],
            "file_size_mb": r["file_size_mb"],
            "status": r["status"],
            "time": r["created_at"].isoformat(),
        }
        for r in rows
    ]
