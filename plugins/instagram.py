import os
import asyncio
from typing import Optional

import yt_dlp

from .base import BasePlugin


class InstagramPlugin(BasePlugin):
    PLATFORM_NAME = "instagram"
    SUPPORTED_DOMAINS = ["instagram.com", "www.instagram.com"]
    PRIORITY = 10

    # Instagram is video-only from yt-dlp; no separate quality ladder
    QUALITY_OPTIONS = [
        {"label": "🎬 Best Quality", "value": "best"},
        {"label": "🎵 Audio Only",   "value": "audio"},
    ]

    _QUALITY_FORMAT_MAP = {
        "best":  "bestvideo+bestaudio/best",
        "audio": "bestaudio",
    }

    def _opts(self, dest_dir: str, quality: str) -> dict:
        fmt = self._QUALITY_FORMAT_MAP.get(quality, "best")
        opts = {
            "format": fmt,
            "outtmpl": os.path.join(dest_dir, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "merge_output_format": "mp4",
            "socket_timeout": 30,
        }
        if quality == "audio":
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        return opts

    async def get_info(self, url: str) -> Optional[dict]:
        def _fetch():
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.get_event_loop().run_in_executor(None, _fetch)
            return {
                "title": info.get("title") or info.get("description") or "Instagram Post",
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "platform": self.PLATFORM_NAME,
                "has_video": True,
                "has_audio": True,
            }
        except Exception:
            return None

    async def download(self, url: str, quality: str, dest_dir: str) -> Optional[str]:
        # normalize quality: 1080p/720p/480p all map to "best" for Instagram
        if quality not in ("audio",):
            quality = "best"

        opts = self._opts(dest_dir, quality)

        def _do_download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        try:
            filename = await asyncio.get_event_loop().run_in_executor(None, _do_download)
            if not os.path.exists(filename):
                files = os.listdir(dest_dir)
                if files:
                    filename = os.path.join(dest_dir, files[0])
                else:
                    return None
            return filename
        except Exception:
            return None
