import os
import asyncio
import uuid
import mimetypes
from typing import Optional

from pyrogram import Client
from pyrogram.types import Message

import config
import database as db
from queue_manager import DownloadJob, _cleanup_job_file


async def upload_file(
    client: Client,
    job: DownloadJob,
    status_message: Message,
) -> bool:
    """
    Upload job.file_path to Telegram. Retries on failure.
    On permanent failure: caches file path in DB, notifies user with /retry_<job_id>.
    On success: logs download, deletes temp file, returns True.
    """
    if not job.file_path or not os.path.exists(job.file_path):
        await _edit(status_message, "❌ فایل پس از دانلود پیدا نشد.")
        return False

    for attempt in range(1, config.UPLOAD_MAX_RETRIES + 1):
        try:
            await _edit(status_message, f"📤 در حال آپلود... (تلاش {attempt}/{config.UPLOAD_MAX_RETRIES})")
            await _send_file(client, job, status_message)

            # success — log and clean up
            await db.log_download(job.telegram_id, job.url, job.platform, job.file_size_mb, "success")
            _cleanup_job_file(job)
            await _edit(status_message, config.MSG_DONE)
            return True

        except Exception as e:
            if attempt < config.UPLOAD_MAX_RETRIES:
                await _edit(
                    status_message,
                    config.MSG_RETRY.format(attempt=attempt, max=config.UPLOAD_MAX_RETRIES)
                )
                await asyncio.sleep(config.UPLOAD_RETRY_DELAY)
            else:
                # all retries exhausted — cache and notify
                await db.cache_failed_upload(job.job_id, job.telegram_id, job.file_path, job.url)
                await _edit(
                    status_message,
                    config.MSG_UPLOAD_FAILED_CACHE.format(
                        max=config.UPLOAD_MAX_RETRIES,
                        job_id=job.job_id,
                    )
                )
                return False

    return False


async def _send_file(client: Client, job: DownloadJob, status_message: Message):
    path = job.file_path
    chat_id = job.chat_id
    caption = f"✅ دانلود شده از طریق @{(await client.get_me()).username}"

    mime, _ = mimetypes.guess_type(path)
    ext = os.path.splitext(path)[1].lower()

    video_exts = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".flv", ".m4v"}
    audio_exts = {".mp3", ".m4a", ".ogg", ".flac", ".wav", ".opus"}
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    if ext in video_exts:
        await client.send_video(
            chat_id=chat_id,
            video=path,
            caption=caption,
            supports_streaming=True,
            progress=_make_progress_callback(status_message, "📤 Uploading video"),
        )
    elif ext in audio_exts:
        await client.send_audio(
            chat_id=chat_id,
            audio=path,
            caption=caption,
            progress=_make_progress_callback(status_message, "📤 Uploading audio"),
        )
    elif ext in image_exts:
        await client.send_photo(
            chat_id=chat_id,
            photo=path,
            caption=caption,
        )
    else:
        await client.send_document(
            chat_id=chat_id,
            document=path,
            caption=caption,
            progress=_make_progress_callback(status_message, "📤 Uploading file"),
        )


def _make_progress_callback(status_message: Message, label: str):
    last_pct = [-1]

    async def progress(current, total):
        if total == 0:
            return
        pct = int(current / total * 100)
        # update every 10% to avoid flood
        if pct - last_pct[0] >= 10:
            last_pct[0] = pct
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            try:
                await status_message.edit_text(f"{label}\n[{bar}] {pct}%")
            except Exception:
                pass

    return progress


async def retry_cached_upload(client: Client, job_id: str, telegram_id: int, status_message: Message) -> bool:
    cached = await db.get_cached_upload(job_id)
    if not cached:
        await _edit(status_message, "❌ کش منقضی شده یا پیدا نشد. لطفاً لینک را دوباره بفرستید.")
        return False
    if cached["telegram_id"] != telegram_id:
        return False

    # reconstruct a minimal job for upload
    job = DownloadJob(
        job_id=job_id,
        telegram_id=telegram_id,
        url=cached["url"],
        platform="cached",
        quality=None,
        chat_id=status_message.chat.id,
        message_id=status_message.id,
        file_path=cached["file_path"],
    )

    if not os.path.exists(job.file_path):
        await _edit(status_message, "❌ فایل کش دیگر وجود ندارد. لطفاً لینک را دوباره بفرستید.")
        await db.delete_cached_upload(job_id)
        return False

    job.file_size_mb = os.path.getsize(job.file_path) / (1024 * 1024)
    success = await upload_file(client, job, status_message)
    if success:
        await db.delete_cached_upload(job_id)
    return success


async def _edit(message: Message, text: str):
    try:
        await message.edit_text(text)
    except Exception:
        pass
