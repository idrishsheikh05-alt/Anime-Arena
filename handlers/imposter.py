import asyncio
import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatType
from database import ensure_user, record_progression

router = Router()

IMPOSTER_LOBBIES: dict[int, dict] = {}

# Massive Comprehensive Anime Characters Pool (50+ per Big Anime, 20+ per other)
ANIME_CHARACTERS = [
    # ── NARUTO (50+ Characters) ──────────────────────────
    ("Naruto Uzumaki", "Naruto"), ("Sasuke Uchiha", "Naruto"), ("Sakura Haruno", "Naruto"), ("Kakashi Hatake", "Naruto"), ("Itachi Uchiha", "Naruto"),
    ("Madara Uchiha", "Naruto"), ("Obito Uchiha", "Naruto"), ("Minato Namikaze", "Naruto"), ("Jiraiya", "Naruto"), ("Tsunade", "Naruto"),
    ("Hinata Hyuga", "Naruto"), ("Shikamaru Nara", "Naruto"), ("Gaara", "Naruto"), ("Pain / Nagato", "Naruto"), ("Killer Bee", "Naruto"),
    ("Rock Lee", "Naruto"), ("Neji Hyuga", "Naruto"), ("Tent-Tent / Tenten", "Naruto"), ("Sai", "Naruto"), ("Yamato", "Naruto"),
    ("Hashirama Senju", "Naruto"), ("Tobirama Senju", "Naruto"), ("Hiruzen Sarutobi", "Naruto"), ("Danzo Shimura", "Naruto"), ("Orochimaru", "Naruto"),
    ("Kabuto Yakushi", "Naruto"), ("Deidara", "Naruto"), ("Sasori", "Naruto"), ("Hidan", "Naruto"), ("Kakuzu", "Naruto"),
    ("Kisame Hoshigaki", "Naruto"), ("Konan", "Naruto"), ("Zabuza Momochi", "Naruto"), ("Haku", "Naruto"), ("Kiba Inuzuka", "Naruto"),
    ("Shino Aburame", "Naruto"), ("Choji Akimichi", "Naruto"), ("Ino Yamanaka", "Naruto"), ("Temari", "Naruto"), ("Kankuro", "Naruto"),
    ("Mei Terumi", "Naruto"), ("A (Fourth Raikage)", "Naruto"), ("Onoki", "Naruto"), ("Darui", "Naruto"), ("Killer Bee", "Naruto"),
    ("Kushina Uzumaki", "Naruto"), ("Shisui Uchiha", "Naruto"), ("Indra Otsutsuki", "Naruto"), ("Asura Otsutsuki", "Naruto"), ("Kaguya Otsutsuki", "Naruto"),

    # ── ONE PIECE (50+ Characters) ───────────────────────
    ("Monkey D. Luffy", "One Piece"), ("Roronoa Zoro", "One Piece"), ("Nami", "One Piece"), ("Usopp", "One Piece"), ("Sanji", "One Piece"),
    ("Tony Tony Chopper", "One Piece"), ("Nico Robin", "One Piece"), ("Franky", "One Piece"), ("Brook", "One Piece"), ("Jinbe", "One Piece"),
    ("Trafalgar Law", "One Piece"), ("Portgas D. Ace", "One Piece"), ("Shanks", "One Piece"), ("Donquixote Doflamingo", "One Piece"), ("Kaido", "One Piece"),
    ("Big Mom / Charlotte Linlin", "One Piece"), ("Whitebeard / Edward Newgate", "One Piece"), ("Gol D. Roger", "One Piece"), ("Blackbeard / Marshall D. Teach", "One Piece"), ("Dracule Mihawk", "One Piece"),
    ("Sabo", "One Piece"), ("Vinsmoke Sanji", "One Piece"), ("Boa Hancock", "One Piece"), ("Crocodile", "One Piece"), ("Enel", "One Piece"),
    ("Rob Lucci", "One Piece"), ("Katakuri Charlotte", "One Piece"), ("Yamato", "One Piece"), ("Oden Kozuki", "One Piece"), ("Marco the Phoenix", "One Piece"),
    ("Silvers Rayleigh", "One Piece"), ("Bartholomew Kuma", "One Piece"), ("Emporio Ivankov", "One Piece"), ("Donquixote Rosinante / Corazon", "One Piece"), ("Smoker", "One Piece"),
    ("Tashigi", "One Piece"), ("Fujitora / Issho", "One Piece"), ("Kizaru / Borsalino", "One Piece"), ("Akainu / Sakazuki", "One Piece"), ("Aokiji / Kuzan", "One Piece"),
    ("Monkey D. Garp", "One Piece"), ("Sengoku", "One Piece"), ("Koby", "One Piece"), ("Helmeppo", "One Piece"), ("Buggy the Star Clown", "One Piece"),
    ("Arlong", "One Piece"), ("Hody Jones", "One Piece"), ("Caesar Clown", "One Piece"), ("Ceasar Clown", "One Piece"), ("Gecko Moria", "One Piece"),

    # ── BLEACH (50+ Characters) ──────────────────────────
    ("Ichigo Kurosaki", "Bleach"), ("Rukia Kuchiki", "Bleach"), ("Orihime Inoue", "Bleach"), ("Uryu Ishida", "Bleach"), ("Renji Abarai", "Bleach"),
    ("Byakuya Kuchiki", "Bleach"), ("Toshiro Hitsugaya", "Bleach"), ("Kenpachi Zaraki", "Bleach"), ("Sosuke Aizen", "Bleach"), ("Kisuke Urahara", "Bleach"),
    ("Yoruichi Shihouin", "Bleach"), ("Shunsui Kyoraku", "Bleach"), ("Jushiro Ukitake", "Bleach"), ("Gin Ichimaru", "Bleach"), ("Kaname Tosen", "Bleach"),
    ("Mayuri Kurotsuchi", "Bleach"), ("Sajin Komamura", "Bleach"), ("Retsu Unohana", "Bleach"), ("Soi Fon", "Bleach"), ("Yamamoto Genryusai", "Bleach"),
    ("Shinji Hirako", "Bleach"), ("Kensei Muguruma", "Bleach"), ("Love Aikawa", "Bleach"), ("Rose Otoribashi", "Bleach"), ("Mashiro Kuna", "Bleach"),
    ("Hiyori Sarugaki", "Bleach"), ("Lisa Yadomaru", "Bleach"), ("Hachigen Ushoda", "Bleach"), ("Yasutora Sado / Chad", "Bleach"), ("Kon", "Bleach"),
    ("Tatsuki Miyazawa", "Bleach"), ("Keigo Asano", "Bleach"), ("Mizuiro Kojima", "Bleach"), ("Don Kanonji", "Bleach"), ("Zangetsu", "Bleach"),
    ("Grimmjeow Jaegerjaquez", "Bleach"), ("Ulquiorra Cifer", "Bleach"), ("Nnoitora Gilga", "Bleach"), ("Neliel Tu Odelschwanck", "Bleatch"), ("Tier Harribel", "Bleach"),
    ("Starrk Coyote", "Bleach"), ("Baraggan Louisenbairn", "Bleach"), ("Yhwach", "Bleach"), ("Uryu's Father / Ryuken Ishida", "Bleach"), ("Isshin Kurosaki", "Bleach"),
    ("Masaki Kurosaki", "Bleatch"), ("Senjumaru Shutara", "Bleach"), ("Kirio Hikifune", "Bleach"), ("Oetsu Nimaiya", "Bleach"), ("Ichibe Hyosube", "Bleach"),

    # ── DRAGON BALL (50+ Characters) ─────────────────────
    ("Son Goku", "Dragon Ball"), ("Vegeta", "Dragon Ball"), ("Son Gohan", "Dragon Ball"), ("Piccolo", "Dragon Ball"), ("Future Trunks", "Dragon Ball"),
    ("Krillin", "Dragon Ball"), ("Bulma", "Dragon Ball"), ("Master Roshi", "Dragon Ball"), ("Android 18", "Dragon Ball"), ("Frieza", "Dragon Ball"),
    ("Beerus", "Dragon Ball"), ("Whis", "Dragon Ball"), ("Goku Black", "Dragon Ball"), ("Broly", "Dragon Ball"), ("Jiren", "Dragon Ball"),
    ("Cell", "Dragon Ball"), ("Majin Buu", "Dragon Ball"), ("Raditz", "Dragon Ball"), ("Nappa", "Dragon Ball"), ("Chi-Chi", "Dragon Ball"),
    ("Videl", "Dragon Ball"), ("Yamcha", "Dragon Ball"), ("Tien Shinhan", "Dragon Ball"), ("Chiaotzu", "Dragon Ball"), ("Android 17", "Dragon Ball"),
    ("Android 16", "Dragon Ball"), ("Zamasu", "Dragon Ball"), ("Gogeta", "Dragon Ball"), ("Vegito", "Dragon Ball"), ("Goten", "Dragon Ball"),
    ("Trunks (Kid)", "Dragon Ball"), ("Pan", "Dragon Ball"), ("Bardock", "Dragon Ball"), ("King Vegeta", "Dragon Ball"), ("King Kai", "Dragon Ball"),
    ("Grand Kai", "Dragon Ball"), ("Grand Priest", "Dragon Ball"), ("Zeno", "Dragon Ball"), ("Toppo", "Dragon Ball"), ("Dyspo", "Dragon Ball"),
    ("Hit", "Dragon Ball"), ("Cabba", "Dragon Ball"), ("Caulifla", "Dragon Ball"), ("Kale", "Dragon Ball"), ("Kefla", "Dragon Ball"),
    ("Dende", "Dragon Ball"), ("Mr. Satan / Hercule", "Dragon Ball"), ("Oolong", "Dragon Ball"), ("Puar", "Dragon Ball"), ("Shenron", "Dragon Ball"),

    # ── JUJUTSU KAISEN (50+ Characters) ──────────────────
    ("Yuji Itadori", "Jujutsu Kaisen"), ("Megumi Fushiguro", "Jujutsu Kaisen"), ("Nobara Kugisaki", "Jujutsu Kaisen"), ("Satoru Gojo", "Jujutsu Kaisen"), ("Ryomen Sukuna", "Jujutsu Kaisen"),
    ("Yuta Okkotsu", "Jujutsu Kaisen"), ("Maki Zenin", "Jujutsu Kaisen"), ("Toge Inumaki", "Jujutsu Kaisen"), ("Kento Nanami", "Jujutsu Kaisen"), ("Suguru Geto", "Jujutsu Kaisen"),
    ("Toji Fushiguro", "Jujutsu Kaisen"), ("Choso", "Jujutsu Kaisen"), ("Mahito", "Jujutsu Kaisen"), ("Kenjaku", "Jujutsu Kaisen"), ("Hajime Kashimo", "Jujutsu Kaisen"),
    ("Panda", "Jujutsu Kaisen"), ("Aoi Todo", "Jujutsu Kaisen"), ("Kasumi Miwa", "Jujutsu Kaisen"), ("Kokichi Muta / Mechamaru", "Jujutsu Kaisen"), ("Noritoshi Kamo", "Jujutsu Kaisen"),
    ("Momo Nishimiya", "Jujutsu Kaisen"), ("Mai Zenin", "Jujutsu Kaisen"), ("Megumi's Sister / Tsumiki Fushiguro", "Jujutsu Kaisen"), ("Shoko Ieiri", "Jujutsu Kaisen"), ("Masamichi Yaga", "Jujutsu Kaisen"),
    ("Kiyotaka Ijichi", "Jujutsu Kaisen"), ("Akutami Gege / Narrator", "Jujutsu Kaisen"), ("Kinji Hakari", "Jujutsu Kaisen"), ("Kirara Hoshi", "Jujutsu Kaisen"), ("Takaba Fumihiko", "Jujutsu Kaisen"),
    ("Angel / Hana Kurusu", "Jujutsu Kaisen"), ("Uraume", "Jujutsu Kaisen"), ("Jogo", "Jujutsu Kaisen"), ("Hanami", "Jujutsu Kaisen"), ("Dagon", "Jujutsu Kaisen"),
    ("Jogo", "Jujutsu Kaisen"), ("Naobito Zenin", "Jujutsu Kaisen"), ("Naoya Zenin", "Jujutsu Kaisen"), ("Ogi Zenin", "Jujutsu Kaisen"), ("Jin Itadori", "Jujutsu Kaisen"),
    ("Wasuke Itadori", "Jujutsu Kaisen"), ("Rika Orimoto", "Jujutsu Kaisen"), ("Ino Takuma", "Jujutsu Kaisen"), ("Yaga Masamichi", "Jujutsu Kaisen"), ("Gakuganji", "Jujutsu Kaisen"),
    ("Mei Mei", "Jujutsu Kaisen"), ("Ui Ui", "Jujutsu Kaisen"), ("Yuki Tsukumo", "Jujutsu Kaisen"), ("Garou / Cursed Spirits", "Jujutsu Kaisen"), ("Reggie Star", "Jujutsu Kaisen"),

    # ── DEMON SLAYER (50+ Characters) ────────────────────
    ("Tanjiro Kamado", "Demon Slayer"), ("Nezuko Kamado", "Demon Slayer"), ("Zenitsu Agatsuma", "Demon Slayer"), ("Inosuke Hashibira", "Demon Slayer"), ("Giyu Tomioka", "Demon Slayer"),
    ("Shinobu Kocho", "Demon Slayer"), ("Kyojuro Rengoku", "Demon Slayer"), ("Tengen Uzui", "Demon Slayer"), ("Mitsuri Kanroji", "Demon Slayer"), ("Muichiro Tokito", "Demon Slayer"),
    ("Sanemi Shinazugawa", "Demon Slayer"), ("Obanai Iguro", "Demon Slayer"), ("Gyomei Himejima", "Demon Slayer"), ("Kanao Tsuyuri", "Demon Slayer"), ("Genya Shinazugawa", "Demon Slayer"),
    ("Muzan Kibutsuji", "Demon Slayer"), ("Kokushibo", "Demon Slayer"), ("Doma", "Demon Slayer"), ("Akaza", "Demon Slayer"), ("Hantengu", "Demon Slayer"),
    ("Gyokko", "Demon Slayer"), ("Daki", "Demon Slayer"), ("Gyutaro", "Demon Slayer"), ("Enmu", "Demon Slayer"), ("Rui", "Demon Slayer"),
    ("Yoriichi Tsugikuni", "Demon Slayer"), ("Michikatsu Tsugikuni", "Demon Slayer"), ("Kagaya Ubuyashiki", "Demon Slayer"), ("Amane Ubuyashiki", "Demon Slayer"), ("Senjuro Rengoku", "Demon Slayer"),
    ("Shinjuro Rengoku", "Demon Slayer"), ("Sakonji Urokodaki", "Demon Slayer"), ("Sabito", "Demon Slayer"), ("Makomo", "Demon Slayer"), ("Tamayo", "Demon Slayer"),
    ("Yushiro", "Demon Slayer"), ("Murata", "Demon Slayer"), ("Aoi Kanzaki", "Demon Slayer"), ("Sumi Nakahara", "Demon Slayer"), ("Kiyo Terauchi", "Demon Slayer"),
    ("Naho Takada", "Demon Slayer"), ("Yushiro", "Demon Slayer"), ("Kibutsuji Muzan", "Demon Slayer"), ("Nakime", "Demon Slayer"), ("Kaigaku", "Demon Slayer"),
    ("Susamaru", "Demon Slayer"), ("Yahaba", "Demon Slayer"), ("Spider Demon Mother", "Demon Slayer"), ("Spider Demon Father", "Demon Slayer"), ("Spider Demon Older Brother", "Demon Slayer"),

    # ── ATTACK ON TITAN (50+ Characters) ─────────────────
    ("Eren Yeager", "Attack on Titan"), ("Mikasa Ackerman", "Attack on Titan"), ("Armin Arlert", "Attack on Titan"), ("Levi Ackerman", "Attack on Titan"), ("Erwin Smith", "Attack on Titan"),
    ("Hange Zoe", "Attack on Titan"), ("Jean Kirstein", "Attack on Titan"), ("Connie Springer", "Attack on Titan"), ("Sasha Blouse", "Attack on Titan"), ("Historia Reiss", "Attack on Titan"),
    ("Reiner Braun", "Attack on Titan"), ("Bertholdt Hoover", "Attack on Titan"), ("Annie Leonhart", "Attack on Titan"), ("Zeke Yeager", "Attack on Titan"), ("Pieck Finger", "Attack on Titan"),
    ("Porco Galliard", "Attack on Titan"), ("Gabi Braun", "Attack on Titan"), ("Falco Grice", "Attack on Titan"), ("Yelena", "Attack on Titan"), ("Onyankopon", "Attack on Titan"),
    ("Floch Forster", "Attack on Titan"), ("Grisha Yeager", "Attack on Titan"), ("Carla Yeager", "Attack on Titan"), ("Dina Fritz", "Attack on Titan"), ("Kenny Ackerman", "Attack on Titan"),
    ("Ymir Fritz", "Attack on Titan"), ("Kitz Woermann", "Attack on Titan"), ("Hannes", "Attack on Titan"), ("Ian Dietrich", "Attack on Titan"), ("Rico Brzenska", "Attack on Titan"),
    ("Marco Bott", "Attack on Titan"), ("Daz", "Attack on Titan"), ("Samuel", "Attack on Titan"), ("Moblit Berner", "Attack on Titan"), ("Nile Dawk", "Attack on Titan"),
    ("Zackly", "Attack on Titan"), ("Pyxis", "Attack on Titan"), ("Rod Reiss", "Attack on Titan"), ("Frieda Reiss", "Attack on Titan"), ("Uri Reiss", "Attack on Titan"),
    ("Faye Yeager", "Attack on Titan"), ("Mr. Leonhart", "Attack on Titan"), ("Mr. Braun", "Attack on Titan"), ("Mrs. Braun", "Attack on Titan"), ("Kruger / Owl", "Attack on Titan"),
    ("Tom Ksaver", "Attack on Titan"), ("Helos", "Attack on Titan"), ("Willy Tybur", "Attack on Titan"), ("Lara Tybur", "Attack on Titan"), ("Kiyomi Azumabito", "Attack on Titan"),

    # ── MY HERO ACADEMIA (50+ Characters) ────────────────
    ("Izuku Midoriya", "My Hero Academia"), ("Katsuki Bakugo", "My Hero Academia"), ("Shoto Todoroki", "My Hero Academia"), ("Ochaco Uraraka", "My Hero Academia"), ("Tenya Iida", "My Hero Academia"),
    ("All Might", "My Hero Academia"), ("Shota Aizawa", "My Hero Academia"), ("Eijiro Kirishima", "My Hero Academia"), ("Momo Yaoyorozu", "My Hero Academia"), ("Denki Kaminari", "My Hero Academia"),
    ("Kyoka Jiro", "My Hero Academia"), ("Fumikage Tokoyami", "My Hero Academia"), ("Tsuyu Asui", "My Hero Academia"), ("Minoru Mineta", "My Hero Academia"), ("Mina Ashido", "My Hero Academia"),
    ("Hanta Sero", "My Hero Academia"), ("Yuga Aoyama", "My Hero Academia"), ("Toru Hagakure", "My Hero Academia"), ("Mezo Shoji", "My Hero Academia"), ("Mashirao Ojiro", "My Hero Academia"),
    ("Koji Koda", "My Hero Academia"), ("Rikido Sato", "My Hero Academia"), ("Ejirou Kirishima", "My Hero Academia"), ("Hitoshi Shinso", "My Hero Academia"), ("Neito Monoma", "My Hero Academia"),
    ("Itsuka Kendo", "My Hero Academia"), ("Ibara Shiozaki", "My Hero Academia"), ("Tetsutetsu Tetsutetsu", "My Hero Academia"), ("Mirio Togata", "My Hero Academia"), ("Nejire Hado", "My Hero Academia"),
    ("Tamaki Amajiki", "My Hero Academia"), ("Hawks / Keigo Takami", "My Hero Academia"), ("Endeavor / Enji Todoroki", "My Hero Academia"), ("Best Jeanist", "My Hero Academia"), ("Edgeshot", "My Hero Academia"),
    ("Mirko / Rumi Usagiyama", "My Hero Academia"), ("Gran Torino", "My Hero Academia"), ("Tomura Shigaraki", "My Hero Academia"), ("Dabi / Toya Todoroki", "My Hero Academia"), ("Himiko Toga", "My Hero Academia"),
    ("Spinner", "My Hero Academia"), ("Compress", "My Hero Academia"), ("Twice / Jin Bubaigawara", "My Hero Academia"), ("Gigantomachia", "My Hero Academia"), ("All For One", "My Hero Academia"),
    ("Overhaul / Chisaki", "My Hero Academia"), ("Stain / Chizuru Akaguro", "My Hero Academia"), ("Gentle Criminal", "My Hero Academia"), ("La Brava", "My Hero Academia"), ("Eri", "My Hero Academia"),

    # ── HUNTER X HUNTER (50+ Characters) ─────────────────
    ("Gon Freecss", "Hunter x Hunter"), ("Killua Zoldyck", "Hunter x Hunter"), ("Kurapika", "Hunter x Hunter"), ("Leorio Paradinight", "Hunter x Hunter"), ("Hisoka Morow", "Hunter x Hunter"),
    ("Chrollo Lucilfer", "Hunter x Hunter"), ("Meruem", "Hunter x Hunter"), ("Neferpitou", "Hunter x Hunter"), ("Menthuthuyoupi", "Hunter x Hunter"), ("Shaiapouf", "Hunter x Hunter"),
    ("Isaac Netero", "Hunter x Hunter"), ("Ging Freecss", "Hunter x Hunter"), ("Kite", "Hunter x Hunter"), ("Illumi Zoldyck", "Hunter x Hunter"), ("Zeno Zoldyck", "Hunter x Hunter"),
    ("Silva Zoldyck", "Hunter x Hunter"), ("Kikyo Zoldyck", "Hunter x Hunter"), ("Milluki Zoldyck", "Hunter x Hunter"), ("Alluka Zoldyck", "Hunter x Hunter"), ("Kalluto Zoldyck", "Hunter x Hunter"),
    ("Biscuit Krueger / Bisky", "Hunter x Hunter"), ("Morel Mackernasey", "Hunter x Hunter"), ("Knov", "Hunter x Hunter"), ("Knuckle Bine", "Hunter x Hunter"), ("Shoot McMahon", "Hunter x Hunter"),
    ("Palm Siberia", "Hunter x Hunter"), ("Ikalgo", "Hunter x Hunter"), ("Meleoron", "Hunter x Hunter"), ("Komugi", "Hunter x Hunter"), ("Phinks Magcub", "Hunter x Hunter"),
    ("Feitan Portor", "Hunter x Hunter"), ("Machi Komacine", "Hunter x Hunter"), ("Nobunaga Hazama", "Hunter x Hunter"), ("Shalnark", "Hunter x Hunter"), ("Franklin Bordeau", "Hunter x Hunter"),
    ("Bonolenov Ndongo", "Hunter x Hunter"), ("Uvogin", "Hunter x Hunter"), ("Pakunoda", "Hunter x Hunter"), ("Genthru", "Hunter x Hunter"), ("Razor", "Hunter x Hunter"),
    ("Tonpa", "Hunter x Hunter"), ("Hanzo", "Hunter x Hunter"), ("Pokkle", "Hunter x Hunter"), ("Bourbon", "Hunter x Hunter"), ("Menchi", "Hunter x Hunter"),
    ("Buhara", "Hunter x Hunter"), ("Satotz", "Hunter x Hunter"), ("Tenth Zodiacs / Pariston Hill", "Hunter x Hunter"), ("Cheadle Yorkshire", "Hunter x Hunter"), ("Beyond Netero", "Hunter x Hunter"),

    # ── OTHER ANIME (20+ Characters Each) ────────────────
    # Chainsaw Man
    ("Denji", "Chainsaw Man"), ("Aki Hayakawa", "Chainsaw Man"), ("Power", "Chainsaw Man"), ("Makima", "Chainsaw Man"), ("Himeno", "Chainsaw Man"),
    ("Kobeni Higashiyama", "Chainsaw Man"), ("Hirofumi Yoshida", "Chainsaw Man"), ("Kishibe", "Chainsaw Man"), ("Reze", "Chainsaw Man"), ("Quanxi", "Chainsaw Man"),
    ("Beam", "Chainsaw Man"), ("Violence Fiend", "Chainsaw Man"), ("Angel Devil", "Chainsaw Man"), ("Control Devil", "Chainsaw Man"), ("War Devil / Asa Mitaka", "Chainsaw Man"),
    ("Yuko", "Chainsaw Man"), ("Darkness Devil", "Chainsaw Man"), ("Gun Devil", "Chainsaw Man"), ("Eternity Devil", "Chainsaw Man"), ("Bat Devil", "Chainsaw Man"),
    
    # Tokyo Ghoul
    ("Ken Kaneki", "Tokyo Ghoul"), ("Touka Kirishima", "Tokyo Ghoul"), ("Rize Kamishiro", "Tokyo Ghoul"), ("Shuu Tsukiyama", "Tokyo Ghoul"), ("Koutarou Amon", "Tokyo Ghoul"),
    ("Juuzou Suzuya", "Tokyo Ghoul"), ("Kishou Arima", "Tokyo Ghoul"), ("Yoshimura", "Tokyo Ghoul"), ("Renji Yomo", "Tokyo Ghoul"), ("Hinami Fueguchi", "Tokyo Ghoul"),
    ("Uta", "Tokyo Ghoul"), ("Itori", "Tokyo Ghoul"), ("Nishiki Nishio", "Tokyo Ghoul"), ("Ayato Kirishima", "Tokyo Ghoul"), ("Eto Yoshimura", "Tokyo Ghoul"),
    ("Tatara", "Tokyo Ghoul"), ("Seidou Takizawa", "Tokyo Ghoul"), ("Haise Sasaki", "Tokyo Ghoul"), ("Noro", "Tokyo Ghoul"), ("Yamori / Jason", "Tokyo Ghoul"),

    # Death Note & Code Geass
    ("Light Yagami", "Death Note"), ("L Lawliet", "Death Note"), ("Misa Amane", "Death Note"), ("Ryuk", "Death Note"), ("Rem", "Death Note"),
    ("Near / Nate River", "Death Note"), ("Mello / Mihael Keehl", "Death Note"), ("Soichiro Yagami", "Death Note"), ("Teru Mikami", "Death Note"), ("Kiyomi Takada", "Death Note"),
    ("Lelouch vi Britannia", "Code Geass"), ("C.C.", "Code Geass"), ("Suzaku Kururugi", "Code Geass"), ("Kallen Stadtfeld", "Code Geass"), ("Nunnally vi Britannia", "Code Geass"),
    ("Shirley Fenette", "Code Geass"), ("Lloyd Asplund", "Code Geass"), ("Cornelia li Britannia", "Code Geass"), ("Zero", "Code Geass"), ("V.V.", "Code Geass"),

    # Solo Leveling & One Punch Man
    ("Sung Jinwoo", "Solo Leveling"), ("Cha Hae-In", "Solo Leveling"), ("Baek Yoonho", "Solo Leveling"), ("Choi Jong-In", "Solo Leveling"), ("Go Gunhee", "Solo Leveling"),
    ("Woo Jinchul", "Solo Leveling"), ("Yoo Jinho", "Solo Leveling"), ("Thomas Andre", "Solo Leveling"), ("Christopher Reed", "Solo Leveling"), ("Liu Zhigang", "Solo Leveling"),
    ("Saitama", "One Punch Man"), ("Genos", "One Punch Man"), ("Tatsumaki", "One Punch Man"), ("Fubuki", "One Punch Man"), ("Bang / Silver Fang", "One Punch Man"),
    ("Garou", "One Punch Man"), ("King", "One Punch Man"), ("Sonic / Speed-o'-Sound Sonic", "One Punch Man"), ("Metal Bat", "One Punch Man"), ("Mumen Rider", "One Punch Man")
]


def is_group_chat(message: Message) -> bool:
    return message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]


def get_imposter_lobby_text(host_name: str, host_id: int, mode: str, category: str, players_dict: dict) -> str:
    if players_dict:
        player_list = "\n".join(
            [f"{idx}. 🕵️ [{name}](tg://user?id={uid})" for idx, (uid, name) in enumerate(players_dict.items(), 1)]
        )
    else:
        player_list = "• *Waiting for detectives to assemble...*"

    host_mention = f"[{host_name}](tg://user?id={host_id})"

    return (
        f"🕵️ **GUESS THE IMPOSTER — LOBBY ({mode.upper()} MODE)**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 **Host:** {host_mention}\n"
        f"🎯 **Category:** `{category.title()}`\n"
        f"👥 **Agents Joined ({len(players_dict)}/10):** (Min 3 required)\n"
        f"{player_list}\n\n"
        f"⚠️ *Every player must start the bot privately first so secret characters can be delivered via DM!*\n\n"
        f"👉 Type `/join` to enter • `/startgame` to begin!"
    )


@router.message(Command("imposter"))
async def cmd_imposter_create(message: Message):
    if not is_group_chat(message):
        return await message.answer(
            "❌ **Guess the Imposter can only be played inside group chats!** Add me to a group to host a match.",
            parse_mode="Markdown",
        )

    chat_id = message.chat.id
    if chat_id in IMPOSTER_LOBBIES:
        return await message.reply("⚠️ An Imposter lobby is already active in this group!")

    args = message.text.split(maxsplit=2)
    mode = "classic"
    category = "random"

    if len(args) > 1:
        potential_mode = args[1].lower()
        if potential_mode in {"classic", "double", "blind"}:
            mode = potential_mode
            if len(args) > 2:
                category = args[2].lower()
        else:
            category = " ".join(args[1:]).lower()

    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    IMPOSTER_LOBBIES[chat_id] = {
        "host": message.from_user.id,
        "host_name": message.from_user.full_name,
        "mode": mode,
        "category": category,
        "phase": "WAITING",
        "players": {message.from_user.id: message.from_user.full_name},
        "alive": set(),
        "imposters": set(),
        "hints": {},
        "votes": {},
        "round_num": 0,
    }

    lobby_text = get_imposter_lobby_text(
        host_name=message.from_user.full_name,
        host_id=message.from_user.id,
        mode=mode,
        category=category,
        players_dict=IMPOSTER_LOBBIES[chat_id]["players"],
    )
    await message.answer(lobby_text, parse_mode="Markdown")


@router.message(Command("animes"))
async def cmd_list_animes(message: Message):
    series_set = sorted(list(set(series for _, series in ANIME_CHARACTERS)))
    text = (
        f"📚 **AVAILABLE ANIME CATEGORIES & DATABASE**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Total Characters: **Massive 500+ Character Pool** across franchises!\n\n"
        f"🔥 **Featured Series:**\n" + "".join(f"• `{s}`\n" for s in series_set) +
        f"\n👉 *Usage example:* `/imposter classic naruto`"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("join"))
async def cmd_generic_join(message: Message):
    if not is_group_chat(message):
        return await message.reply("❌ Game lobbies can only be joined inside group chats.")

    chat_id = message.chat.id
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

    lobby_text = get_imposter_lobby_text(
        host_name=lobby["host_name"],
        host_id=lobby["host"],
        mode=lobby["mode"],
        category=lobby["category"],
        players_dict=lobby["players"],
    )
    await message.answer(
        f"🕵️ **{message.from_user.full_name}** joined the Imposter lobby!\n\n{lobby_text}",
        parse_mode="Markdown",
    )


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
            new_host_id = next(iter(lobby["players"]))
            lobby["host"] = new_host_id
            lobby["host_name"] = lobby["players"][new_host_id]
            await message.answer(f"👑 Host left! New host: **{lobby['players'][new_host_id]}**", parse_mode="Markdown")
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
    lobby["alive"] = list(player_ids)

    cat = lobby["category"]
    filtered_pool = ANIME_CHARACTERS if cat == "random" else [c for c in ANIME_CHARACTERS if cat in c[1].lower()]
    if len(filtered_pool) < 2:
        filtered_pool = ANIME_CHARACTERS

    crew_tuple, imp_tuple = random.sample(filtered_pool, k=2)
    crew_char, imp_char = crew_tuple[0], imp_tuple[0]

    lobby["crew_char"] = crew_char
    lobby["imp_char"] = imp_char

    imp_count = 2 if (lobby["mode"] == "double" and len(player_ids) >= 5) else 1
    imposters = set(random.sample(player_ids, k=imp_count))
    lobby["imposters"] = imposters

    for pid in player_ids:
        try:
            if pid in imposters:
                if lobby["mode"] == "blind":
                    secret_text = (
                        "🤫 **YOU ARE THE IMPOSTER! (BLIND MODE)**\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🙈 You received **NO character**!\n"
                        "Listen to everyone else's descriptions, blend in, and survive the vote!"
                    )
                else:
                    secret_text = (
                        "🤫 **YOU ARE THE IMPOSTER!**\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎭 **Your Decoy Character:** `{imp_char}`\n"
                        "Everyone else got a different character! Describe yours carefully so you don't get caught!"
                    )
            else:
                secret_text = (
                    "🛡️ **YOU ARE A CREWMATE!**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌟 **Your Anime Character:** `{crew_char}`\n"
                    "Describe this character without making it too obvious for the Imposter!"
                )
            await message.bot.send_message(pid, secret_text, parse_mode="Markdown")
        except Exception:
            IMPOSTER_LOBBIES.pop(chat_id, None)
            return await message.answer(
                f"❌ **DM Delivery Failed!** **{lobby['players'][pid]}** must start the bot in private chat first. Match aborted."
            )

    bot_user = await message.bot.get_me()
    dm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Check Secret Character in DM", url=f"https://t.me/{bot_user.username}?start=secret")]
        ]
    )

    await message.answer(
        "📩 **SECRET ANIME CHARACTERS SENT VIA DM!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Tap the button below to open private chat and view your assigned character. Get ready!",
        reply_markup=dm_kb,
        parse_mode="Markdown"
    )

    asyncio.create_task(run_imposter_phases(message, chat_id))


async def run_imposter_phases(message: Message, chat_id: int):
    lobby = IMPOSTER_LOBBIES.get(chat_id)
    if not lobby:
        return

    while chat_id in IMPOSTER_LOBBIES:
        lobby["round_num"] += 1
        lobby["phase"] = "DESCRIBING"
        lobby["hints"] = {}
        lobby["votes"] = {}

        await message.answer(
            f"🗣️ **ROUND {lobby['round_num']} — TURN-BY-TURN DESCRIPTIONS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Players will now describe their character one by one in order!",
            parse_mode="Markdown"
        )

        for uid in list(lobby["alive"]):
            if chat_id not in IMPOSTER_LOBBIES:
                return
            p_name = lobby["players"][uid]
            await message.answer(
                f"🎯 **Turn:** [{p_name}](tg://user?id={uid})\n"
                f"👉 Describe your character now! (You have **45 seconds**)",
                parse_mode="Markdown"
            )
            await asyncio.sleep(45)

        lobby["phase"] = "VOTING"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"🗳️ Vote {lobby['players'][uid]}", callback_data=f"impvote:{chat_id}:{uid}")]
                for uid in lobby["alive"]
            ]
        )
        await message.answer(
            f"🗳️ **ROUND {lobby['round_num']} — ELIMINATION VOTING (45s)**\n"
            f"Who is describing a different character? Tap below to vote!",
            reply_markup=kb,
            parse_mode="Markdown",
        )
        await asyncio.sleep(45)
        if chat_id not in IMPOSTER_LOBBIES:
            return

        tally: dict[int, int] = {}
        for voter, target in lobby["votes"].items():
            if voter in lobby["alive"] and target in lobby["alive"]:
                tally[target] = tally.get(target, 0) + 1

        if tally:
            eliminated = max(tally, key=tally.get)
            lobby["alive"].remove(eliminated)
            was_imp = eliminated in lobby["imposters"]
            await message.answer(
                f"⚖️ **VOTING RESULTS — ROUND {lobby['round_num']}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚫 **{lobby['players'][eliminated]}** was voted out!\n"
                f"Identity: **{'🤫 AN IMPOSTER!' if was_imp else '🛡️ AN INNOCENT CREWMATE!'}**",
                parse_mode="Markdown",
            )
        else:
            await message.answer(
                f"🤷 **No votes cast in Round {lobby['round_num']}!** Nobody was eliminated.",
                parse_mode="Markdown",
            )

        alive_imps = [u for u in lobby["alive"] if u in lobby["imposters"]]
        alive_crew = [u for u in lobby["alive"] if u not in lobby["imposters"]]

        if not alive_imps:
            await finalize_imposter_match(message, chat_id, crew_won=True)
            return

        if len(lobby["alive"]) == 2 and len(alive_imps) == 1:
            await finalize_imposter_match(message, chat_id, crew_won=False)
            return

        if len(alive_imps) >= len(alive_crew):
            await finalize_imposter_match(message, chat_id, crew_won=False)
            return

        await asyncio.sleep(3)


async def finalize_imposter_match(message: Message, chat_id: int, crew_won: bool):
    lobby = IMPOSTER_LOBBIES.pop(chat_id, None)
    if not lobby:
        return

    imp_names = ", ".join(lobby["players"][i] for i in lobby["imposters"])
    imp_char_display = "None (Blind Mode)" if lobby["mode"] == "blind" else lobby["imp_char"]

    for uid in lobby["players"]:
        is_imp = uid in lobby["imposters"]
        won = (not is_imp and crew_won) or (is_imp and not crew_won)
        await record_progression(
            uid,
            chat_id,
            xp=250 if won else 60,
            coins=100 if won else 25,
            won_mode="imposter" if won else None,
        )

    await message.answer(
        f"🎭 **GUESS THE IMPOSTER — FINAL RESULTS**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 **{'CREWMATES WIN! All Imposters caught!' if crew_won else 'IMPOSTER WINS! They survived to the end!'}**\n\n"
        f"🤫 **True Imposter(s):** `{imp_names}`\n"
        f"🌟 **Crewmate Character:** `{lobby['crew_char']}`\n"
        f"🎭 **Imposter Character:** `{imp_char_display}`",
        parse_mode="Markdown",
    )


@router.message(Command("hint"))
async def cmd_submit_hint(message: Message):
    lobby = IMPOSTER_LOBBIES.get(message.chat.id)
    if not lobby or lobby["phase"] != "DESCRIBING":
        return
    uid = message.from_user.id
    if uid not in lobby["alive"]:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply("Usage: `/hint <your description>`")
    lobby["hints"][uid] = parts[1][:100]
    await message.reply(f"✅ Clue saved for **{message.from_user.full_name}**!")


@router.callback_query(F.data.startswith("impvote:"))
async def cb_imposter_vote(callback: CallbackQuery):
    _, chat_id_s, target_s = callback.data.split(":")
    lobby = IMPOSTER_LOBBIES.get(int(chat_id_s))
    if not lobby or lobby["phase"] != "VOTING":
        return await callback.answer("Voting is closed.", show_alert=True)
    voter = callback.from_user.id
    if voter not in lobby["alive"]:
        return await callback.answer("You are eliminated or not in this match.", show_alert=True)
    target = int(target_s)
    if target not in lobby["alive"]:
        return await callback.answer("That player is already eliminated.", show_alert=True)
    lobby["votes"][voter] = target
    await callback.answer(f"🗳️ Vote cast against {lobby['players'][target]}!")
    

