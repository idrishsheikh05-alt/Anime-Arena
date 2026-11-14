import os
import pytz

BOT_TOKEN = "7553716587:AAFX2L1OMSWzVa98VUSm3C2nv_xnT_0Tg-U"

# Hardcoded PostgreSQL URL (with asyncpg driver conversion)
_raw_db = "postgresql://anime_arena_user:keQ6ajb6iI2nb5owcPJ9OOqBAddPmdpy@dpg-dbrkbnon74is73fgn36g-a/anime_arena"

if _raw_db.startswith("postgres://"):
    DATABASE_URL = _raw_db.replace("postgres://", "postgresql+asyncpg://", 1)
elif _raw_db.startswith("postgresql://"):
    DATABASE_URL = _raw_db.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = _raw_db

# Hardcoded Redis URL
REDIS_URL = "redis://red-dbrkh0on74is7394bapg:6379"

PORT = int(os.getenv("PORT", 8080))
BOT_OWNERS = {123456789}
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
