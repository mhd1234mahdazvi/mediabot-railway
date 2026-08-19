import asyncpg
import asyncio
import os
from datetime import datetime, date, timedelta
from typing import Optional
import config

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(config.DATABASE_URL, min_size=2, max_size=10)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id     BIGINT PRIMARY KEY,
                username        TEXT,
                display_name    TEXT,
                is_active       BOOLEAN DEFAULT TRUE,
                is_banned       BOOLEAN DEFAULT FALSE,
                ban_message     TEXT,
                max_file_mb     INTEGER DEFAULT NULL,
                daily_limit_mb  INTEGER DEFAULT NULL,
                queue_limit     INTEGER DEFAULT NULL,
                added_by        BIGINT,
                added_at        TIMESTAMPTZ DEFAULT NOW(),
                last_seen       TIMESTAMPTZ
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS download_log (
                id              BIGSERIAL PRIMARY KEY,
                telegram_id     BIGINT REFERENCES users(telegram_id),
                url             TEXT,
                platform        TEXT,
                file_size_mb    FLOAT,
                status          TEXT,  -- success | failed | cancelled
                created_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS upload_cache (
                job_id          TEXT PRIMARY KEY,
                telegram_id     BIGINT REFERENCES users(telegram_id),
                file_path       TEXT,
                url             TEXT,
                created_at      TIMESTAMPTZ DEFAULT NOW(),
                expires_at      TIMESTAMPTZ
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS platform_settings (
                platform        TEXT PRIMARY KEY,
                enabled         BOOLEAN DEFAULT TRUE,
                updated_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key             TEXT PRIMARY KEY,
                value           TEXT,
                updated_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                id              SERIAL PRIMARY KEY,
                token           TEXT UNIQUE NOT NULL,
                bot_username    TEXT,
                bot_name        TEXT,
                is_active       BOOLEAN DEFAULT TRUE,
                added_at        TIMESTAMPTZ DEFAULT NOW(),
                last_seen       TIMESTAMPTZ
            )
        """)

        # seed bots from env
        if os.environ.get("BOT_TOKEN"):
            await conn.execute("""
                INSERT INTO bots (token) VALUES ($1)
                ON CONFLICT (token) DO NOTHING
            """, os.environ["BOT_TOKEN"])

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_logs (
                id          BIGSERIAL PRIMARY KEY,
                level       TEXT NOT NULL,
                logger      TEXT,
                message     TEXT NOT NULL,
                traceback   TEXT,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS bot_logs_created_idx ON bot_logs (created_at DESC)
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS link_history (
                id              BIGSERIAL PRIMARY KEY,
                telegram_id     BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,
                username        TEXT,
                display_name    TEXT,
                url             TEXT NOT NULL,
                title           TEXT,
                platform        TEXT,
                quality         TEXT,
                file_size_mb    FLOAT,
                status          TEXT,
                created_at      TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS link_history_created_idx ON link_history (created_at DESC)
        """)

        # seed platform_settings from config defaults
        for platform, enabled in config.DEFAULT_PLATFORMS.items():
            await conn.execute("""
                INSERT INTO platform_settings (platform, enabled)
                VALUES ($1, $2)
                ON CONFLICT (platform) DO NOTHING
            """, platform, enabled)

        # seed default bot settings
        defaults = {
            "default_max_file_mb": str(config.DEFAULT_MAX_FILE_SIZE_MB),
            "default_daily_limit_mb": str(config.DEFAULT_DAILY_LIMIT_MB),
            "default_queue_limit": str(config.DEFAULT_QUEUE_LIMIT),
        }
        for key, value in defaults.items():
            await conn.execute("""
                INSERT INTO bot_settings (key, value)
                VALUES ($1, $2)
                ON CONFLICT (key) DO NOTHING
            """, key, value)


# ─── User queries ────────────────────────────────────────────────────────────

async def get_user(telegram_id: int) -> Optional[asyncpg.Record]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1", telegram_id
        )


async def add_user(telegram_id: int, username: str, display_name: str, added_by: int) -> asyncpg.Record:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            INSERT INTO users (telegram_id, username, display_name, added_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (telegram_id) DO UPDATE
                SET username = $2, display_name = $3, is_active = TRUE, is_banned = FALSE
            RETURNING *
        """, telegram_id, username, display_name, added_by)


async def remove_user(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET is_active = FALSE WHERE telegram_id = $1", telegram_id
        )


async def ban_user(telegram_id: int, message: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET is_banned = TRUE, ban_message = $2
            WHERE telegram_id = $1
        """, telegram_id, message)


async def unban_user(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET is_banned = FALSE, ban_message = NULL
            WHERE telegram_id = $1
        """, telegram_id)


async def set_user_limit(telegram_id: int, max_file_mb: Optional[int], daily_limit_mb: Optional[int], queue_limit: Optional[int]):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users
            SET max_file_mb = $2, daily_limit_mb = $3, queue_limit = $4
            WHERE telegram_id = $1
        """, telegram_id, max_file_mb, daily_limit_mb, queue_limit)


async def list_users() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM users ORDER BY added_at DESC"
        )


async def update_last_seen(telegram_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET last_seen = NOW() WHERE telegram_id = $1", telegram_id
        )


async def is_authorized(telegram_id: int) -> tuple[bool, str]:
    """Returns (authorized, reason). reason is 'ok' | 'not_found' | 'inactive' | 'banned'"""
    if telegram_id == config.ADMIN_ID:
        return True, "ok"
    user = await get_user(telegram_id)
    if not user:
        return False, "not_found"
    if user["is_banned"]:
        return False, "banned"
    if not user["is_active"]:
        return False, "inactive"
    return True, "ok"


# ─── Limit queries ────────────────────────────────────────────────────────────

async def get_user_limits(telegram_id: int) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
        settings = await conn.fetch("SELECT key, value FROM bot_settings")
        defaults = {row["key"]: row["value"] for row in settings}

        return {
            "max_file_mb": user["max_file_mb"] if user and user["max_file_mb"] else int(defaults.get("default_max_file_mb", config.DEFAULT_MAX_FILE_SIZE_MB)),
            "daily_limit_mb": user["daily_limit_mb"] if user and user["daily_limit_mb"] else int(defaults.get("default_daily_limit_mb", config.DEFAULT_DAILY_LIMIT_MB)),
            "queue_limit": user["queue_limit"] if user and user["queue_limit"] else int(defaults.get("default_queue_limit", config.DEFAULT_QUEUE_LIMIT)),
        }


async def get_daily_usage_mb(telegram_id: int) -> float:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval("""
            SELECT COALESCE(SUM(file_size_mb), 0)
            FROM download_log
            WHERE telegram_id = $1
              AND status = 'success'
              AND created_at >= CURRENT_DATE
        """, telegram_id)
        return float(result)


# ─── Download log ─────────────────────────────────────────────────────────────

async def log_download(telegram_id: int, url: str, platform: str, file_size_mb: float, status: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO download_log (telegram_id, url, platform, file_size_mb, status)
            VALUES ($1, $2, $3, $4, $5)
        """, telegram_id, url, platform, file_size_mb, status)


# ─── Stats ────────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
        total_downloads = await conn.fetchval("SELECT COUNT(*) FROM download_log WHERE status = 'success'")
        total_volume_mb = await conn.fetchval("SELECT COALESCE(SUM(file_size_mb), 0) FROM download_log WHERE status = 'success'")
        failed = await conn.fetchval("SELECT COUNT(*) FROM download_log WHERE status = 'failed'")
        today_downloads = await conn.fetchval("""
            SELECT COUNT(*) FROM download_log
            WHERE status = 'success' AND created_at >= CURRENT_DATE
        """)
        platform_breakdown = await conn.fetch("""
            SELECT platform, COUNT(*) as count
            FROM download_log WHERE status = 'success'
            GROUP BY platform ORDER BY count DESC
        """)

        return {
            "total_users": total_users,
            "total_downloads": total_downloads,
            "total_volume_gb": round(float(total_volume_mb) / 1024, 2),
            "failed": failed,
            "today_downloads": today_downloads,
            "platforms": {row["platform"]: row["count"] for row in platform_breakdown},
        }


# ─── Platform settings ────────────────────────────────────────────────────────

async def get_platform_settings() -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT platform, enabled FROM platform_settings")
        return {row["platform"]: row["enabled"] for row in rows}


async def toggle_platform(platform: str, enabled: bool):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE platform_settings SET enabled = $2, updated_at = NOW()
            WHERE platform = $1
        """, platform, enabled)


# ─── Bot settings ─────────────────────────────────────────────────────────────

async def get_bot_setting(key: str) -> Optional[str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT value FROM bot_settings WHERE key = $1", key)


async def set_bot_setting(key: str, value: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO bot_settings (key, value, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()
        """, key, value)


# ─── Upload cache ─────────────────────────────────────────────────────────────

async def cache_failed_upload(job_id: str, telegram_id: int, file_path: str, url: str):
    pool = await get_pool()
    expires = datetime.utcnow() + timedelta(hours=config.CACHE_TTL_HOURS)
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO upload_cache (job_id, telegram_id, file_path, url, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (job_id) DO UPDATE SET file_path = $3, expires_at = $5
        """, job_id, telegram_id, file_path, url, expires)


async def get_cached_upload(job_id: str) -> Optional[asyncpg.Record]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM upload_cache
            WHERE job_id = $1 AND expires_at > NOW()
        """, job_id)


async def delete_cached_upload(job_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM upload_cache WHERE job_id = $1", job_id)


async def cleanup_expired_cache():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM upload_cache WHERE expires_at <= NOW()")


# ─── Bot logs ─────────────────────────────────────────────────────────────────

async def insert_log(level: str, logger: str, message: str, traceback: Optional[str] = None):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO bot_logs (level, logger, message, traceback)
                VALUES ($1, $2, $3, $4)
            """, level, logger, message, traceback)
    except Exception:
        pass  # never crash the bot because of a logging failure


async def get_logs(limit: int = 200, level: Optional[str] = None, search: Optional[str] = None) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        conditions = []
        args = []
        idx = 1
        if level and level != "ALL":
            conditions.append(f"level = ${idx}")
            args.append(level)
            idx += 1
        if search:
            conditions.append(f"message ILIKE ${idx}")
            args.append(f"%{search}%")
            idx += 1
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        args.append(limit)
        return await conn.fetch(f"""
            SELECT id, level, logger, message, traceback, created_at
            FROM bot_logs
            {where}
            ORDER BY created_at DESC
            LIMIT ${idx}
        """, *args)


async def clear_logs():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM bot_logs")


async def cleanup_old_logs(days: int = 14):
    """Archive old log rows to keep the bot_logs table small."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM bot_logs WHERE created_at < NOW() - ($1 || ' days')::interval",
                days,
            )
    except Exception:
        pass


# ─── Link history ─────────────────────────────────────────────────────────────

async def insert_link_history(
    telegram_id: int,
    username: str,
    display_name: str,
    url: str,
    title: Optional[str],
    platform: str,
    quality: Optional[str],
    file_size_mb: float,
    status: str,
):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO link_history
                    (telegram_id, username, display_name, url, title, platform, quality, file_size_mb, status)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            """, telegram_id, username, display_name, url, title, platform, quality, file_size_mb, status)
    except Exception:
        pass


async def get_link_history(
    limit: int = 100,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        conditions = []
        args = []
        idx = 1
        if platform and platform != "ALL":
            conditions.append(f"platform = ${idx}")
            args.append(platform)
            idx += 1
        if status and status != "ALL":
            conditions.append(f"status = ${idx}")
            args.append(status)
            idx += 1
        if search:
            conditions.append(f"(url ILIKE ${idx} OR title ILIKE ${idx} OR username ILIKE ${idx})")
            args.append(f"%{search}%")
            idx += 1
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        args.append(limit)
        return await conn.fetch(f"""
            SELECT id, telegram_id, username, display_name, url, title,
                   platform, quality, file_size_mb, status, created_at
            FROM link_history
            {where}
            ORDER BY created_at DESC
            LIMIT ${idx}
        """, *args)


# ─── Bots (multi-token) ───────────────────────────────────────────────────────

async def list_bots() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM bots ORDER BY added_at DESC"
        )


async def add_bot(token: str) -> asyncpg.Record:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            INSERT INTO bots (token) VALUES ($1)
            ON CONFLICT (token) DO NOTHING
            RETURNING *
        """, token.strip())


async def remove_bot(bot_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM bots WHERE id = $1", bot_id)


async def toggle_bot(bot_id: int, active: bool):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE bots SET is_active = $2 WHERE id = $1", bot_id, active
        )


async def update_bot_meta(bot_id: int, username: Optional[str], name: Optional[str]):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE bots SET bot_username = $2, bot_name = $3, last_seen = NOW()
            WHERE id = $1
        """, bot_id, username, name)


# ─── Bot pause state ──────────────────────────────────────────────────────────

async def is_bot_paused() -> bool:
    val = await get_bot_setting("bot_paused")
    return val == "true"


async def set_bot_paused(paused: bool):
    await set_bot_setting("bot_paused", "true" if paused else "false")
