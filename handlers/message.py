import uuid
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import config
import database as db
from queue_manager import DownloadJob, enqueue, make_job_dir
from uploader import upload_file, retry_cached_upload
import plugins as plugin_registry

URL_PATTERN = re.compile(r"https?://[^\s]+")

# in-memory pending quality selections: job_id -> partial DownloadJob
_pending: dict[str, DownloadJob] = {}


def register(app: Client):

    @app.on_message(filters.text & filters.private & ~filters.command([
        "start", "help", "admin", "retry"
    ]))
    async def handle_text(client: Client, message: Message):
        user_id = message.from_user.id

        if await db.is_bot_paused():
            await message.reply("🔴 Bot is currently paused by admin.")
            return

        authorized, reason = await db.is_authorized(user_id)
        if not authorized:
            if reason == "banned":
                user = await db.get_user(user_id)
                ban_msg = user["ban_message"] if user and user["ban_message"] else config.MSG_BANNED
                await message.reply(ban_msg)
            else:
                await message.reply(config.MSG_NO_ACCESS)
            return

        await db.update_last_seen(user_id)

        urls = URL_PATTERN.findall(message.text)
        if not urls:
            await message.reply("یک لینک بفرستید تا دانلود کنم.")
            return

        url = urls[0]

        # platform enabled check
        platform_settings = await db.get_platform_settings()

        handler = await plugin_registry.get_handler_async(url)
        if not handler:
            await message.reply("❌ لینک پشتیبانی‌نشده. یوتیوب، اینستاگرام، تیک‌تاک، X یا لینک مستقیم فایل امتحان کنید.")
            return

        platform = handler.PLATFORM_NAME
        if not platform_settings.get(platform, True):
            await message.reply(config.MSG_PLATFORM_DISABLED)
            return

        # queue limit check before doing any work
        limits = await db.get_user_limits(user_id)
        from queue_manager import get_user_active_count
        if get_user_active_count(user_id) >= limits["queue_limit"]:
            await message.reply(
                config.MSG_QUEUE_FULL.format(limit=limits["queue_limit"])
            )
            return

        # build partial job — quality TBD
        job_id = str(uuid.uuid4())[:8]
        job = DownloadJob(
            job_id=job_id,
            telegram_id=user_id,
            url=url,
            platform=platform,
            quality=None,
            chat_id=message.chat.id,
            message_id=0,
        )
        _pending[job_id] = job

        # send quality selection keyboard
        quality_opts = handler.get_quality_options()
        buttons = [
            [InlineKeyboardButton(opt["label"], callback_data=f"quality:{job_id}:{opt['value']}")]
            for opt in quality_opts
        ]
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{job_id}")])

        await message.reply(
            f"🔗 لینک **{handler.PLATFORM_NAME.title()}** تشخیص داده شد.\nکیفیت را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    @app.on_message(filters.command("retry") & filters.private)
    async def handle_retry_command(client: Client, message: Message):
        user_id = message.from_user.id
        authorized, _ = await db.is_authorized(user_id)
        if not authorized:
            return

        parts = message.text.split("_", 1)
        if len(parts) < 2:
            await message.reply("Usage: /retry_<job_id>")
            return

        job_id = parts[1].strip()
        status_msg = await message.reply("🔄 در حال تلاش دوباره برای آپلود...")
        await retry_cached_upload(client, job_id, user_id, status_msg)


async def dispatch_download(client: Client, job: DownloadJob, quality: str, status_msg):
    """Called from callbacks.py after quality is selected."""
    job.quality = quality
    job.message_id = status_msg.id

    handler = plugin_registry.get_handler(job.url)
    if not handler:
        await status_msg.edit_text("❌ پلاگین برای این لینک پیدا نشد.")
        _pending.pop(job.job_id, None)
        return

    async def download_fn(j: DownloadJob) -> bool:
        dest_dir = make_job_dir(j.job_id)
        path = await handler.download(j.url, j.quality, dest_dir)
        if path:
            j.file_path = path
            return True
        return False

    async def on_done(j: DownloadJob):
        if j.status == "uploading":
            await upload_file(client, j, status_msg)
            user = await db.get_user(j.telegram_id)
            uname = user["username"] if user else ""
            dname = user["display_name"] if user else str(j.telegram_id)
            info = await handler.get_info(j.url)
            title = info.get("title") if info else None
            final_status = "success" if j.file_size_mb > 0 else "failed"
            await db.insert_link_history(
                telegram_id=j.telegram_id,
                username=uname or "",
                display_name=dname or "",
                url=j.url,
                title=title,
                platform=j.platform,
                quality=j.quality,
                file_size_mb=j.file_size_mb,
                status=final_status,
            )
        elif j.status == "failed_size":
            limits = await db.get_user_limits(j.telegram_id)
            await status_msg.edit_text(
                config.MSG_FILE_TOO_LARGE.format(
                    size=round(j.file_size_mb, 1),
                    limit=limits["max_file_mb"],
                )
            )
        elif j.status == "failed_daily":
            limits = await db.get_user_limits(j.telegram_id)
            used = await db.get_daily_usage_mb(j.telegram_id)
            await status_msg.edit_text(
                config.MSG_DAILY_LIMIT.format(
                    used=round(used, 1),
                    limit=limits["daily_limit_mb"],
                )
            )
        elif j.status == "cancelled":
            await status_msg.edit_text("🚫 دانلود لغو شد.")
        else:
            await status_msg.edit_text(config.MSG_FAILED)

    queued = await enqueue(job, download_fn, on_done)
    if not queued:
        limits = await db.get_user_limits(job.telegram_id)
        await status_msg.edit_text(
            config.MSG_QUEUE_FULL.format(limit=limits["queue_limit"])
        )

    _pending.pop(job.job_id, None)


def get_pending(job_id: str):
    return _pending.get(job_id)


def remove_pending(job_id: str):
    _pending.pop(job_id, None)
