import os
import asyncio
from typing import Optional

import yt_dlp

from .base import BasePlugin
import config


class YouTubePlugin(BasePlugin):
    PLATFORM_NAME = "youtube"
    SUPPORTED_DOMAINS = ["youtube.com", "youtu.be", "www.youtube.com", "m.youtube.com"]
    PRIORITY = 10

    _QUALITY_FORMAT_MAP = {
        "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "720p":  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480p":  "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]",
        "audio": "bestaudio[ext=m4a]/bestaudio",
    }

    def _base_opts(self, dest_dir: str, quality: str) -> dict:
        fmt = self._QUALITY_FORMAT_MAP.get(quality, self._QUALITY_FORMAT_MAP["720p"])
        outtmpl = os.path.join(dest_dir, "%(title)s.%(ext)s")

        opts = {
            "format": fmt,
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "merge_output_format": "mp4",
            "postprocessors": [],
            "socket_timeout": 30,
        }

        if quality == "audio":
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
            opts["outtmpl"] = os.path.join(dest_dir, "%(title)s.%(ext)s")

        return opts

    async def get_info(self, url: str) -> Optional[dict]:
        def _fetch():
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await asyncio.get_event_loop().run_in_executor(None, _fetch)
            return {
                "title": info.get("title", "Unknown"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "platform": self.PLATFORM_NAME,
                "has_video": True,
                "has_audio": True,
            }
        except Exception:
            return None

    async def download(self, url: str, quality: str, dest_dir: str) -> Optional[str]:
        opts = self._base_opts(dest_dir, quality)

        def _do_download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        try:
            filename = await asyncio.get_event_loop().run_in_executor(None, _do_download)

            # yt-dlp may change extension after merge/postprocess
            if not os.path.exists(filename):
                files = os.listdir(dest_dir)
                if files:
                    filename = os.path.join(dest_dir, files[0])
                else:
                    return None

            return filename
        except Exception:
            return None
