# MediaBot — Telegram Media Downloader

Plugin-based Telegram bot. Supports YouTube, Instagram, TikTok, X/Twitter, and direct URLs.
Runs on Railway with PostgreSQL. Pyrogram MTProto — uploads up to 2GB.

---

## Railway Setup (5 minutes)

### 1. Create Railway project
- Go to railway.app → New Project → Deploy from GitHub repo

### 2. Add PostgreSQL
- Inside your project → **+ New** → **Database** → **PostgreSQL**
- Railway automatically sets `DATABASE_URL` environment variable

### 3. Set environment variables
In Railway → your service → **Variables**, add:

| Variable | Where to get it |
|---|---|
| `API_ID` | https://my.telegram.org → API Development Tools |
| `API_HASH` | Same as above |
| `BOT_TOKEN` | @BotFather on Telegram |
| `ADMIN_ID` | Your numeric Telegram ID — get it from @userinfobot |

`DATABASE_URL` is set automatically by the PostgreSQL addon.

### 4. Deploy
Push to GitHub → Railway auto-deploys.

---

## Adding a New Platform (Plugin)

Create `plugins/mysite.py`:

```python
from .base import BasePlugin
import yt_dlp, asyncio, os

class MySitePlugin(BasePlugin):
    PLATFORM_NAME = "mysite"
    SUPPORTED_DOMAINS = ["mysite.com", "www.mysite.com"]
    PRIORITY = 10

    async def get_info(self, url: str):
        # return metadata dict or None
        ...

    async def download(self, url: str, quality: str, dest_dir: str):
        # download to dest_dir, return file path or None
        ...
```

That's it. No other file needs editing. The plugin loader picks it up automatically on next deploy.

---

## Admin Commands

| Command | Description |
|---|---|
| `/admin` | Open inline admin panel |
| `/adduser @username` | Add user by username |
| `/adduser 123456789` | Add user by ID |
| `/removeuser 123456789` | Remove user (they get a notification) |
| `/banuser 123456789 message` | Ban with custom message |
| `/unbanuser 123456789` | Restore access |
| `/setlimit 123456789 1024 5120 5` | Set per-user limits (file MB, daily MB, queue) |
| `/broadcast message` | Send message to all active users |
| `/setdefault max_file 500` | Change global default max file size |
| `/setdefault daily 2048` | Change global daily limit |
| `/setdefault queue 3` | Change global queue limit |

---

## Architecture

```
bot/
├── main.py              # entry point
├── config.py            # env vars
├── database.py          # PostgreSQL (asyncpg)
├── queue_manager.py     # per-user async queue
├── uploader.py          # upload + retry + cache
│
├── plugins/             # one file per platform
│   ├── base.py          # BasePlugin interface
│   ├── youtube.py
│   ├── instagram.py
│   ├── twitter.py
│   ├── tiktok.py
│   └── direct_url.py    # fallback for direct links
│
├── admin/
│   ├── panel.py         # inline keyboard admin UI
│   ├── users.py         # user management commands
│   └── broadcast.py
│
└── handlers/
    ├── message.py       # link detection + quality keyboard
    └── callbacks.py     # inline button callbacks
```
