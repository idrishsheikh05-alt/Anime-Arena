import asyncio
import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import ensure_user, record_progression

router = Router()

MAFIA_LOBBIES: dict[int, dict] = {}

ROLE_META = {
    "DON": ("🎩 DON", "Mafia", "Leader of the Mafia. Coordinates the night hit."),
    "MAFIA": ("🗡️ MAFIA", "Mafia", "Assists the Don. Inherits Don title upon Don's death."),
    "FRAMER": ("🎭 FRAMER", "Mafia", "Frames a target so Detective sees them as Mafia."),
    "CONSIGLIERE": ("📜 CONSIGLIERE", "Mafia", "Learns a player's exact role at night."),
    "DETECTIVE": ("🔍 DETECTIVE", "Town", "Investigates one player each night."),
    "DOCTOR": ("💉 DOCTOR", "Town", "Protects one player from a night attack."),
    "BODYGUARD": ("🛡️ BODYGUARD", "Town", "Guards a player against night attacks."),
    "VIGILANTE": ("🔫 VIGILANTE", "Town", "Can eliminate one suspect during the night."),
    "MAYOR": ("🎖️ MAYOR", "Town", "Your daytime elimination vote counts twice."),
    "CITIZEN": ("🏘️ CITIZEN", "Town", "Deduce the Mafia and vote them out by day."),
    "JESTER": ("🃏 JESTER", "Independent", "Win immediately if the Town votes to execute you!"),
    "SERIAL_KILLER": ("🔪 SERIAL KILLER", "Independent", "Eliminate everyone at night to be the last standing."),
}


def build_role_pool(count: int) -> list[str]:
    base = ["DON", "DETECTIVE", "DOCTOR", "CITIZEN", "CITIZEN"]
    if count >= 6:
        base.append("MAFIA")
    if count >= 7:
        base.append("JESTER")
    if count >= 8:
        base.append("BODYGUARD")
    if count >= 9:
        base.append("CONSIGLIERE")
    if count >= 10:
        base.append("SERIAL_KILLER")
    while len(base) < count:
        base.append(random.choice(["CITIZEN", "VIGILANTE", "MAYOR", "MAFIA", "FRAMER"]))
    return base[:count]


@router.message(Command("mafia"))
async def cmd_mafia_create(message: Message):
    chat_id = message.chat.id
    if chat_id in MAFIA_LOBBIES:
        return await message.reply("⚠️ An Anime Mafia match is already active in this group!")

    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    MAFIA_LOBBIES[chat_id] = {
        "host": message.from_user.id,
        "phase": "LOBBY",
        "players": {message.from_user.id: message.from_user.full_name},
        "alive": set(),
        "roles": {},
        "mafia_seniority": [],  # Ordered list: [Don_id, MafiaA_id, MafiaB_id]
        "night_actions": {},
        "votes": {},
        "night_num": 0,
    }
    await message.answer(
        "🌙 **ANIME MAFIA — STRATEGIC DEDUCTION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 **Host:** {message.from_user.full_name}\n"
        "👥 **Players:** `1/20` (Recommended: 6–20 players; Min 4 for testing)\n\n"
        "⚠️ *Start the bot in DM first to receive secret roles & night action buttons!*\n"
        "👉 `/join` to enter • `/startgame` to begin • `/mafiahelp` for rules"
    )


@router.message(Command("mafiahelp"))
async def cmd_mafia_help(message: Message):
    await message.answer(
        "🌙 **ANIME MAFIA — FIELD MANUAL**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• **Teams:** 🏘️ Town vs 🗡️ Mafia vs 🃏 Independent\n"
        "• **Night Phase:** Special roles act privately via bot DM.\n"
        "• **Don Succession:** If the Don dies, the senior surviving Mafia automatically inherits the Don title.\n"
        "• **Day Phase:** Discuss morning casualties and vote out suspects."
    )


async def join_mafia_lobby(message: Message):
    game = MAFIA_LOBBIES[message.chat.id]
    if game["phase"] != "LOBBY":
        return await message.reply("🚫 Match already in progress!")
    uid = message.from_user.id
    if uid in game["players"]:
        return await message.reply("✅ Already in the Mafia lobby.")
    if len(game["players"]) >= 20:
        return await message.reply("🚫 Lobby full (20/20).")
    await ensure_user(uid, message.from_user.username, message.from_user.full_name)
    game["players"][uid] = message.from_user.full_name
    await message.answer(f"🌙 **{message.from_user.full_name}** entered the Mafia lobby! (`{len(game['players'])}/20`)")


async def leave_mafia_lobby(message: Message):
    game = MAFIA_LOBBIES[message.chat.id]
    uid = message.from_user.id
    if game["phase"] == "LOBBY" and uid in game["players"]:
        del game["players"][uid]
        if not game["players"]:
            MAFIA_LOBBIES.pop(message.chat.id, None)
            return await message.answer("🗑️ Mafia lobby closed.")
        await message.answer(f"🚪 **{message.from_user.full_name}** left the Mafia lobby.")


async def start_mafia_game(message: Message):
    chat_id = message.chat.id
    game = MAFIA_LOBBIES[chat_id]
    if game["phase"] != "LOBBY":
        return
    if message.from_user.id != game["host"]:
        return await message.reply("⚠️ Only the host can start the game.")
    if len(game["players"]) < 4:
        return await message.reply("⚠️ Minimum **4 players** required to launch Anime Mafia.")

    pids = list(game["players"].keys())
    random.shuffle(pids)
    pool = build_role_pool(len(pids))
    random.shuffle(pool)

    # Assign roles and record Mafia seniority order (Don first, then Mafia)
    mafia_members = []
    for pid, role in zip(pids, pool):
        game["roles"][pid] = role
        game["alive"].add(pid)
        if role == "DON":
            mafia_members.insert(0, pid)
        elif role in {"MAFIA", "FRAMER", "CONSIGLIERE"}:
            mafia_members.append(pid)
    game["mafia_seniority"] = mafia_members

    # Deliver roles privately
    for pid in pids:
        role = game["roles"][pid]
        r_name, team, desc = ROLE_META[role]
        teammates = ""
        if team == "Mafia":
            mates = [f"{game['players'][m]} ({game['roles'][m]})" for m in mafia_members if m != pid]
            teammates = f"\n🤝 **Mafia Allies:** {', '.join(mates) if mates else 'None'}"
        try:
            await message.bot.send_message(
                pid,
                f"🎭 **YOUR SECRET MAFIA ROLE**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Role: **{r_name}** (`{team} Team`)\n"
                f"Ability: _{desc}_{teammates}",
            )
        except Exception:
            MAFIA_LOBBIES.pop(chat_id, None)
            return await message.answer(
                f"❌ **DM Failed!** **{game['players'][pid]}** must start the bot privately first. Match cancelled."
            )

    asyncio.create_task(run_mafia_cycle(message, chat_id))


def promote_next_don(game: dict) -> int | None:
    don_alive = any(p in game["alive"] and game["roles"][p] == "DON" for p in game["mafia_seniority"])
    if don_alive:
        return None
    for candidate in game["mafia_seniority"]:
        if candidate in game["alive"]:
            game["roles"][candidate] = "DON"
            return candidate
    return None


def check_mafia_winner(game: dict) -> str | None:
    alive = game["alive"]
    mafia_alive = [p for p in alive if ROLE_META[game["roles"][p]][1] == "Mafia"]
    sk_alive = [p for p in alive if game["roles"][p] == "SERIAL_KILLER"]
    town_alive = [p for p in alive if ROLE_META[game["roles"][p]][1] == "Town"]

    if not mafia_alive and not sk_alive:
        return "TOWN"
    if len(mafia_alive) >= (len(alive) - len(mafia_alive)) and not sk_alive:
        return "MAFIA"
    if len(sk_alive) == 1 and len(alive) <= 2 and not mafia_alive:
        return "SERIAL_KILLER"
    return None


async def run_mafia_cycle(message: Message, chat_id: int):
    game = MAFIA_LOBBIES.get(chat_id)
    if not game:
        return

    while chat_id in MAFIA_LOBBIES:
        game["night_num"] += 1
        game["phase"] = "NIGHT"
        game["night_actions"] = {}

        await message.answer(
            f"🌃 **NIGHT {game['night_num']} FALLS OVER THE CITY...**\n"
            "Special roles: check your bot DM to perform your night actions! (`35s`)"
        )

        # Send night action keyboards in DM
        for pid in list(game["alive"]):
            role = game["roles"][pid]
            if role in {"DON", "DETECTIVE", "DOCTOR", "BODYGUARD", "VIGILANTE", "CONSIGLIERE", "SERIAL_KILLER"}:
                targets = [t for t in game["alive"] if t != pid or role == "DOCTOR"]
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=game["players"][t], callback_data=f"mafnight:{chat_id}:{t}")]
                        for t in targets
                    ]
                )
                try:
                    await message.bot.send_message(pid, f"🌙 **Night {game['night_num']} Action ({ROLE_META[role][0]}):** Choose target:", reply_markup=kb)
                except Exception:
                    pass

        await asyncio.sleep(35)
        if chat_id not in MAFIA_LOBBIES:
            return

        # Resolve Night Actions
        actions = game["night_actions"]
        protected = set()
        kills = set()

        for actor, target in actions.items():
            if actor not in game["alive"]:
                continue
            r = game["roles"][actor]
            if r in {"DOCTOR", "BODYGUARD"}:
                protected.add(target)
            elif r in {"DON", "SERIAL_KILLER", "VIGILANTE"}:
                kills.add(target)
            elif r == "DETECTIVE":
                t_team = ROLE_META[game["roles"][target]][1]
                try:
                    await message.bot.send_message(actor, f"🔍 **Investigation Result:** `{game['players'][target]}` belongs to **{t_team}**.")
                except Exception:
                    pass
            elif r == "CONSIGLIERE":
                t_role = ROLE_META[game["roles"][target]][0]
                try:
                    await message.bot.send_message(actor, f"📜 **Consigliere Intel:** `{game['players'][target]}` is **{t_role}**.")
                except Exception:
                    pass

        casualties = []
        for victim in kills:
            if victim not in protected and victim in game["alive"]:
                game["alive"].remove(victim)
                casualties.append(f"💀 **{game['players'][victim]}** ({ROLE_META[game['roles'][victim]][0]})")

        new_don = promote_next_don(game)
        if new_don:
            try:
                await message.bot.send_message(new_don, "🎩 **The Don has fallen!** By seniority, you are now the **NEW DON**.")
            except Exception:
                pass

        game["phase"] = "MORNING"
        report = "\n".join(casualties) if casualties else "🌅 **A peaceful night!** Nobody was eliminated."
        await message.answer(f"☀️ **MORNING {game['night_num']} REPORT**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{report}")

        winner = check_mafia_winner(game)
        if winner:
            return await finalize_mafia_match(message, chat_id, winner)

        # Discussion & Voting
        game["phase"] = "DISCUSSION"
        await message.answer("🗣️ **DAY DISCUSSION (45s)** — Uncover the Mafia before voting begins!")
        await asyncio.sleep(45)
        if chat_id not in MAFIA_LOBBIES:
            return

        game["phase"] = "VOTING"
        game["votes"] = {}
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"⚖️ Vote {game['players'][p]}", callback_data=f"mafvote:{p}")]
                for p in game["alive"]
            ]
        )
        await message.answer("🗳️ **DAYTIME ELIMINATION VOTE (30s)**", reply_markup=kb)
        await asyncio.sleep(30)
        if chat_id not in MAFIA_LOBBIES:
            return

        tally: dict[int, int] = {}
        for voter, target in game["votes"].items():
            if voter in game["alive"]:
                weight = 2 if game["roles"][voter] == "MAYOR" else 1
                tally[target] = tally.get(target, 0) + weight

        if tally:
            executed = max(tally, key=tally.get)
            game["alive"].remove(executed)
            exec_role = game["roles"][executed]
            await message.answer(
                f"⚖️ **THE TOWN HAS SPOKEN!**\n"
                f"**{game['players'][executed]}** was executed! Role: **{ROLE_META[exec_role][0]}**"
            )
            if exec_role == "JESTER":
                return await finalize_mafia_match(message, chat_id, "JESTER", jester_id=executed)
            new_don = promote_next_don(game)
            if new_don:
                try:
                    await message.bot.send_message(new_don, "🎩 **The Don was executed!** You are now the **NEW DON**.")
                except Exception:
                    pass
        else:
            await message.answer("🤷 **No majority reached.** Nobody was executed today.")

        winner = check_mafia_winner(game)
        if winner:
            return await finalize_mafia_match(message, chat_id, winner)


async def finalize_mafia_match(message: Message, chat_id: int, winner: str, jester_id: int | None = None):
    game = MAFIA_LOBBIES.pop(chat_id, None)
    if not game:
        return

    summary = ["🏆 **ANIME MAFIA — MATCH CONCLUDED**", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━", f"🎉 **VICTORY: {winner} TEAM!**\n"]
    for pid, name in game["players"].items():
        role = game["roles"][pid]
        team = ROLE_META[role][1].upper()
        won = (winner == "JESTER" and pid == jester_id) or (winner == team) or (winner == "SERIAL_KILLER" and role == "SERIAL_KILLER")
        mode_tag = "mafia" if team == "MAFIA" else ("town" if team == "TOWN" else None)
        await record_progression(pid, chat_id, xp=300 if won else 75, coins=120 if won else 25, won_mode=mode_tag if won else None)
        summary.append(f"• **{name}** — {ROLE_META[role][0]} ({'🏆 WIN' if won else '💀 LOSS'})")

    await message.answer("\n".join(summary))


@router.callback_query(F.data.startswith("mafnight:"))
async def cb_mafia_night(callback: CallbackQuery):
    _, chat_id_s, target_s = callback.data.split(":")
    game = MAFIA_LOBBIES.get(int(chat_id_s))
    uid = callback.from_user.id
    if not game or game["phase"] != "NIGHT" or uid not in game["alive"]:
        return await callback.answer("Night action window closed.", show_alert=True)
    if uid in game["night_actions"]:
        return await callback.answer("Action already locked in!", show_alert=True)

    target = int(target_s)
    game["night_actions"][uid] = target
    await callback.message.edit_text(f"✅ Night target confirmed: **{game['players'][target]}**")
    await callback.answer()


@router.callback_query(F.data.startswith("mafvote:"))
async def cb_mafia_vote(callback: CallbackQuery):
    game = MAFIA_LOBBIES.get(callback.message.chat.id)
    uid = callback.from_user.id
    if not game or game["phase"] != "VOTING" or uid not in game["alive"]:
        return await callback.answer("Voting is closed or you are eliminated.", show_alert=True)
    target = int(callback.data.split(":")[1])
    game["votes"][uid] = target
    await callback.answer(f"⚖️ Vote registered against {game['players'][target]}!")
  
