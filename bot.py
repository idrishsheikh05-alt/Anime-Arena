import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, PORT
from database import init_db
from middlewares import AccessControlMiddleware
from handlers import general, quiz, imposter, mafia

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# 1. Bot aur Dispatcher ko pehle initialize karein
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
)
dp = Dispatcher(storage=MemoryStorage())

# Middleware aur Routers register karein
dp.message.middleware(AccessControlMiddleware())
dp.callback_query.middleware(AccessControlMiddleware())

dp.include_router(general.router)
dp.include_router(quiz.router)
dp.include_router(imposter.router)
dp.include_router(mafia.router)


# 2. Render Health Check Server
async def health_check(_request):
    return web.Response(text="Anime Arena Bot is Online!", status=200)


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render ke dynamic PORT ya config se port uthayega
    port = int(os.getenv("PORT", PORT))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Render Web Service health endpoint listening on port {port}")


# 3. Main function
async def main():
    await init_db()
    await start_web_server()
    
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("⚔️ Anime Arena Multi-Game Engine is LIVE!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    
  
