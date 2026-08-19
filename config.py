import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")  # multi-bot: توکن‌ها از پنل اضافه می‌شوند
ADMIN_ID = int(os.environ["ADMIN_ID"])  # your telegram numeric ID

# --- Database ---
DATABASE_URL = os.environ["DATABASE_URL"]  # set by Railway PostgreSQL addon

# --- Download limits (overridable per-user in DB) ---
DEFAULT_MAX_FILE_SIZE_MB = int(os.getenv("DEFAULT_MAX_FILE_SIZE_MB", "500"))
DEFAULT_DAILY_LIMIT_MB = int(os.getenv("DEFAULT_DAILY_LIMIT_MB", "2048"))
DEFAULT_QUEUE_LIMIT = int(os.getenv("DEFAULT_QUEUE_LIMIT", "3"))

# --- Queue ---
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))

# --- Retry / Cache ---
UPLOAD_MAX_RETRIES = 3
UPLOAD_RETRY_DELAY = 5  # seconds between retries
CACHE_TTL_HOURS = 24    # how long to keep failed-upload cache entries

# --- Temp storage ---
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/mediabot")

# --- Platforms enabled by default ---
DEFAULT_PLATFORMS = {
    "youtube": True,
    "instagram": True,
    "twitter": True,
    "tiktok": True,
    "direct_url": True,
}

# --- Bot messages (فارسی) ---
MSG_NO_ACCESS = "⛔ شما به این ربات دسترسی ندارید."
MSG_BANNED = "🚫 دسترسی شما به این ربات تعلیق شده است."
MSG_QUEUE_FULL = "⏳ صف دانلود شما پر است (حداکثر {limit}). لطفاً منتظر پایان دانلودهای فعلی بمانید."
MSG_FILE_TOO_LARGE = "❌ حجم فایل از حد مجاز شما بیشتر است ({size}MB / {limit}MB)."
MSG_DAILY_LIMIT = "📊 به سقف دانلود روزانه رسیده‌اید ({used}MB / {limit}MB)."
MSG_PLATFORM_DISABLED = "❌ این پلتفرم فعلاً غیرفعال است."
MSG_DOWNLOAD_START = "⬇️ دانلود شروع شد..."
MSG_UPLOAD_START = "📤 در حال آپلود به تلگرام..."
MSG_DONE = "✅ انجام شد!"
MSG_FAILED = "❌ دانلود ناموفق بود. لطفاً دوباره تلاش کنید."
MSG_RETRY = "🔄 آپلود ناموفق بود. تلاش مجدد ({attempt}/{max})..."
MSG_UPLOAD_FAILED_CACHE = "❌ آپلود پس از {max} بار تلاش ناموفق بود. فایل شما ذخیره شده — برای تلاش دوباره /retry_{job_id} را بفرستید."
MSG_WELCOME = (
    "👋 ربات دانلودر مدیا\n\n"
    "هر لینکی بفرستید تا دانلود کنم:\n"
    "• ویدیوهای یوتیوب\n"
    "• پست‌ها و استوری‌های اینستاگرام\n"
    "• ویدیوهای تیک‌تاک\n"
    "• ویدیوهای X / توییتر\n"
    "• لینک مستقیم فایل\n\n"
    "بعد از ارسال لینک، کیفیت را انتخاب کنید."
)
MSG_HELP = (
    "**نحوه استفاده:**\n"
    "1. یک لینک بفرستید\n"
    "2. کیفیت را از دکمه‌ها انتخاب کنید\n"
    "3. منتظر آپلود بمانید\n\n"
    "**دستورها:**\n"
    "/start — خوش‌آمد\n"
    "/help — همین راهنما\n"
    "/retry_شناسه — تلاش دوباره برای آپلود ناموفق"
)