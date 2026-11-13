from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, desc
from config import SHOP_CATALOG, IST, BOT_OWNERS
from database import async_session, User, UserItem, GroupMemberStats, ensure_user, get_rank_title, redis_client

router = Router()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧠 QUIZ", callback_data="nav:quiz"),
                InlineKeyboardButton(text="🕵️ IMPOSTER", callback_data="nav:imposter"),
            ],
            [
                InlineKeyboardButton(text="🌙 MAFIA", callback_data="nav:mafia"),
                InlineKeyboardButton(text="👤 PROFILE", callback_data="nav:profile"),
            ],
            [InlineKeyboardButton(text="🏆 LEADERBOARD", callback_data="nav:leaderboard")],
            [InlineKeyboardButton(text="🎁 DAILY REWARDS", callback_data="nav:daily")],
            [
                InlineKeyboardButton(text="🛒 SHOP", callback_data="nav:shop"),
                InlineKeyboardButton(text="🎒 INVENTORY", callback_data="nav:inventory"),
            ],
            [
                InlineKeyboardButton(text="📜 MISSIONS", callback_data="nav:missions"),
                InlineKeyboardButton(text="📖 HELP", callback_data="nav:help"),
            ],
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(
        "⚔️ **ANIME ARENA** • `Online`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Welcome to **Anime Arena**!\n"
        "Choose your battlefield and prove your skills.\n\n"
        "• 🧠 **Anime Quiz** — Knowledge & speed\n"
        "• 🕵️ **Guess the Imposter** — Bluff & deduction\n"
        "• 🌙 **Anime Mafia** — Roles & strategy\n"
        "• 🏆 **Shared Progression** — XP, coins & ranks",
        reply_markup=main_menu_keyboard(),
    )


from io import BytesIO
from aiogram.types import BufferedInputFile
from PIL import Image, ImageDraw, ImageFont

async def render_profile(message, user_id: int, bot) -> tuple[BufferedInputFile, str]:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return None, "❌ Profile not found."
            
        total_wins = user.quiz_wins + user.imposter_wins + user.mafia_wins + user.town_wins
        xp_in_lvl = user.xp % 500
        filled = int((xp_in_lvl / 500) * 10)
        bar = "🟩" * filled + "⬛" * (10 - filled)
        title = get_rank_title(user.level, user.equipped_border)

        # 1. Custom Image Background & Drawing
        card = Image.new("RGB", (800, 400), color=(25, 25, 35))
        draw = ImageDraw.Draw(card)

        # 2. User ki Telegram PFP fetch karke draw karein
        try:
            photos = await bot.get_user_profile_photos(user_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                file = await bot.get_file(file_id)
                photo_bytes = await bot.download_file(file.file_path)
                
                pfp = Image.open(BytesIO(photo_bytes)).resize((140, 140))
                # Circular mask
                mask = Image.new("L", (140, 140), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 140, 140), fill=255)
                
                card.paste(pfp, (40, 40), mask)
        except Exception:
            pass # Agar PFP na mile toh default rehne dein

        # 3. Text Overlay on Image
        draw.text((210, 45), f"PLAYER PROFILE - {user.full_name if hasattr(user, 'full_name') else 'User'}", fill=(255, 255, 255))
        draw.text((210, 95), f"Rank: {title} (Level {user.level})", fill=(0, 255, 127))
        draw.text((210, 140), f"XP: {user.xp:,}  |  Coins: 🪙 {user.coins:,}", fill=(255, 215, 0))
        draw.text((210, 185), f"Tickets: 🎟️ {user.tickets if hasattr(user, 'tickets') else 3}", fill=(255, 105, 180))

        output = BytesIO()
        card.save(output, format="PNG")
        output.seek(0)
        photo_file = BufferedInputFile(output.read(), filename="profile.png")

        # 4. Text caption niche ke liye
        caption = (
            f"🪪 **PLAYER PROFILE — {user.full_name if hasattr(user, 'full_name') else 'User'}**\n"
            f"────────────────────────\n"
            f"🏅 **Rank:** {title} • Level {user.level}\n"
            f"🖼️ **Border:** `{user.equipped_border}`\n"
            f"✨ **XP:** `{user.xp:,}`  |  🪙 **Coins:** `{user.coins:,}`  |  🎟️ **Tickets:** `{user.tickets if hasattr(user, 'tickets') else 3}`\n"
            f"📊 **Level Progress:** `{xp_in_lvl}/500 XP`\n"
            f"{bar}\n\n"
            f"📈 **BATTLE STATISTICS**\n"
            f"• 🧠 Quiz Wins: `{user.quiz_wins}`  |  🕵️ Imposter Wins: `{user.imposter_wins}`\n"
            f"• 🌙 Mafia Wins: `{user.mafia_wins}`  |  ⛪ Town Wins: `{user.town_wins}`\n"
            f"• 🏆 Total Wins: `{total_wins}`\n"
            f"• 🔥 Best Streak: `{user.best_streak}`"
        )
        return photo_file, caption

@router.message(Command("profile"))
async def cmd_profile(message: Message, bot):
    await ensure_user(message.from_user.id, message.from_user.full_name)
    photo, caption = await render_profile(message, message.from_user.id, bot)
    if isinstance(photo, str):
        await message.answer(photo)
    else:
        await message.answer_photo(photo=photo, caption=caption)
        
async def cmd_balance(message: Message):
    user = await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(
        f"💰 **ARENA WALLET**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 **Arena Coins:** `{user.coins:,}`\n"
        f"✨ **Total XP:** `{user.xp:,}` (Level {user.level})\n"
        f"🎟️ **Tournament Tickets:** `{user.tickets}`"
    )


@router.message(Command("shop"))
async def cmd_shop(message: Message):
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    text = "🛒 **ANIME ARENA COSMETIC SHOP**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n*Purely cosmetic — no pay-to-win advantages.*\n\n"
    kb = []
    for item_id, info in SHOP_CATALOG.items():
        text += f"• **{info['name']}** — `{info['price']} Coins`\n"
        kb.append([InlineKeyboardButton(text=f"Buy {info['name']} ({info['price']}🪙)", callback_data=f"buy:{item_id}")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy_item(callback: CallbackQuery):
    item_id = callback.data.split(":", 1)[1]
    item = SHOP_CATALOG.get(item_id)
    if not item:
        return await callback.answer("Item unavailable.", show_alert=True)

    async with async_session() as session:
        user = await session.get(User, callback.from_user.id)
        if not user or user.coins < item["price"]:
            return await callback.answer("❌ Not enough Arena Coins!", show_alert=True)

        existing = (
            await session.execute(
                select(UserItem).where(UserItem.user_id == user.telegram_id, UserItem.item_id == item_id)
            )
        ).scalar_one_or_none()
        if existing:
            return await callback.answer("✅ You already own this item!", show_alert=True)

        user.coins -= item["price"]
        session.add(UserItem(user_id=user.telegram_id, item_id=item_id, item_type=item["type"]))
        if item["type"] == "border":
            user.equipped_border = item["name"]
        elif item["type"] == "title":
            user.equipped_title = item["name"].replace("👤 Title: ", "")
        await session.commit()

    await callback.answer(f"🎉 Purchased & equipped {item['name']}!", show_alert=True)


@router.message(Command("inventory"))
async def cmd_inventory(message: Message):
    async with async_session() as session:
        rows = (
            await session.execute(select(UserItem).where(UserItem.user_id == message.from_user.id))
        ).scalars().all()
    if not rows:
        return await message.answer("🎒 **Your Inventory is empty.** Visit `/shop` to unlock borders & titles!")
    lines = ["🎒 **OWNED COSMETICS**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for r in rows:
        name = SHOP_CATALOG.get(r.item_id, {}).get("name", r.item_id)
        lines.append(f"• {name} (`{r.item_type}`)")
    await message.answer("\n".join(lines))


@router.message(Command("top", "quizrank", "imposterrank", "mafiarank", "grouprank"))
async def cmd_leaderboards(message: Message):
    cmd = message.text.split()[0].lstrip("/").split("@")[0]
    medals = ["🥇", "🥈", "🥉"]

    async with async_session() as session:
        if cmd == "grouprank":
            if message.chat.type == "private":
                return await message.reply("⚠️ Run `/grouprank` inside a group chat.")
            stmt = (
                select(GroupMemberStats, User.full_name)
                .join(User, GroupMemberStats.user_id == User.telegram_id)
                .where(GroupMemberStats.chat_id == message.chat.id)
                .order_by(desc(GroupMemberStats.group_xp))
                .limit(10)
            )
            rows = (await session.execute(stmt)).all()
            out = [f"👥 **GROUP LEADERBOARD — {message.chat.title}**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
            for i, (st, name) in enumerate(rows):
                tag = medals[i] if i < 3 else f"**{i+1}.**"
                out.append(f"{tag} **{name}** — `{st.group_xp:,} XP` ({st.group_wins} wins)")
            return await message.answer("\n".join(out) if rows else "No group matches recorded yet!")

        col_map = {
            "top": (User.xp, "🌍 GLOBAL XP LEADERBOARD", "XP"),
            "quizrank": (User.quiz_wins, "🧠 GLOBAL QUIZ WINS", "Wins"),
            "imposterrank": (User.imposter_wins, "🕵️ IMPOSTER DECEIVER RANKING", "Wins"),
            "mafiarank": (User.mafia_wins, "🌙 MAFIA MASTERMIND RANKING", "Wins"),
        }
        col, header, unit = col_map.get(cmd, col_map["top"])
        users = (await session.execute(select(User).order_by(desc(col)).limit(10))).scalars().all()
        out = [f"**{header} (TOP 10)**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        for i, u in enumerate(users):
            tag = medals[i] if i < 3 else f"**{i+1}.**"
            val = getattr(u, col.key)
            out.append(f"{tag} **{u.full_name}** — `{val:,} {unit}`")
        await message.answer("\n".join(out))


@router.callback_query(F.data.startswith("nav:"))
async def cb_navigation(callback: CallbackQuery):
    target = callback.data.split(":", 1)[1]
    if target == "profile":
            await ensure_user(callback.from_user.id, callback.from_user.full_name)
        photo, caption = await render_profile(callback.from_user.id, callback.bot)
if isinstance(photo, str):
    await callback.message.answer(photo)
else:
    await callback.message.answer_photo(photo=photo, caption=caption)
    
    elif target == "daily":
        async with async_session() as session:
            user = await session.get(User, callback.from_user.id)
            now = datetime.now(IST)
            if user and user.last_daily and (now - user.last_daily) < timedelta(hours=20):
                return await callback.answer("⏳ Daily reward already claimed! Come back later.", show_alert=True)
            if user:
                user.coins += 250
                user.xp += 150
                user.tickets += 1
                user.last_daily = now
                await session.commit()
        await callback.answer("🎁 Claimed +250 Coins, +150 XP & +1 Ticket!", show_alert=True)
    elif target == "missions":
        today = datetime.now(IST).strftime("%Y-%m-%d")
        d_data = await redis_client.hgetall(f"mission:d:{callback.from_user.id}:{today}")
        await callback.message.answer(
            "📜 **DAILY & WEEKLY MISSIONS**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Win 1 Quiz Match: `{d_data.get('win_quiz', 0)}/1` (+150 Coins)\n"
            f"• Win 1 Imposter Match: `{d_data.get('win_imposter', 0)}/1` (+200 Coins)\n"
            f"• Win 1 Mafia Match: `{d_data.get('win_mafia', 0)}/1` (+300 Coins)\n"
            "• Play all 3 game modes weekly for `1,000 XP`!"
        )
    elif target == "help":
        await callback.message.answer(
            "📖 **ANIME ARENA — COMMAND GUIDE**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "**🧠 Anime Quiz:** `/quiz`, `/quizjoin`, `/quizstart`, `/quizstop`\n"
            "**🕵️ Imposter:** `/imposter [mode]`, `/join`, `/startgame`, `/hint`, `/vote`\n"
            "**🌙 Mafia:** `/mafia`, `/join`, `/startgame`, `/vote`, `/mafiahelp`\n"
            "**📊 Stats & Shop:** `/profile`, `/shop`, `/inventory`, `/balance`, `/top`"
        )
    else:
        cmds = {
            "quiz": "🧠 Start a group trivia lobby with `/quiz`!",
            "imposter": "🕵️ Start social deduction with `/imposter` (Modes: `classic`, `double`, `blind`, `reverse`)!",
            "mafia": "🌙 Launch an Anime Mafia match (6–20 players) in your group with `/mafia`!",
            "leaderboard": "🏆 Rankings: `/top`, `/quizrank`, `/imposterrank`, `/mafiarank`, `/grouprank`",
            "shop": "🛒 Open the cosmetic store with `/shop`!",
            "inventory": "🎒 Check owned items with `/inventory`!",
        }
        await callback.message.answer(cmds.get(target, "Use /start to return to menu."))
    await callback.answer()


@router.message(Command("maintenance"))
async def cmd_maintenance(message: Message):
    if message.from_user.id not in BOT_OWNERS:
        return
    if await redis_client.get("maintenance_mode") == "1":
        await redis_client.delete("maintenance_mode")
        await message.reply("🟢 Maintenance mode **OFF**.")
    else:
        await redis_client.set("maintenance_mode", "1")
        await message.reply("🛠️ Maintenance mode **ON**.")
