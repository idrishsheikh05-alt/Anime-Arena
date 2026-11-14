from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
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


async def render_profile(user_id: int, bot: Bot) -> tuple[BufferedInputFile | None, str]:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return None, "❌ Profile not found. Send /start first."

        total_wins = user.quiz_wins + user.imposter_wins + user.mafia_wins + user.town_wins
        xp_in_lvl = user.xp % 500
        filled = int((xp_in_lvl / 500) * 10)
        bar = "🟩" * filled + "⬛" * (10 - filled)
        title = get_rank_title(user.level, user.equipped_border)

        # 1. Custom Dark Card Background (Matching your UI theme)
        card = Image.new("RGB", (800, 420), color=(18, 18, 26))
        draw = ImageDraw.Draw(card)

        # Draw outer glowing border frame
        draw.rectangle([10, 10, 790, 410], outline=(138, 43, 226), width=2)

        # Avatar circle placeholder
        draw.ellipse((40, 40, 180, 180), fill=(30, 30, 45), outline=(255, 105, 180), width=3)

        # 2. Fetch Telegram PFP if available
        try:
            photos = await bot.get_user_profile_photos(user_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                file = await bot.get_file(file_id)
                photo_stream = await bot.download_file(file.file_path)

                pfp = Image.open(photo_stream).convert("RGBA").resize((140, 140))
                mask = Image.new("L", (140, 140), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 140, 140), fill=255)

                card.paste(pfp, (40, 40), mask)
        except Exception:
            pass

        display_name = getattr(user, "full_name", None) or "Player"
        tickets_count = getattr(user, "tickets", 0)

        # 3. Drawing text overlay onto the generated card image
        draw.text((210, 45), display_name, fill=(255, 255, 255))
        draw.text((210, 80), "YOUR WALLET / YOUR POWER", fill=(160, 160, 180))
        draw.line((210, 110, 750, 110), fill=(138, 43, 226), width=2)

        # Stat Boxes info representation inside image
        draw.text((210, 130), f"CRIMSON / RANK: {title.upper()}", fill=(255, 105, 180))
        draw.text((210, 160), f"Level {user.level}  |  XP: {user.xp:,}", fill=(255, 255, 255))

        draw.text((210, 225), f"COINS", fill=(255, 215, 0))
        draw.text((210, 255), f"{user.coins:,}", fill=(255, 255, 255))

        draw.text((40, 350), "LEVEL UP. KEEP BUILDING.", fill=(160, 160, 180))
        draw.text((40, 375), "XENO • WALLET", fill=(138, 43, 226))

        output = BytesIO()
        card.save(output, format="PNG")
        output.seek(0)
        photo_file = BufferedInputFile(output.read(), filename="profile.png")

        # 4. Text caption matching your exact clean style
        caption = (
            f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            f"┃  👤 **{display_name}**\n"
            f"┃  _YOUR WALLET / YOUR POWER_\n"
            f"┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
            f"┃\n"
            f"┃  🪙 **COINS**\n"
            f"┃     `{user.coins:,}`\n"
            f"┃\n"
            f"┃  ✨ **XP & LEVEL**\n"
            f"┃     Level {user.level}  •  {user.xp:,} XP\n"
            f"┃\n"
            f"┃  🎟️ **TICKETS & WINS**\n"
            f"┃     Tickets: {tickets_count}  •  Wins: {total_wins}\n"
            f"┃\n"
            f"┃  📊 **PROGRESS ({xp_in_lvl}/500 XP)**\n"
            f"┃     {bar}\n"
            f"┃\n"
            f"┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n"
            f"   `LEVEL UP. KEEP BUILDING.`"
        )
        return photo_file, caption


@router.message(Command("profile"))
async def cmd_profile(message: Message, bot: Bot):
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    photo, caption = await render_profile(message.from_user.id, bot)
    if not photo:
        await message.answer(caption)
    else:
        await message.answer_photo(photo=photo, caption=caption)


@router.message(Command("balance"))
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
        await ensure_user(callback.from_user.id, callback.from_user.username, callback.from_user.full_name)
        photo, caption = await render_profile(callback.from_user.id, callback.bot)
        if not photo:
            await callback.message.answer(caption)
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
        
