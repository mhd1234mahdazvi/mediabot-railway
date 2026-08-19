import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from web.auth import require_auth
import database as db

router = APIRouter(prefix="/api/logs", tags=["logs"])

# connected WebSocket clients
_ws_clients: set[WebSocket] = set()


async def broadcast_log(entry: dict):
    """Called by logger.py when a new log line arrives."""
    dead = set()
    for ws in _ws_clients:
        try:
            await ws.send_text(json.dumps({
                "level": entry["level"],
                "logger": entry["logger"],
                "message": entry["message"],
                "traceback": entry.get("traceback"),
                "time": entry["time"],
            }))
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)


@router.get("")
async def get_logs(
    limit: int = Query(200, le=1000),
    level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    _=Depends(require_auth),
):
    rows = await db.get_logs(limit=limit, level=level, search=search)
    return [
        {
            "id": r["id"],
            "level": r["level"],
            "logger": r["logger"],
            "message": r["message"],
            "traceback": r["traceback"],
            "time": r["created_at"].isoformat(),
        }
        for r in rows
    ]


@router.delete("")
async def clear_logs(_=Depends(require_auth)):
    await db.clear_logs()
    return {"ok": True}


@router.websocket("/ws")
async def logs_ws(websocket: WebSocket):
    """
    Real-time log stream. Client must send JWT token as first message after connect.
    """
    await websocket.accept()
    try:
        # expect auth token as first message
        token_msg = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        from web.auth import _verify
        if not _verify(token_msg):
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    _ws_clients.add(websocket)
    try:
        while True:
            # keep connection alive, client can send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(websocket)
