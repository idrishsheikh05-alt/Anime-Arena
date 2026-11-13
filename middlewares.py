from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from config import BOT_OWNERS
from database import redis_client


class AccessControlMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = getattr(event, "from_user", None)
        if not user or user.id in BOT_OWNERS:
            return await handler(event, data)

        if await redis_client.get("maintenance_mode") == "1":
            if isinstance(event, Message):
                await event.reply("🛠️ **Anime Arena is undergoing scheduled maintenance.** Back shortly!")
            elif isinstance(event, CallbackQuery):
                await event.answer("🛠️ Maintenance mode is active.", show_alert=True)
            return

        if await redis_client.sismember("banned_users", str(user.id)):
            if isinstance(event, CallbackQuery):
                await event.answer("🚫 You are restricted from Anime Arena.", show_alert=True)
            return

        return await handler(event, data)
      
