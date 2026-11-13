import asyncio
import logging
import sys
import os
from aiohttp import web
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


async def health_check(_request):
    return web.Response(text="Anime Arena Bot is Online!", status=200)


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Render Web Service health endpoint listening on port {PORT}")


# 1. Simple web server handler for Render health check
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

async bld_web_app():
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
async def main():
    await init_db()
    await start_web_server()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(AccessControlMiddleware())
    dp.callback_query.middleware(AccessControlMiddleware())

    dp.include_router(general.router)
    dp.include_router(quiz.router)
    dp.include_router(imposter.router)
    dp.include_router(mafia.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("⚔️ Anime Arena Multi-Game Engine is LIVE!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
  
