import asyncio
import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import ensure_user, record_progression

router = Router()

IMPOSTER_LOBBIES: dict[int, dict] = {}

WORD_PAIRS = [
    ("Naruto Uzumaki", "Boruto Uzumaki"),
    ("Sharingan", "Rinnegan"),
    ("Attack on Titan", "Kabaneri of the Iron Fortress"),
    ("Satoru Gojo", "Kakashi Hatake"),
    ("Death Note", "Code Geass"),
    ("Katana", "Zanpakuto"),
    ("Akatsuki", "Phantom Troupe"),
    ("Dragon Ball", "One Piece"),
]


@router.message(Command("imposter"))
async def cmd_imposter_create(message: Message):
    chat_id = message.chat.id
    if chat_id in IMPOSTER_LOBBIES:
        return await message.reply("⚠️ An Imposter lobby is already active in this group!")

    args = message.text.split()
    mode = args[1].lower() if len(args) > 1 and args[1].lower() in {"classic", "double", "blind", "reverse"} else "classic"
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    IMPOSTER_LOBBIES[chat_id] = {
        "host": message.from_user.id,
        "mode": mode,
        "phase": "WAITING",
        "players": {message.from_user.id: message.from_user.full_name},
        "imposters": set(),
        "hints": {},
        "votes": {},
    }
    await message.answer(
        f"🕵️ **GUESS THE IMPOSTER — LOBBY ({mode.upper()} MODE)**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 **Host:** {message.from_user.full_name}\n"
        "👥 **Players (1/10)** (Min 3 required)\n\n"
        "⚠️ *Important: Every player must start the bot privately first so secret words can be delivered via DM!*\n\n"
        "👉 Type `/join` to enter • `/startgame` to begin!"
    )


@router.message(Command("join"))
async def cmd_generic_join(message: Message):
    chat_id = message.chat.id
    # Route to Imposter if active here; Mafia handles its own if Mafia lobby is active
    from handlers.mafia import MAFIA_LOBBIES
    if chat_id in MAFIA_LOBBIES:
        from handlers.mafia import join_mafia_lobby
        return await join_mafia_lobby(message)

    lobby = IMPOSTER_LOBBIES.get(chat_id)
    if not lobby or lobby["phase"] != "WAITING":
        return await message.reply("❌ No waiting lobby found. Start `/imposter` or `/mafia`.")
    uid = message.from_user.id
    if uid in lobby["players"]:
        return await message.reply("✅ You already joined!")
    if len(lobby["players"]) >= 10:
        return await message.reply("🚫 Lobby full (10/10).")

    await ensure_user(uid, message.from_user.username, message.from_user.full_name)
    lobby["players"][uid] = message.from_user.full_name
    await message.answer(f"🕵️ **{message.from_user.full_name}** joined the Imposter lobby! (`{len(lobby['players'])}/10`)")


@router.message(Command("leave"))
async def cmd_generic_leave(message: Message):
    chat_id = message.chat.id
    from handlers.mafia import MAFIA_LOBBIES
    if chat_id in MAFIA_LOBBIES:
        from handlers.mafia import leave_mafia_lobby
        return await leave_mafia_lobby(message)

    lobby = IMPOSTER_LOBBIES.get(chat_id)
    uid = message.from_user.id
    if lobby and lobby["phase"] == "WAITING" and uid in lobby["players"]:
        del lobby["players"][uid]
        if not lobby["players"]:
            IMPOSTER_LOBBIES.pop(chat_id, None)
            return await message.answer("🗑️ Lobby closed because all players left.")
        if uid == lobby["host"]:
            lobby["host"] = next(iter(lobby["players"]))
            await message.answer(f"👑 Host left! New host: **{lobby['players'][lobby['host']]}**")
        else:
            await message.answer(f"🚪 **{message.from_user.full_name}** left the lobby.")


@router.message(Command("startgame"))
async def cmd_generic_startgame(message: Message):
    chat_id = message.chat.id
    from handlers.mafia import MAFIA_LOBBIES
    if chat_id in MAFIA_LOBBIES:
        from handlers.mafia import start_mafia_game
        return await start_mafia_game(message)

    lobby = IMPOSTER_LOBBIES.get(chat_id)
    if not lobby or lobby["phase"] != "WAITING":
        return await message.reply("❌ No active lobby ready to start.")
    if message.from_user.id != lobby["host"]:
        return await message.reply("⚠️ Only the host can start the game.")
    if len(lobby["players"]) < 3:
        return await message.reply("⚠️ Minimum **3 players** required for Guess the Imposter.")

    lobby["phase"] = "DISTRIBUTING"
    player_ids = list(lobby["players"].keys())
    imp_count = 2 if (lobby["mode"] == "double" and len(player_ids) >= 5) else 1
    imposters = set(random.sample(player_ids, k=imp_count))
    lobby["imposters"] = imposters

    crew_word, imp_word = random.choice(WORD_PAIRS)
    if lobby["mode"] == "reverse":
        crew_word, imp_word = imp_word, crew_word

    # Private DM word delivery with failure protection
    for pid in player_ids:
        try:
            if pid in imposters:
                secret_text = (
                    "🤫 **YOU ARE THE IMPOSTER!**\n"
                    "Blend in with the hints and survive the vote!\n"
                    + ("🙈 **Blind Mode:** You receive NO word!" if lobby["mode"] == "blind" else f"🔑 **Your Decoy Word:** `{imp_word}`")
                )
            else:
                secret_text = f"🛡️ **CREWMATE ROLE**\n🔑 **Secret Anime Word:** `{crew_word}`\nGive a subtle hint without exposing the exact word!"
            await message.bot.send_message(pid, secret_text)
        except Exception:
            IMPOSTER_LOBBIES.pop(chat_id, None)
            return await message.answer(
                f"❌ **DM Delivery Failed!** **{lobby['players'][pid]}** has not started the bot in private chat. Match aborted."
            )

    lobby["phase"] = "HINTING"
    lobby["crew_word"] = crew_word
    lobby["imp_word"] = imp_word
    asyncio.create_task(run_imposter_phases(message, chat_id))


async def run_imposter_phases(message: Message, chat_id: int):
    lobby = IMPOSTER_LOBBIES.get(chat_id)
    if not lobby:
        return

    await message.answer(
        "📩 **SECRET WORDS DELIVERED VIA DM!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✍️ **PHASE: HINTING (45s)**\n"
        "Every player submit ONE clue using `/hint your clue here`"
    )
    await asyncio.sleep(45)
    if chat_id not in IMPOSTER_LOBBIES:
        return

    lobby["phase"] = "DISCUSSION"
    hint_summary = "\n".join(
        [f"• **{lobby['players'][uid]}:** _{lobby['hints'].get(uid, 'No hint submitted')}_" for uid in lobby["players"]]
    )
    await message.answer(
        f"💬 **PHASE: DISCUSSION (45s)**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**Collected Clues:**\n{hint_summary}\n\n"
        f"Discuss who sounds suspicious!"
    )
    await asyncio.sleep(45)
    if chat_id not in IMPOSTER_LOBBIES:
        return

    lobby["phase"] = "VOTING"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🗳️ Vote {name}", callback_data=f"impvote:{uid}")]
            for uid, name in lobby["players"].items()
        ]
    )
    await message.answer("🗳️ **PHASE: ANONYMOUS VOTING (30s)**\nTap below to vote out the suspected Imposter!", reply_markup=kb)
    await asyncio.sleep(30)
    if chat_id not in IMPOSTER_LOBBIES:
        return

    # Tally & Reveal
    tally: dict[int, int] = {}
    for target in lobby["votes"].values():
        tally[target] = tally.get(target, 0) + 1

    eliminated = max(tally, key=tally.get) if tally else None
    imp_names = ", ".join(lobby["players"][i] for i in lobby["imposters"])
    crew_won = eliminated in lobby["imposters"]

    for uid in lobby["players"]:
        is_imp = uid in lobby["imposters"]
        won = (not is_imp and crew_won) or (is_imp and not crew_won)
        await record_progression(uid, chat_id, xp=200 if won else 50, coins=80 if won else 20, won_mode="imposter" if won else None)

    IMPOSTER_LOBBIES.pop(chat_id, None)
    await message.answer(
        f"🎭 **IMPOSTER REVEAL & RESULTS**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗳️ **Voted Out:** `{lobby['players'].get(eliminated, 'Nobody')}`\n"
        f"🤫 **True Imposter(s):** `{imp_names}`\n"
        f"🔑 **Crew Word:** `{lobby['crew_word']}` | **Imposter Word:** `{lobby['imp_word']}`\n\n"
        f"🏆 **{'CREWMATES WIN!' if crew_won else 'IMPOSTER SURVIVED & WINS!'}**"
    )


@router.message(Command("hint"))
async def cmd_submit_hint(message: Message):
    lobby = IMPOSTER_LOBBIES.get(message.chat.id)
    if not lobby or lobby["phase"] != "HINTING":
        return
    uid = message.from_user.id
    if uid not in lobby["players"]:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Usage: `/hint <your clue>`")
    lobby["hints"][uid] = parts[1][:100]
    await message.reply(f"✅ Hint locked in for **{message.from_user.full_name}**!")


@router.callback_query(F.data.startswith("impvote:"))
async def cb_imposter_vote(callback: CallbackQuery):
    lobby = IMPOSTER_LOBBIES.get(callback.message.chat.id)
    if not lobby or lobby["phase"] != "VOTING":
        return await callback.answer("Voting is closed.", show_alert=True)
    voter = callback.from_user.id
    if voter not in lobby["players"]:
        return await callback.answer("You are not in this match.", show_alert=True)
    target = int(callback.data.split(":")[1])
    lobby["votes"][voter] = target
    await callback.answer(f"🗳️ Anonymous vote cast for {lobby['players'][target]}!")
      
