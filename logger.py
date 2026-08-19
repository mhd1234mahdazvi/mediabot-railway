"""
Logging setup. Sends logs to:
1. stdout (Railway captures this)
2. PostgreSQL bot_logs table (with traceback for exceptions)
3. WebSocket broadcast (web panel real-time view)
"""

import logging
import asyncio
import traceback
from typing import Callable, Awaitable

# WebSocket broadcaster — set by web server at startup
_ws_broadcast: Callable[[dict], Awaitable[None]] | None = None


def set_ws_broadcaster(fn: Callable[[dict], Awaitable[None]]):
    global _ws_broadcast
    _ws_broadcast = fn


class DBAndWSHandler(logging.Handler):
    """Async-safe handler: schedules DB insert + WS broadcast on the running event loop."""

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        tb = None
        if record.exc_info and record.exc_info[2]:
            tb = "".join(traceback.format_exception(*record.exc_info))
        entry = {
            "level": record.levelname,
            "logger": record.name,
            "message": msg,
            "traceback": tb,
            "time": record.created,
        }
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._async_emit(entry))
        except RuntimeError:
            pass

    async def _async_emit(self, entry: dict):
        import database as db
        await db.insert_log(
            entry["level"],
            entry["logger"],
            entry["message"],
            entry.get("traceback"),
        )
        if _ws_broadcast:
            try:
                await _ws_broadcast(entry)
            except Exception:
                pass


def setup_logging():
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    stream = logging.StreamHandler()
    stream.setFormatter(fmt)

    db_ws = DBAndWSHandler()
    db_ws.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(stream)
    root.addHandler(db_ws)

    # quiet down pyrogram's noise a bit
    logging.getLogger("pyrogram").setLevel(logging.WARNING)