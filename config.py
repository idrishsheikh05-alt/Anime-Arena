import os
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN", "7553716587:AAFX2L1OMSWzVa98VUSm3C2nv_xnT_0Tg-U")

# Render PostgreSQL URLs start with postgres://; SQLAlchemy asyncpg requires postgresql+asyncpg://
_raw_db = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres@localhost/anime_arena")
if _raw_db.startswith("postgres://"):
    DATABASE_URL = _raw_db.replace("postgres://", "postgresql+asyncpg://", 1)
elif _raw_db.startswith("postgresql://") and "+asyncpg" not in _raw_db:
    DATABASE_URL = _raw_db.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = _raw_db

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
PORT = int(os.getenv("PORT", 8080))
BOT_OWNERS = {123456789}  # Replace with your Telegram numeric ID
IST = pytz.timezone("Asia/Kolkata")

LEVEL_TITLES = [
    (5, "🌱 Beginner"),
    (10, "🎌 Otaku"),
    (20, "⚔️ Anime Fan"),
    (30, "🔥 Anime Expert"),
    (50, "⚡ Elite"),
    (75, "🏆 Champion"),
    (100, "👑 Legend"),
    (999999, "🌌 Arena God"),
]

SHOP_CATALOG = {
    "border_azure": {"name": "💠 Celestial Azure Border", "type": "border", "price": 500},
    "border_gold": {"name": "🌟 Sovereign Gold Border", "type": "border", "price": 1200},
    "title_shadow": {"name": "👤 Title: Shadow Monarch", "type": "title", "price": 1500},
    "title_hokage": {"name": "🔥 Title: Will of Fire", "type": "title", "price": 2000},
    "theme_crimson": {"name": "🩸 Crimson Eclipse Theme", "type": "theme", "price": 2500},
    "badge_founder": {"name": "🎖️ Arena Vanguard Badge", "type": "badge", "price": 800},
}
