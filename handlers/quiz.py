import asyncio
import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatType
from database import ensure_user, record_progression, async_session

router = Router()

# Active group quiz lobbies: chat_id -> state dict
QUIZ_GAMES: dict[int, dict] = {}

# Expanded Question Bank with lots of questions
QUESTION_BANK = [
    {"cat": "Anime Knowledge", "diff": "Easy", "xp": 50, "q": "Which hidden village does Naruto Uzumaki belong to?", "opts": ["Konohagakure", "Sunagakure", "Kirigakure", "Kumogakure"], "ans": 0},
    {"cat": "Who Said It?", "diff": "Medium", "xp": 100, "q": "Who said: 'Throughout Heaven and Earth, I alone am the honored one'?", "opts": ["Sukuna", "Satoru Gojo", "Madara Uchiha", "Aizen"], "ans": 1},
    {"cat": "Emoji Quiz", "diff": "Easy", "xp": 50, "q": "Decode the anime: 📓🍎✍️💀", "opts": ["Soul Eater", "Bleach", "Death Note", "Tokyo Ghoul"], "ans": 2},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "Which Bankai allows Ichigo Kurosaki to compress all his spiritual pressure into a sleek black blade?", "opts": ["Senbonzakura Kageyoshi", "Tensa Zangetsu", "Zanka no Tachi", "Kannonbiraki"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "A blindfolded jujutsu sorcerer wielding Limitless and Six Eyes.", "opts": ["Kakashi Hatake", "Satoru Gojo", "Yami Sukehiro", "Levi Ackerman"], "ans": 1},
    {"cat": "Guess the Opening", "diff": "Medium", "xp": 100, "q": "'Gurenge' by LiSA is the iconic first opening of which anime?", "opts": ["Demon Slayer", "Attack on Titan", "Jujutsu Kaisen", "Black Clover"], "ans": 0},
    {"cat": "Anime Knowledge", "diff": "Hard", "xp": 150, "q": "What is the name of Edward Elric's automail mechanic in Fullmetal Alchemist?", "opts": ["Riza Hawkeye", "Winry Rockbell", "Olivier Armstrong", "Izumi Curtis"], "ans": 1},
    {"cat": "Emoji Quiz", "diff": "Medium", "xp": 100, "q": "Decode the anime: 🏴‍☠️👒🍖🌊", "opts": ["Fairy Tail", "Vinland Saga", "One Piece", "Magi"], "ans": 2},
    {"cat": "Who Said It?", "diff": "Hard", "xp": 150, "q": "Who said: 'Nothing happened' after absorbing Luffy's pain on Thriller Bark?", "opts": ["Sanji", "Roronoa Zoro", "Brook", "Franky"], "ans": 1},
    {"cat": "Power Scaling", "diff": "Medium", "xp": 100, "q": "Which Titan power allows Eren Yeager to see memories of future inheritors?", "opts": ["Founding Titan", "War Hammer Titan", "Attack Titan", "Colossal Titan"], "ans": 2},
    {"cat": "Classic Anime", "diff": "Easy", "xp": 50, "q": "What is the name of Goku's signature energy attack?", "opts": ["Spirit Bomb", "Kamehameha", "Final Flash", "Galick Gun"], "ans": 1},
    {"cat": "Shonen Legends", "diff": "Medium", "xp": 100, "q": "In Hunter x Hunter, what is Gon Freecss's Nen type?", "opts": ["Transmuter", "Enhancer", "Emitter", "Conjurer"], "ans": 1},
    {"cat": "Dark Fantasy", "diff": "Hard", "xp": 150, "q": "What is the true name of the demon bound to Asta's grimoire in Black Clover?", "opts": ["Lucifero", "Zagred", "Liebe", "Megicula"], "ans": 2},
    {"cat": "Sci-Fi / Mecha", "diff": "Medium", "xp": 100, "q": "What is the name of the colossal humanoids that attack humanity in Attack on Titan?", "opts": ["Nomus", "Titans", "Ghouls", "Hollows"], "ans": 1},
]

# Helper: Check if chat is a group or supergroup
def is_group_chat(message: Message) -> bool:
    return message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]


@router.message(Command("quiz"))
async def cmd_quiz_create(message: Message):
    if not is_group_chat(message):
        return await message.answer("❌ **Anime Quiz can only be played inside group chats!** Add me to your group to host a match.", parse_mode="Markdown")

    chat_id = message.chat.id
    if chat_id in QUIZ_GAMES:
        return await message.reply("⚠️ A quiz lobby or match is already active here! Use `/quizjoin` or `/quizstop`.")

    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    
    QUIZ_GAMES[chat_id] = {
        "host": message.from_user.id,
        "status": "WAITING",
        "players": {message.from_user.id: message.from_user.full_name},
        "scores": {message.from_user.id: 0},
        "streaks": {message.from_user.id: 0},
        "q_index": 0,
        "answered_current": set(),
        "first_answered": False,
        "questions": random.sample(QUESTION_BANK, k=min(10, len(QUESTION_BANK))),
    }
    
    host_mention = f"[{message.from_user.full_name}](tg://user?id={message.from_user.id})"
    players_list = f"1. {host_mention}"

    await message.answer(
        "🧠 **ANIME QUIZ — MATCH LOBBY**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 **Host:** {host_mention}\n"
        "⚙️ **Settings:** `10 Questions` • `20s/Question` • `Streak & Speed Bonuses`\n\n"
        f"👥 **Joined Players (1/30):**\n"
        f"{players_list}\n\n"
        "👉 Type `/quizjoin` to enter, `/quizstart` to begin!",
        parse_mode="Markdown"
    )


@router.message(Command("quizjoin"))
async def cmd_quiz_join(message: Message):
    if not is_group_chat(message):
        return await message.reply("❌ Quiz lobbies can only be joined inside group chats.")

    game = QUIZ_GAMES.get(message.chat.id)
    if not game or game["status"] != "WAITING":
        return await message.reply("❌ No open quiz lobby to join. Start one with `/quiz`.")
    
    uid = message.from_user.id
    if uid in game["players"]:
        return await message.reply("✅ You are already in the lobby!")
    if len(game["players"]) >= 30:
        return await message.reply("🚫 Lobby is full (30/30 players).")

    await ensure_user(uid, message.from_user.username, message.from_user.full_name)
    game["players"][uid] = message.from_user.full_name
    game["scores"][uid] = 0
    game["streaks"][uid] = 0

    # Build updated mentioned players list
    players_text = "\n".join(
        f"{idx}. [{name}](tg://user?id={pid})" 
        for idx, (pid, name) in enumerate(game["players"].items(), 1)
    )

    await message.answer(
        f"⚡ **{message.from_user.full_name}** joined the quiz! (`{len(game['players'])}/30`)\n\n"
        f"👥 **Current Lobby:**\n{players_text}",
        parse_mode="Markdown"
    )


@router.message(Command("quizleave"))
async def cmd_quiz_leave(message: Message):
    game = QUIZ_GAMES.get(message.chat.id)
    uid = message.from_user.id
    if game and game["status"] == "WAITING" and uid in game["players"]:
        del game["players"][uid]
        game["scores"].pop(uid, None)
        await message.answer(f"🚪 **{message.from_user.full_name}** left the quiz lobby.")


@router.message(Command("quizstop"))
async def cmd_quiz_stop(message: Message):
    game = QUIZ_GAMES.get(message.chat.id)
    if game and message.from_user.id == game["host"]:
        QUIZ_GAMES.pop(message.chat.id, None)
        await message.answer("🛑 Quiz match terminated by host.")


@router.message(Command("quizstart"))
async def cmd_quiz_start(message: Message):
    chat_id = message.chat.id
    game = QUIZ_GAMES.get(chat_id)
    if not game or game["status"] != "WAITING":
        return await message.reply("❌ No waiting quiz lobby found.")
    if message.from_user.id != game["host"]:
        return await message.reply("⚠️ Only the lobby host can start the quiz.")

    game["status"] = "RUNNING"
    asyncio.create_task(run_quiz_loop(message, chat_id))


async def run_quiz_loop(message: Message, chat_id: int):
    game = QUIZ_GAMES.get(chat_id)
    if not game:
        return

    for idx, q_data in enumerate(game["questions"]):
        if chat_id not in QUIZ_GAMES:
            return
        game["q_index"] = idx
        game["answered_current"] = set()
        game["first_answered"] = False

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{chr(65+i)}) {opt}", callback_data=f"qz:{idx}:{i}")]
                for i, opt in enumerate(q_data["opts"])
            ]
        )
        q_msg = await message.answer(
            f"❓ **QUESTION {idx+1}/{len(game['questions'])}**  |  🏷️ `{q_data['cat']}` ({q_data['diff']})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**{q_data['q']}**\n\n"
            f"⏱️ *20 seconds remaining...*",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        await asyncio.sleep(20)
        if chat_id not in QUIZ_GAMES:
            return
        correct_opt = q_data["opts"][q_data["ans"]]
        try:
            await q_msg.edit_text(
                f"⏰ **TIME'S UP! — Question {idx+1}**\n"
                f"✅ Correct Answer: **{correct_opt}**",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        await asyncio.sleep(2)

    # Match Podium & Rewards
    sorted_scores = sorted(game["scores"].items(), key=lambda x: x[1], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 **ANIME QUIZ — FINAL PODIUM**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for rank, (uid, pts) in enumerate(sorted_scores):
        tag = medals[rank] if rank < 3 else f"**{rank+1}.**"
        name = game["players"].get(uid, "Player")
        mention_name = f"[{name}](tg://user?id={uid})"
        lines.append(f"{tag} {mention_name} — `{pts} XP`")
        won = "quiz" if rank == 0 and pts > 0 else None
        coins = 100 if rank == 0 else 30
        await record_progression(uid, chat_id, xp=pts, coins=coins, won_mode=won, played=True)

    QUIZ_GAMES.pop(chat_id, None)
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.callback_query(F.data.startswith("qz:"))
async def cb_quiz_answer(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    game = QUIZ_GAMES.get(chat_id)
    if not game or game["status"] != "RUNNING":
        return await callback.answer("This question has expired.", show_alert=True)

    _, q_idx_str, opt_str = callback.data.split(":")
    q_idx, opt = int(q_idx_str), int(opt_str)
    uid = callback.from_user.id

    if uid not in game["players"]:
        return await callback.answer("You are not registered in this match!", show_alert=True)
    if q_idx != game["q_index"]:
        return await callback.answer("Question already closed!", show_alert=True)
    if uid in game["answered_current"]:
        return await callback.answer("You already locked in an answer!", show_alert=True)

    game["answered_current"].add(uid)
    q_data = game["questions"][q_idx]

    if opt == q_data["ans"]:
        bonus = 0
        if not game["first_answered"]:
            game["first_answered"] = True
            bonus += 25  # First correct answer bonus
        game["streaks"][uid] = game["streaks"].get(uid, 0) + 1
        if game["streaks"][uid] == 5:
            bonus += 100  # Five-answer streak bonus
        earned = q_data["xp"] + bonus
        game["scores"][uid] += earned
        await callback.answer(f"✅ Correct! +{earned} XP", show_alert=False)
    else:
        game["streaks"][uid] = 0
        await callback.answer("❌ Wrong answer! Streak reset.", show_alert=False)


@router.message(Command("addquiz"))
async def cmd_add_quiz(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "⚠️ **Usage:**\n`/addquiz Question | Option1, Option2, Option3, Option4 | CorrectIndex (0-3)`",
            parse_mode="Markdown"
        )
        return
    
    parts = args[1].split("|")
    if len(parts) < 3:
        await message.answer("❌ **Invalid format!** Use `|` to separate question, options, and correct option index.", parse_mode="Markdown")
        return
        
    q_text = parts[0].strip()
    options = [opt.strip() for opt in parts[1].split(",")]
    try:
        correct_idx = int(parts[2].strip())
    except ValueError:
        await message.answer("❌ Correct index must be a number between 0 and 3.")
        return
        
    if len(options) < 2:
        await message.answer("❌ Please provide at least 2 options separated by commas.")
        return

    if not (0 <= correct_idx < len(options)):
        await message.answer(f"❌ Correct index must be between 0 and {len(options)-1}.")
        return

    # Add question dynamically to runtime question bank as well as database if applicable
    new_q = {
        "cat": "Community Added",
        "diff": "Medium",
        "xp": 100,
        "q": q_text,
        "opts": options,
        "ans": correct_idx
    }
    QUESTION_BANK.append(new_q)

    await message.answer(
        f"✅ **Successfully added new quiz question!**\n\n"
        f"📌 **Q:** {q_text}\n"
        f"🔢 **Options:** {', '.join(options)}\n"
        f"🎯 **Correct Option Index:** `{correct_idx}`",
        parse_mode="Markdown"
    )
    
