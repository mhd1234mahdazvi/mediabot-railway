import asyncio
import os
import logging

import uvicorn
from pyrogram import Client

import config
import database as db
import plugins as plugin_registry
import handlers
import admin
from logger import setup_logging
from web.server import app as web_app

setup_logging()
log = logging.getLogger(__name__)

os.makedirs(config.TEMP_DIR, exist_ok=True)


def register_welcome_handlers(bot: Client):
    from pyrogram import filters
    from pyrogram.types import Message

    @bot.on_message(filters.command("start") & filters.private)
    async def cmd_start(client: Client, message: Message):
        if await db.is_bot_paused():
            await message.reply("🔴 ربات فعلاً توسط مدیر متوقف شده است. بعداً تلاش کنید.")
            return
        authorized, reason = await db.is_authorized(message.from_user.id)
        if not authorized:
            await message.reply(config.MSG_NO_ACCESS)
            return
        await message.reply(config.MSG_WELCOME, parse_mode="markdown")

    @bot.on_message(filters.command("help") & filters.private)
    async def cmd_help(client: Client, message: Message):
        authorized, _ = await db.is_authorized(message.from_user.id)
        if not authorized:
            return
        await message.reply(config.MSG_HELP, parse_mode="markdown")


async def start_all_bots() -> list[Client]:
    """Start every active bot token registered in the database."""
    started: list[Client] = []
    for row in await db.list_bots():
        if not row["is_active"]:
            continue
        token = row["token"]
        try:
            bot = Client(
                name=f"bot_{token[-6:]}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                bot_token=token,
                in_memory=True,
                workdir=config.TEMP_DIR,
            )
            handlers.register_all(bot)
            admin.register_all(bot)
            register_welcome_handlers(bot)
            await bot.start()
            me = await bot.get_me()
            await db.update_bot_meta(row["id"], me.username, me.first_name)
            log.info(f"Bot started: @{me.username} (id={row['id']})")
            started.append(bot)
        except Exception as e:
            log.error(f"Failed to start bot id={row['id']}: {type(e).__name__}: {e}")
    return started


async def run_bot():
    log.info("Initializing database...")
    await db.init_db()

    log.info("Loading plugins...")
    plugin_registry.load_plugins()
    loaded = [p.PLATFORM_NAME for p in plugin_registry.list_plugins()]
    log.info(f"Plugins loaded: {loaded}")

    log.info("Starting bots...")
    global bots
    bots = await start_all_bots()
    if not bots:
        log.warning("No bots started. Add a BOT_TOKEN via env or the web panel.")

    async def cache_cleanup_loop():
        while True:
            await asyncio.sleep(3600)
            await db.cleanup_expired_cache()
            await db.cleanup_old_logs(days=14)
            log.info("Expired cache & old logs cleaned.")

    asyncio.create_task(cache_cleanup_loop())
    await asyncio.Event().wait()


async def run_web():
    port = int(os.environ.get("PORT", "8080"))
    log.info(f"Starting web panel on port {port}...")
    serv = uvicorn.Config(web_app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(serv)
    await server.serve()


async def main():
    await asyncio.gather(run_bot(), run_web())


if __name__ == "__main__":
    asyncio.run(main())