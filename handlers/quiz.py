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
        # ===== PART 1: QUESTIONS 1-100 =====

    {"cat": "Anime Knowledge", "diff": "Easy", "xp": 50, "q": "What is the name of Naruto's father?", "opts": ["Jiraiya", "Minato Namikaze", "Hiruzen Sarutobi", "Fugaku Uchiha"], "ans": 1},
    {"cat": "Anime Knowledge", "diff": "Medium", "xp": 100, "q": "Who was the first person to awaken the Mangekyo Sharingan in the Uchiha clan's history?", "opts": ["Madara Uchiha", "Itachi Uchiha", "Indra Otsutsuki", "Sasuke Uchiha"], "ans": 2},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character is known as the Copy Ninja?", "opts": ["Might Guy", "Kakashi Hatake", "Jiraiya", "Orochimaru"], "ans": 1},
    {"cat": "Anime Knowledge", "diff": "Medium", "xp": 100, "q": "What is the name of the Nine-Tailed Fox sealed inside Naruto?", "opts": ["Shukaku", "Gyuki", "Kurama", "Matatabi"], "ans": 2},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "Who was the Ten-Tails' jinchuriki during the Fourth Great Ninja War?", "opts": ["Hashirama", "Obito Uchiha", "Nagato", "Killer Bee"], "ans": 1},
    {"cat": "Anime Knowledge", "diff": "Easy", "xp": 50, "q": "Which village is Gaara from?", "opts": ["Konohagakure", "Kirigakure", "Sunagakure", "Iwagakure"], "ans": 2},
    {"cat": "Who Said It?", "diff": "Medium", "xp": 100, "q": "Who famously said, 'Wake up to reality'?", "opts": ["Pain", "Madara Uchiha", "Obito Uchiha", "Itachi Uchiha"], "ans": 1},
    {"cat": "Anime Knowledge", "diff": "Hard", "xp": 150, "q": "What is the name of the Sage of Six Paths?", "opts": ["Hamura Otsutsuki", "Hagoromo Otsutsuki", "Toneri Otsutsuki", "Indra Otsutsuki"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which Naruto character uses the Eight Gates technique?", "opts": ["Shikamaru", "Might Guy", "Neji", "Kiba"], "ans": 1},
    {"cat": "Anime Knowledge", "diff": "Medium", "xp": 100, "q": "Who trained the legendary Sannin?", "opts": ["Danzo", "Hiruzen Sarutobi", "Tobirama", "Minato"], "ans": 1},

    {"cat": "One Piece", "diff": "Easy", "xp": 50, "q": "What is the name of Luffy's first ship?", "opts": ["Thousand Sunny", "Going Merry", "Red Force", "Oro Jackson"], "ans": 1},
    {"cat": "One Piece", "diff": "Medium", "xp": 100, "q": "Who was the first member to join Luffy's crew?", "opts": ["Sanji", "Usopp", "Roronoa Zoro", "Nami"], "ans": 2},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character is known as the Surgeon of Death?", "opts": ["Eustass Kid", "Trafalgar D. Water Law", "Dracule Mihawk", "Crocodile"], "ans": 1},
    {"cat": "One Piece", "diff": "Medium", "xp": 100, "q": "What is the name of Sanji's family?", "opts": ["Donquixote", "Vinsmoke", "Charlotte", "Nefertari"], "ans": 1},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "Who was the captain of the Rocks Pirates?", "opts": ["Gol D. Roger", "Edward Newgate", "Rocks D. Xebec", "Shiki"], "ans": 2},
    {"cat": "One Piece", "diff": "Easy", "xp": 50, "q": "What is the name of Chopper's Devil Fruit?", "opts": ["Hito Hito no Mi", "Ushi Ushi no Mi", "Inu Inu no Mi", "Neko Neko no Mi"], "ans": 0},
    {"cat": "One Piece", "diff": "Medium", "xp": 100, "q": "Which island is the home of the Revolutionary Army's headquarters?", "opts": ["Dressrosa", "Baltigo", "Wano", "Punk Hazard"], "ans": 1},
    {"cat": "Who Said It?", "diff": "Medium", "xp": 100, "q": "Who said, 'I want to live!' at Enies Lobby?", "opts": ["Nami", "Nico Robin", "Vivi", "Boa Hancock"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of Gol D. Roger's ship?", "opts": ["Moby Dick", "Oro Jackson", "Polar Tang", "Thriller Bark"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which Straw Hat is a skeleton musician?", "opts": ["Franky", "Brook", "Jinbe", "Usopp"], "ans": 1},

    {"cat": "Bleach", "diff": "Easy", "xp": 50, "q": "What is the name of Ichigo's Zanpakuto?", "opts": ["Zangetsu", "Benihime", "Hyorinmaru", "Sakanade"], "ans": 0},
    {"cat": "Bleach", "diff": "Medium", "xp": 100, "q": "Who is the captain of Squad 10?", "opts": ["Byakuya Kuchiki", "Toshiro Hitsugaya", "Kenpachi Zaraki", "Shunsui Kyoraku"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character is known as the Kenpachi?", "opts": ["Renji Abarai", "Kenpachi Zaraki", "Kisuke Urahara", "Gin Ichimaru"], "ans": 1},
    {"cat": "Bleach", "diff": "Medium", "xp": 100, "q": "What is the name of Rukia's Zanpakuto?", "opts": ["Senbonzakura", "Sode no Shirayuki", "Hyorinmaru", "Suzumushi"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who was the first captain of Squad 12?", "opts": ["Kisuke Urahara", "Mayuri Kurotsuchi", "Kirio Hikifune", "Shinji Hirako"], "ans": 2},
    {"cat": "Bleach", "diff": "Easy", "xp": 50, "q": "What is the name of Ichigo's younger sister?", "opts": ["Yuzu Kurosaki", "Orihime Inoue", "Rangiku Matsumoto", "Momo Hinamori"], "ans": 0},
    {"cat": "Bleach", "diff": "Medium", "xp": 100, "q": "Who is known as the God of Thunder in the Soul Society?", "opts": ["Soi Fon", "Yoruichi Shihouin", "Retsu Unohana", "Lisa Yadomaru"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of Aizen's Zanpakuto?", "opts": ["Kyoka Suigetsu", "Katen Kyokotsu", "Ryujin Jakka", "Suzumebachi"], "ans": 0},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which character was formerly the captain of Squad 5 before Aizen?", "opts": ["Shinji Hirako", "Jushiro Ukitake", "Sajin Komamura", "Kensei Muguruma"], "ans": 0},
    {"cat": "Bleach", "diff": "Easy", "xp": 50, "q": "What is the name of Ichigo's father?", "opts": ["Isshin Kurosaki", "Ryuken Ishida", "Genryusai Yamamoto", "Kugo Ginjo"], "ans": 0},

    {"cat": "Dragon Ball", "diff": "Easy", "xp": 50, "q": "What is Goku's Saiyan birth name?", "opts": ["Vegeta", "Kakarot", "Bardock", "Raditz"], "ans": 1},
    {"cat": "Dragon Ball", "diff": "Medium", "xp": 100, "q": "Who is Vegeta's father?", "opts": ["King Cold", "King Vegeta", "Bardock", "Nappa"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character is the God of Destruction of Universe 7?", "opts": ["Whis", "Beerus", "Zeno", "Champa"], "ans": 1},
    {"cat": "Dragon Ball", "diff": "Medium", "xp": 100, "q": "Who trained Gohan during the Saiyan Saga?", "opts": ["Master Roshi", "Piccolo", "King Kai", "Yamcha"], "ans": 1},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "What is the name of the fusion between Goku and Vegeta using the Potara earrings?", "opts": ["Gogeta", "Vegito", "Gotenks", "Kefla"], "ans": 1},
    {"cat": "Dragon Ball", "diff": "Easy", "xp": 50, "q": "How many Dragon Balls are traditionally needed to summon Shenron?", "opts": ["Five", "Six", "Seven", "Eight"], "ans": 2},
    {"cat": "Dragon Ball", "diff": "Medium", "xp": 100, "q": "Who is the angel attendant of Beerus?", "opts": ["Vados", "Whis", "Merus", "Marcarita"], "ans": 1},
    {"cat": "Dragon Ball", "diff": "Hard", "xp": 150, "q": "What is the name of the legendary Super Saiyan from Universe 6?", "opts": ["Caulifla", "Cabba", "Kale", "Hit"], "ans": 2},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which character is known as the Prince of all Saiyans?", "opts": ["Goku", "Broly", "Vegeta", "Trunks"], "ans": 2},
    {"cat": "Dragon Ball", "diff": "Easy", "xp": 50, "q": "What is the name of Goku's grandfather?", "opts": ["Bardock", "Grandpa Gohan", "King Kai", "Ox-King"], "ans": 1},

    {"cat": "Jujutsu Kaisen", "diff": "Easy", "xp": 50, "q": "What is the name of Yuji Itadori's school?", "opts": ["Kyoto Jujutsu High", "Tokyo Jujutsu High", "Tokyo Metropolitan High", "Shibuya Academy"], "ans": 1},
    {"cat": "Jujutsu Kaisen", "diff": "Medium", "xp": 100, "q": "Who is the King of Curses?", "opts": ["Mahito", "Jogo", "Ryomen Sukuna", "Kenjaku"], "ans": 2},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character uses the Cursed Speech technique?", "opts": ["Panda", "Toge Inumaki", "Yuta Okkotsu", "Kento Nanami"], "ans": 1},
    {"cat": "Jujutsu Kaisen", "diff": "Medium", "xp": 100, "q": "What is the name of Megumi's shikigami technique?", "opts": ["Cursed Spirit Manipulation", "Ten Shadows Technique", "Boogie Woogie", "Limitless"], "ans": 1},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "Who was the original owner of the body Kenjaku uses during much of the main story?", "opts": ["Suguru Geto", "Toji Fushiguro", "Yuta Okkotsu", "Kento Nanami"], "ans": 0},
    {"cat": "Jujutsu Kaisen", "diff": "Easy", "xp": 50, "q": "What is the name of Yuji's grandfather?", "opts": ["Wasuke Itadori", "Masamichi Yaga", "Yoshinobu Gakuganji", "Tengen"], "ans": 0},
    {"cat": "Jujutsu Kaisen", "diff": "Medium", "xp": 100, "q": "What is the name of Todo's cursed technique?", "opts": ["Ratio Technique", "Boogie Woogie", "Idle Transfiguration", "Straw Doll Technique"], "ans": 1},
    {"cat": "Jujutsu Kaisen", "diff": "Hard", "xp": 150, "q": "What is the name of Yuta Okkotsu's childhood friend and cursed spirit?", "opts": ["Rika Orimoto", "Maki Zenin", "Mai Zenin", "Yuki Tsukumo"], "ans": 0},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which sorcerer uses the Ratio Technique?", "opts": ["Aoi Todo", "Kento Nanami", "Mei Mei", "Noritoshi Kamo"], "ans": 1},
    {"cat": "Jujutsu Kaisen", "diff": "Easy", "xp": 50, "q": "What is the name of Gojo's school in Kyoto's rival campus?", "opts": ["Kyoto Jujutsu High", "Tokyo Jujutsu High", "Jujutsu Academy", "Kamo Academy"], "ans": 0},

    {"cat": "Demon Slayer", "diff": "Easy", "xp": 50, "q": "What is the name of Tanjiro's sister?", "opts": ["Kanao", "Nezuko", "Aoi", "Mitsuri"], "ans": 1},
    {"cat": "Demon Slayer", "diff": "Medium", "xp": 100, "q": "Who is the Flame Hashira?", "opts": ["Tengen Uzui", "Kyojuro Rengoku", "Sanemi Shinazugawa", "Muichiro Tokito"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character wears a boar mask?", "opts": ["Zenitsu Agatsuma", "Genya Shinazugawa", "Inosuke Hashibira", "Giyu Tomioka"], "ans": 2},
    {"cat": "Demon Slayer", "diff": "Medium", "xp": 100, "q": "Who is the leader of the Demon Slayer Corps?", "opts": ["Kagaya Ubuyashiki", "Muzan Kibutsuji", "Sakonji Urokodaki", "Shinjuro Rengoku"], "ans": 0},
    {"cat": "Demon Slayer", "diff": "Hard", "xp": 150, "q": "What is the name of the first demon to be turned by Muzan?", "opts": ["Akaza", "Kokushibo", "Tamayo", "The series does not explicitly identify the first demon"], "ans": 3},
    {"cat": "Demon Slayer", "diff": "Easy", "xp": 50, "q": "Which breathing style is associated with Zenitsu?", "opts": ["Water Breathing", "Thunder Breathing", "Wind Breathing", "Stone Breathing"], "ans": 1},
    {"cat": "Demon Slayer", "diff": "Medium", "xp": 100, "q": "What is the rank of the strongest demons serving Muzan?", "opts": ["Hashira", "Twelve Kizuki", "Kakushi", "Tsuguko"], "ans": 1},
    {"cat": "Demon Slayer", "diff": "Hard", "xp": 150, "q": "Which Upper Rank demon was formerly a human named Hakuji?", "opts": ["Doma", "Akaza", "Gyutaro", "Kokushibo"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which Hashira is known as the Mist Hashira?", "opts": ["Obanai Iguro", "Muichiro Tokito", "Mitsuri Kanroji", "Gyomei Himejima"], "ans": 1},
    {"cat": "Demon Slayer", "diff": "Easy", "xp": 50, "q": "What is the name of the demon who killed Tanjiro's family?", "opts": ["Akaza", "Muzan Kibutsuji", "Doma", "Enmu"], "ans": 1},

    {"cat": "Attack on Titan", "diff": "Easy", "xp": 50, "q": "What is the name of Eren's hometown?", "opts": ["Trost", "Shiganshina", "Stohess", "Mitras"], "ans": 1},
    {"cat": "Attack on Titan", "diff": "Medium", "xp": 100, "q": "Who is known as the Commander of the Survey Corps before Hange?", "opts": ["Levi Ackerman", "Erwin Smith", "Keith Shadis", "Dot Pixis"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character is Mikasa's childhood friend?", "opts": ["Jean Kirstein", "Eren Yeager", "Reiner Braun", "Armin Arlert"], "ans": 1},
    {"cat": "Attack on Titan", "diff": "Medium", "xp": 100, "q": "What is the name of the military branch responsible for exploring beyond the Walls?", "opts": ["Military Police", "Garrison Regiment", "Survey Corps", "Warrior Unit"], "ans": 2},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "Which Titan is also known as the Dancing Titan?", "opts": ["Jaw Titan", "Female Titan", "Attack Titan", "Cart Titan"], "ans": 0},
    {"cat": "Attack on Titan", "diff": "Easy", "xp": 50, "q": "What is the name of Armin's childhood friend?", "opts": ["Connie", "Eren", "Marco", "Reiner"], "ans": 1},
    {"cat": "Attack on Titan", "diff": "Medium", "xp": 100, "q": "Who inherited the Colossal Titan after Bertholdt?", "opts": ["Jean Kirstein", "Armin Arlert", "Connie Springer", "Floch Forster"], "ans": 1},
    {"cat": "Attack on Titan", "diff": "Hard", "xp": 150, "q": "What is the name of the royal family ruling inside the Walls?", "opts": ["Fritz", "Ackerman", "Braun", "Tybur"], "ans": 0},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which character is nicknamed Humanity's Strongest Soldier?", "opts": ["Erwin Smith", "Levi Ackerman", "Mikasa Ackerman", "Hange Zoe"], "ans": 1},
    {"cat": "Attack on Titan", "diff": "Easy", "xp": 50, "q": "What are the giant humanoid creatures called?", "opts": ["Hollows", "Titans", "Ghouls", "Nomus"], "ans": 1},

    {"cat": "Death Note", "diff": "Easy", "xp": 50, "q": "What is the name of the Shinigami who drops the Death Note?", "opts": ["Rem", "Ryuk", "Sidoh", "Gelus"], "ans": 1},
    {"cat": "Death Note", "diff": "Medium", "xp": 100, "q": "What is the real name of L?", "opts": ["Near", "Mello", "L Lawliet", "Teru Mikami"], "ans": 2},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character is known as the Second Kira?", "opts": ["Kiyomi Takada", "Misa Amane", "Naomi Misora", "Sayu Yagami"], "ans": 1},
    {"cat": "Death Note", "diff": "Medium", "xp": 100, "q": "What is the name of Light Yagami's father?", "opts": ["Soichiro Yagami", "Touta Matsuda", "Shuichi Aizawa", "Kanzo Mogi"], "ans": 0},
    {"cat": "Death Note", "diff": "Hard", "xp": 150, "q": "What is the name of the Shinigami who gives Misa the Death Note?", "opts": ["Ryuk", "Rem", "Sidoh", "Armonia Justin"], "ans": 1},
    {"cat": "Death Note", "diff": "Easy", "xp": 50, "q": "What does Light Yagami initially use the Death Note for?", "opts": ["Finding treasure", "Punishing criminals", "Saving Shinigami", "Becoming a detective"], "ans": 1},
    {"cat": "Death Note", "diff": "Medium", "xp": 100, "q": "Who is the successor to L at Wammy's House?", "opts": ["Matsuda", "Near", "Mello", "Matt"], "ans": 1},
    {"cat": "Death Note", "diff": "Hard", "xp": 150, "q": "What is the name of the orphanage associated with L, Near and Mello?", "opts": ["Grace Field House", "Wammy's House", "Sunrise Academy", "St. Marguerite"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which character is a professional detective and a member of the investigation team?", "opts": ["Teru Mikami", "Touta Matsuda", "Kiyomi Takada", "Misa Amane"], "ans": 1},
    {"cat": "Death Note", "diff": "Easy", "xp": 50, "q": "What is the name of Light's younger sister?", "opts": ["Misa", "Sayu", "Naomi", "Kiyomi"], "ans": 1},

    {"cat": "Hunter x Hunter", "diff": "Easy", "xp": 50, "q": "What is the name of Gon's father?", "opts": ["Silva Zoldyck", "Ging Freecss", "Isaac Netero", "Kite"], "ans": 1},
    {"cat": "Hunter x Hunter", "diff": "Medium", "xp": 100, "q": "Which family does Killua belong to?", "opts": ["Freecss", "Zoldyck", "Kurta", "Nostrade"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character is a doctor-in-training and one of Gon's closest friends?", "opts": ["Kurapika", "Leorio", "Knuckle", "Kite"], "ans": 1},
    {"cat": "Hunter x Hunter", "diff": "Medium", "xp": 100, "q": "What is the name of the leader of the Phantom Troupe?", "opts": ["Hisoka", "Chrollo Lucilfer", "Feitan", "Illumi"], "ans": 1},
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "What is the name of the Hunter Exam's examiner during Gon's first exam?", "opts": ["Satotz", "Buhara", "Menchi", "Basho"], "ans": 0},
    {"cat": "Hunter x Hunter", "diff": "Easy", "xp": 50, "q": "What is the name of the game Gon enters to find clues about his father?", "opts": ["Heaven's Arena", "Greed Island", "Yorknew City", "Dark Continent"], "ans": 1},
    {"cat": "Hunter x Hunter", "diff": "Medium", "xp": 100, "q": "Which Nen category does Kurapika use when his eyes turn scarlet?", "opts": ["Enhancer", "Specialist", "Emitter", "Transmuter"], "ans": 1},
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "What is the name of the chairman of the Hunter Association during the Chimera Ant arc?", "opts": ["Beyond Netero", "Isaac Netero", "Cheadle Yorkshire", "Pariston Hill"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which Phantom Troupe member uses a vacuum cleaner called Blinky?", "opts": ["Machi", "Shizuku", "Pakunoda", "Shalnark"], "ans": 1},
    {"cat": "Hunter x Hunter", "diff": "Easy", "xp": 50, "q": "What is the name of Killua's younger sister?", "opts": ["Alluka", "Mito", "Canary", "Palm"], "ans": 0},

    {"cat": "My Hero Academia", "diff": "Easy", "xp": 50, "q": "What is the name of the school Izuku Midoriya attends?", "opts": ["Shiketsu High", "U.A. High School", "Ketsubutsu Academy", "Seiai Academy"], "ans": 1},
    {"cat": "My Hero Academia", "diff": "Medium", "xp": 100, "q": "What is All Might's real name?", "opts": ["Shota Aizawa", "Toshinori Yagi", "Enji Todoroki", "Hizashi Yamada"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Easy", "xp": 50, "q": "Which character has the hero name Froppy?", "opts": ["Mina Ashido", "Tsuyu Asui", "Ochaco Uraraka", "Momo Yaoyorozu"], "ans": 1},
    {"cat": "My Hero Academia", "diff": "Medium", "xp": 100, "q": "What is the name of Shoto Todoroki's father?", "opts": ["Hawks", "Endeavor", "Best Jeanist", "Edgeshot"], "ans": 1},
    {"cat": "My Hero Academia", "diff": "Hard", "xp": 150, "q": "Which previous One For All user possessed the Gearshift quirk?", "opts": ["Second user", "Third user", "Fourth user", "Sixth user"], "ans": 0},
    {"cat": "My Hero Academia", "diff": "Easy", "xp": 50, "q": "What is the name of Bakugo's quirk?", "opts": ["Explosion", "Engine", "Hardening", "Dark Shadow"], "ans": 0},
    {"cat": "My Hero Academia", "diff": "Medium", "xp": 100, "q": "Who is the homeroom teacher of Class 1-A?", "opts": ["Present Mic", "Shota Aizawa", "All Might", "Cementoss"], "ans": 1},
    {"cat": "My Hero Academia", "diff": "Hard", "xp": 150, "q": "What is the name of the League of Villains' original leader?", "opts": ["Tomura Shigaraki", "All For One", "Dabi", "Kurogiri"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which character can create objects using her body fat?", "opts": ["Kyoka Jiro", "Momo Yaoyorozu", "Toru Hagakure", "Mina Ashido"], "ans": 1},
    {"cat": "My Hero Academia", "diff": "Easy", "xp": 50, "q": "What is the name of Deku's childhood friend and rival?", "opts": ["Eijiro Kirishima", "Katsuki Bakugo", "Tenya Iida", "Hitoshi Shinso"], "ans": 1},
        # ===== PART 2: QUESTIONS 101-200 =====

    # FAIRY TAIL

    {"cat": "Fairy Tail Lore", "diff": "Hard", "xp": 150, "q": "What is the original identity of Zeref's younger brother?", "opts": ["Natsu Dragneel", "Larcade Dragneel", "August", "E.N.D."], "ans": 0},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "Who created the Etherious demons of the Book of Zeref?", "opts": ["Mavis Vermillion", "Zeref Dragneel", "Acnologia", "Irene Belserion"], "ans": 1},
    {"cat": "Fairy Tail Lore", "diff": "Hard", "xp": 150, "q": "What is the name of Erza Scarlet's mother?", "opts": ["Mavis Vermillion", "Irene Belserion", "Dimaria Yesta", "Brandish Mu"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Hard", "xp": 150, "q": "Which character is known as the Black Wizard?", "opts": ["Acnologia", "Zeref Dragneel", "Jellal Fernandes", "Mard Geer"], "ans": 1},
    {"cat": "Fairy Tail Lore", "diff": "Medium", "xp": 100, "q": "What is the name of the celestial spirit associated with Lucy's zodiac sign?", "opts": ["Aquarius", "Cancer", "Virgo", "Sagittarius"], "ans": 0},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "Which Dragon Slayer was raised by the Sky Dragon Grandeeney?", "opts": ["Rogue Cheney", "Wendy Marvell", "Sting Eucliffe", "Gajeel Redfox"], "ans": 1},
    {"cat": "Fairy Tail Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient dragon who taught Natsu Fire Dragon Slayer Magic?", "opts": ["Metalicana", "Igneel", "Weisslogia", "Atlas Flame"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which Fairy Tail member uses Satan Soul Take Over magic?", "opts": ["Lisanna Strauss", "Mirajane Strauss", "Evergreen", "Cana Alberona"], "ans": 1},
    {"cat": "Fairy Tail Lore", "diff": "Hard", "xp": 150, "q": "Who was the first guild master of Fairy Tail?", "opts": ["Makarov Dreyar", "Precht Gaebolg", "Mavis Vermillion", "Yuri Dreyar"], "ans": 2},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "What is the name of Acnologia's original human identity profession?", "opts": ["Dragon Slayer", "Dragon King", "Dragon Priest", "Dragon Emperor"], "ans": 0},

    # BLACK CLOVER

    {"cat": "Black Clover Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the devil residing within Asta's grimoire?", "opts": ["Lucifero", "Liebe", "Zagred", "Megicula"], "ans": 1},
    {"cat": "Black Clover Lore", "diff": "Hard", "xp": 150, "q": "Who is the mother of Asta?", "opts": ["Acier Silva", "Licita", "Lolopechka", "Vanica"], "ans": 1},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "Which devil occupies the highest position in the Underworld's first layer?", "opts": ["Beelzebub", "Lucifero", "Megicula", "Adrammelech"], "ans": 1},
    {"cat": "Black Clover Lore", "diff": "Hard", "xp": 150, "q": "Who was the original owner of the five-leaf grimoire before Asta?", "opts": ["Julius Novachrono", "Licht", "Yuno", "Lemiel Silvamillion"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which character possesses Spatial Magic and is the vice-captain of the Black Bulls?", "opts": ["Zora Ideale", "Nacht Faust", "Finral Roulacase", "Gauche Adlai"], "ans": 1},
    {"cat": "Black Clover Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the first Wizard King?", "opts": ["Julius Novachrono", "Lemiel Silvamillion Clover", "Licht", "Lumiere Silva"], "ans": 1},
    {"cat": "Black Clover Lore", "diff": "Medium", "xp": 100, "q": "Which magic attribute does Nozel Silva possess?", "opts": ["Mercury Magic", "Steel Magic", "Water Magic", "Mist Magic"], "ans": 0},
    {"cat": "Power Scaling", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient elf leader who became the demon Licht?", "opts": ["Patolli", "Licht", "Rhya", "Vetto"], "ans": 1},
    {"cat": "Black Clover Lore", "diff": "Hard", "xp": 150, "q": "Who is the devil associated with the Qliphoth's second gate?", "opts": ["Lucifero", "Lilith", "Naamah", "Beelzebub"], "ans": 3},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which Black Bulls member uses spatial magic to transport people?", "opts": ["Magna Swing", "Finral Roulacase", "Luck Voltia", "Gordon Agrippa"], "ans": 1},

    # POKEMON

    {"cat": "Pokemon Lore", "diff": "Hard", "xp": 150, "q": "Which Pokémon is known as the Original One in Sinnoh mythology?", "opts": ["Dialga", "Palkia", "Arceus", "Giratina"], "ans": 2},
    {"cat": "Pokemon Lore", "diff": "Hard", "xp": 150, "q": "Which Pokémon created the legendary birds according to the Orange Islands anime storyline?", "opts": ["Lugia", "Ho-Oh", "Mewtwo", "Articuno"], "ans": 0},
    {"cat": "Guess the Character", "diff": "Hard", "xp": 150, "q": "Which Sinnoh Champion is famous for using Garchomp?", "opts": ["Steven Stone", "Cynthia", "Wallace", "Diantha"], "ans": 1},
    {"cat": "Pokemon Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the Pokémon that represents antimatter in Sinnoh mythology?", "opts": ["Dialga", "Palkia", "Giratina", "Uxie"], "ans": 2},
    {"cat": "Pokemon Knowledge", "diff": "Medium", "xp": 100, "q": "Which Pokémon evolves into Gyarados?", "opts": ["Feebas", "Magikarp", "Carvanha", "Goldeen"], "ans": 1},
    {"cat": "Pokemon Lore", "diff": "Hard", "xp": 150, "q": "Which Pokémon is associated with the concept of time?", "opts": ["Palkia", "Dialga", "Giratina", "Celebi"], "ans": 1},
    {"cat": "Pokemon Knowledge", "diff": "Medium", "xp": 100, "q": "What is the name of Ash's first Pokémon partner?", "opts": ["Charizard", "Pikachu", "Bulbasaur", "Squirtle"], "ans": 1},
    {"cat": "Pokemon Lore", "diff": "Hard", "xp": 150, "q": "Which Pokémon is known as the Aura Pokémon?", "opts": ["Lucario", "Riolu", "Absol", "Gallade"], "ans": 0},
    {"cat": "Pokemon Lore", "diff": "Hard", "xp": 150, "q": "Which legendary Pokémon represents the sea in the Hoenn weather trio?", "opts": ["Groudon", "Rayquaza", "Kyogre", "Regice"], "ans": 2},
    {"cat": "Pokemon Knowledge", "diff": "Medium", "xp": 100, "q": "Which Pokémon is the evolved form of Eevee using a Water Stone?", "opts": ["Jolteon", "Flareon", "Vaporeon", "Espeon"], "ans": 2},

    # FULLMETAL ALCHEMIST

    {"cat": "FMA Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the being who created the Homunculi?", "opts": ["Father", "Van Hohenheim", "Truth", "Dante"], "ans": 0},
    {"cat": "FMA Lore", "diff": "Hard", "xp": 150, "q": "Which Homunculus represents the sin of Envy?", "opts": ["Greed", "Envy", "Lust", "Pride"], "ans": 1},
    {"cat": "FMA Lore", "diff": "Medium", "xp": 100, "q": "What is the name of the country where Edward and Alphonse live?", "opts": ["Xing", "Amestris", "Drachma", "Creta"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which character is known as the Flame Alchemist?", "opts": ["Alex Louis Armstrong", "Roy Mustang", "Maes Hughes", "King Bradley"], "ans": 1},
    {"cat": "FMA Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the principle that governs alchemy?", "opts": ["Equivalent Exchange", "The Law of Conservation", "Alchemy Balance", "Truth's Contract"], "ans": 0},
    {"cat": "FMA Lore", "diff": "Hard", "xp": 150, "q": "Who is the father of Edward and Alphonse Elric?", "opts": ["Roy Mustang", "Van Hohenheim", "Scar", "King Bradley"], "ans": 1},
    {"cat": "FMA Lore", "diff": "Medium", "xp": 100, "q": "Which Homunculus disguises himself as King Bradley?", "opts": ["Wrath", "Pride", "Sloth", "Gluttony"], "ans": 0},
    {"cat": "FMA Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the mysterious gate encountered during human transmutation?", "opts": ["The Gate of Truth", "The Gate of Xerxes", "The Philosopher's Gate", "The Gate of Equivalent Exchange"], "ans": 0},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Who is Edward Elric's younger brother?", "opts": ["Ling Yao", "Alphonse Elric", "Selim Bradley", "Jean Havoc"], "ans": 1},
    {"cat": "FMA Lore", "diff": "Hard", "xp": 150, "q": "Which ancient civilization was destroyed in the creation of the nationwide transmutation circle?", "opts": ["Xing", "Ishval", "Xerxes", "Amestris"], "ans": 2},

    # TOKYO GHOUL

    {"cat": "Tokyo Ghoul Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the organization that investigates and hunts ghouls?", "opts": ["CCG", "Aogiri Tree", "Anteiku", "V"], "ans": 0},
    {"cat": "Tokyo Ghoul Lore", "diff": "Medium", "xp": 100, "q": "What is the name of Kaneki's kagune type?", "opts": ["Ukaku", "Koukaku", "Rinkaku", "Bikaku"], "ans": 2},
    {"cat": "Tokyo Ghoul Lore", "diff": "Hard", "xp": 150, "q": "Who performed the surgery that transformed Kaneki into a one-eyed ghoul?", "opts": ["Dr. Shiba", "Akihiro Kanou", "Kureo Mado", "Yoshimura"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which ghoul is known as the Gourmet?", "opts": ["Noro", "Shuu Tsukiyama", "Tatara", "Roma Hoito"], "ans": 1},
    {"cat": "Tokyo Ghoul Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the ghoul organization led by Eto Yoshimura?", "opts": ["Anteiku", "Aogiri Tree", "Clowns", "V"], "ans": 1},
    {"cat": "Tokyo Ghoul Lore", "diff": "Medium", "xp": 100, "q": "What is the name of the coffee shop where Kaneki first works?", "opts": ["Re:", "Anteiku", "HySy ArtMask Studio", "Helter Skelter"], "ans": 1},
    {"cat": "Tokyo Ghoul Lore", "diff": "Hard", "xp": 150, "q": "What is the identity of the One-Eyed Owl?", "opts": ["Eto Yoshimura", "Touka Kirishima", "Rize Kamishiro", "Nishiki Nishio"], "ans": 0},
    {"cat": "Tokyo Ghoul Lore", "diff": "Hard", "xp": 150, "q": "What is the name of Touka's younger brother?", "opts": ["Nishiki Nishio", "Ayato Kirishima", "Hideyoshi Nagachika", "Renji Yomo"], "ans": 1},
    {"cat": "Tokyo Ghoul Lore", "diff": "Medium", "xp": 100, "q": "Which investigator becomes known as the Reaper?", "opts": ["Kishou Arima", "Koutarou Amon", "Juuzou Suzuya", "Akira Mado"], "ans": 0},
    {"cat": "Tokyo Ghoul Lore", "diff": "Hard", "xp": 150, "q": "What is the name of Kaneki's childhood friend?", "opts": ["Hideyoshi Nagachika", "Nishiki Nishio", "Koutarou Amon", "Shuu Tsukiyama"], "ans": 0},

    # SWORD ART ONLINE

    {"cat": "SAO Lore", "diff": "Hard", "xp": 150, "q": "What is Kirito's player name in Sword Art Online?", "opts": ["Kirito", "Kazuto", "Black Swordsman", "The Flash"], "ans": 0},
    {"cat": "SAO Lore", "diff": "Medium", "xp": 100, "q": "What is the name of the guild Kirito briefly joins?", "opts": ["Knights of the Blood", "Moonlit Black Cats", "Laughing Coffin", "Aincrad Liberation Force"], "ans": 1},
    {"cat": "SAO Lore", "diff": "Hard", "xp": 150, "q": "Who created the original Sword Art Online game?", "opts": ["Kikuoka Seijirou", "Akihiko Kayaba", "Oberon", "Heathcliff"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which character is known as the Flash?", "opts": ["Sinon", "Asuna", "Lisbeth", "Silica"], "ans": 1},
    {"cat": "SAO Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the virtual world in the Alicization arc?", "opts": ["ALfheim Online", "Gun Gale Online", "Underworld", "Aincrad"], "ans": 2},
    {"cat": "SAO Lore", "diff": "Medium", "xp": 100, "q": "What is the name of Kirito's sister or cousin?", "opts": ["Suguha Kirigaya", "Shino Asada", "Yui", "Alice Zuberg"], "ans": 0},
    {"cat": "SAO Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the death game guild known for murdering players?", "opts": ["Moonlit Black Cats", "Laughing Coffin", "Sleeping Knights", "Divine Division"], "ans": 1},
    {"cat": "SAO Lore", "diff": "Medium", "xp": 100, "q": "Which game is primarily associated with Sinon?", "opts": ["Aincrad", "Gun Gale Online", "ALfheim Online", "Underworld"], "ans": 1},
    {"cat": "SAO Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the AI girl adopted by Kirito and Asuna?", "opts": ["Alice", "Yui", "Strea", "Argo"], "ans": 1},
    {"cat": "SAO Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the highest-ranking guild in Aincrad led by Heathcliff?", "opts": ["Moonlit Black Cats", "Knights of the Blood", "Laughing Coffin", "Aincrad Liberation Force"], "ans": 1},

    # JOJO'S BIZARRE ADVENTURE

    {"cat": "JoJo Lore", "diff": "Hard", "xp": 150, "q": "What is the name of Jonathan Joestar's Stand?", "opts": ["The World", "Hermit Purple", "Jonathan does not have a Stand in the original story", "Star Platinum"], "ans": 2},
    {"cat": "JoJo Lore", "diff": "Medium", "xp": 100, "q": "Who is the main antagonist of Stardust Crusaders?", "opts": ["Kars", "DIO", "Diavolo", "Enrico Pucci"], "ans": 1},
    {"cat": "JoJo Lore", "diff": "Hard", "xp": 150, "q": "What is the name of Jotaro Kujo's Stand?", "opts": ["Crazy Diamond", "Star Platinum", "Gold Experience", "King Crimson"], "ans": 1},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which character uses the Stand Killer Queen?", "opts": ["Yoshikage Kira", "Diavolo", "DIO", "Rohan Kishibe"], "ans": 0},
    {"cat": "JoJo Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the Pillar Man who seeks the Red Stone of Aja?", "opts": ["Wamuu", "Esidisi", "Kars", "Santana"], "ans": 2},
    {"cat": "JoJo Lore", "diff": "Medium", "xp": 100, "q": "Which JoJo is the protagonist of Golden Wind?", "opts": ["Jotaro Kujo", "Giorno Giovanna", "Josuke Higashikata", "Joseph Joestar"], "ans": 1},
    {"cat": "JoJo Lore", "diff": "Hard", "xp": 150, "q": "What is the name of Diavolo's Stand?", "opts": ["King Crimson", "Metallica", "The Grateful Dead", "Purple Haze"], "ans": 0},
    {"cat": "JoJo Lore", "diff": "Hard", "xp": 150, "q": "Which Stand is capable of stopping time?", "opts": ["Crazy Diamond", "The World", "Echoes", "Heaven's Door"], "ans": 1},
    {"cat": "JoJo Lore", "diff": "Medium", "xp": 100, "q": "What is the name of the Stand user who is also a manga artist?", "opts": ["Koichi Hirose", "Rohan Kishibe", "Okuyasu Nijimura", "Josuke Higashikata"], "ans": 1},
    {"cat": "JoJo Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the horse ridden by Johnny Joestar?", "opts": ["Slow Dancer", "Silver Bullet", "Poco Loco", "Hey Ya"], "ans": 0},

    # MOB PSYCHO 100 / ONE PUNCH MAN

    {"cat": "Mob Psycho Lore", "diff": "Hard", "xp": 150, "q": "What percentage does Mob reach when his emotions overflow?", "opts": ["50%", "75%", "100%", "120%"], "ans": 2},
    {"cat": "Mob Psycho Lore", "diff": "Medium", "xp": 100, "q": "What is the name of Mob's younger brother?", "opts": ["Ritsu Kageyama", "Teruki Hanazawa", "Shou Suzuki", "Tome Kurata"], "ans": 0},
    {"cat": "Mob Psycho Lore", "diff": "Hard", "xp": 150, "q": "What organization is led by Toichiro Suzuki?", "opts": ["Claw", "Black Vinegar Middle School", "Spirits and Such", "LOL"], "ans": 0},
    {"cat": "One Punch Man", "diff": "Medium", "xp": 100, "q": "What hero rank does Saitama initially receive?", "opts": ["S-Class", "A-Class", "C-Class", "B-Class"], "ans": 2},
    {"cat": "One Punch Man", "diff": "Hard", "xp": 150, "q": "What is the name of the martial arts tournament Garou's former master runs?", "opts": ["Super Fight", "Hero Hunt", "Monster Arena", "Martial Arts Festival"], "ans": 0},
    {"cat": "One Punch Man", "diff": "Hard", "xp": 150, "q": "What is the name of the alien leader who attacks Earth in the first season?", "opts": ["Boros", "Garou", "Orochi", "Psykos"], "ans": 0},
    {"cat": "Guess the Character", "diff": "Medium", "xp": 100, "q": "Which hero is known as the Silver Fang?", "opts": ["Atomic Samurai", "Bang", "Flashy Flash", "Child Emperor"], "ans": 1},
    {"cat": "One Punch Man", "diff": "Hard", "xp": 150, "q": "What is the name of the organization that creates artificial heroes and monsters?", "opts": ["Neo Heroes", "House of Evolution", "Hero Association", "Monster Association"], "ans": 1},
    {"cat": "One Punch Man", "diff": "Medium", "xp": 100, "q": "Which S-Class hero is a cyborg disciple of Bang?", "opts": ["Genos", "Metal Bat", "Drive Knight", "Puri-Puri Prisoner"], "ans": 0},
    {"cat": "Mob Psycho Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the spirit who possesses a broccoli-shaped divine tree?", "opts": ["Dimple", "Ekubo's rival", "Mogami", "Toichiro"], "ans": 0},
        # ===== PART 3: QUESTIONS 201-300 =====

    # ==================== ONE PIECE ====================

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What was the name of the ancient kingdom mentioned during the Void Century?", "opts": ["Great Kingdom", "Ancient Kingdom", "Lulusia Kingdom", "Holy Kingdom"], "ans": 1},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the giant robot that attacked Mary Geoise approximately 200 years ago?", "opts": ["Iron Giant", "Pluton", "Uranus", "Mother Flame"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Who was the previous user of the Ope Ope no Mi before Trafalgar Law?", "opts": ["Donquixote Rosinante", "Law's predecessor is not named", "Diez Barrels", "Vergo"], "ans": 1},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What was the name of the island where the Rocks Pirates were defeated?", "opts": ["God Valley", "Hachinosu", "Fullalead", "Beehive"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Who gave Shanks his famous straw hat originally?", "opts": ["Gol D. Roger", "Silvers Rayleigh", "Monkey D. Luffy", "Edward Newgate"], "ans": 0},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the sword carried by Kozuki Oden alongside Enma?", "opts": ["Shusui", "Ame no Habakiri", "Wado Ichimonji", "Sandai Kitetsu"], "ans": 1},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Which member of the Five Elders is associated with the title Warrior God of Finance?", "opts": ["Topman Warcury", "Ethanbaron V. Nusjuro", "Marcus Mars", "Shepherd Ju Peter"], "ans": 1},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient weapon hidden in Wano?", "opts": ["Uranus", "Poseidon", "Pluton", "Mother Flame"], "ans": 2},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Who was the first known person to be called Joy Boy in the story?", "opts": ["Gol D. Roger", "A figure from the Void Century", "Nika", "Imu"], "ans": 1},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the scientist who created the Pacifista project?", "opts": ["Caesar Clown", "Dr. Vegapunk", "Judge Vinsmoke", "Queen"], "ans": 1},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Which Road Poneglyph was located on Zou?", "opts": ["The one guarded by the Kozuki clan", "The one protected by the Mink Tribe", "The one hidden beneath Fish-Man Island", "The one owned by the Roger Pirates"], "ans": 1},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What was the name of the ship used by the Roger Pirates?", "opts": ["Oro Jackson", "Polar Tang", "Red Force", "Moby Dick"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Which of these characters was NOT a member of the Rocks Pirates?", "opts": ["Big Mom", "Kaido", "Shiki", "Silvers Rayleigh"], "ans": 3},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the sword wielded by Dracule Mihawk?", "opts": ["Yoru", "Kokuto", "Enma", "Murakumogiri"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Which island was destroyed by a mysterious weapon after Sabo's transmission?", "opts": ["Ohara", "Lulusia Kingdom", "God Valley", "Flevance"], "ans": 1},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the Mink who possesses the Sulong form and was a member of the Roger Pirates?", "opts": ["Carrot", "Pedro", "Inuarashi", "Nekomamushi"], "ans": 2},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Who was the first known user of the Gomu Gomu no Mi before Luffy?", "opts": ["Shanks", "The previous user is unknown", "Joy Boy", "Rocks D. Xebec"], "ans": 1},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which member of the Roger Pirates was known as the Dark King?", "opts": ["Scopper Gaban", "Silvers Rayleigh", "Kozuki Oden", "Douglas Bullet"], "ans": 1},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the special substance used to coat ships for travelling to Fish-Man Island?", "opts": ["Seastone", "Yoroi", "Yarukiman Mangrove resin", "Adam Wood"], "ans": 2},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient giant associated with the Iron Giant in Egghead's history?", "opts": ["Oars", "Emeth", "Zunesha", "Onimaru"], "ans": 1},

    # ==================== NARUTO ====================

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the first person to awaken the Rinnegan in the known history of the shinobi world?", "opts": ["Nagato", "Madara Uchiha", "Hagoromo Otsutsuki", "Sasuke Uchiha"], "ans": 2},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the Uchiha who helped Itachi during the Uchiha massacre?", "opts": ["Obito Uchiha", "Shisui Uchiha", "Madara Uchiha", "Fugaku Uchiha"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "What was the name of the forbidden technique used by Tobirama to revive the dead?", "opts": ["Izanagi", "Edo Tensei", "Rinne Tensei", "Kuchiyose: Reanimation"], "ans": 1},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "Which two chakra natures are combined to create Wood Release?", "opts": ["Water and Earth", "Earth and Fire", "Water and Wind", "Earth and Lightning"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the first jinchuriki of the Ten-Tails?", "opts": ["Madara Uchiha", "Obito Uchiha", "Hagoromo Otsutsuki", "Kaguya Otsutsuki"], "ans": 2},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the sword wielded by Orochimaru that emerged from the mouth of a snake?", "opts": ["Kusanagi", "Samehada", "Kubikiribocho", "Nuibari"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which member of Akatsuki was originally from the Hidden Waterfall Village?", "opts": ["Kisame Hoshigaki", "Kakuzu", "Hidan", "Deidara"], "ans": 1},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the clan that possessed the Shikotsumyaku kekkei genkai?", "opts": ["Kaguya Clan", "Aburame Clan", "Inuzuka Clan", "Yuki Clan"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the original owner of the Mangekyo Sharingan that Kakashi used?", "opts": ["Shisui Uchiha", "Obito Uchiha", "Madara Uchiha", "Izuna Uchiha"], "ans": 1},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the sword used by the Seven Ninja Swordsmen of the Mist that can absorb chakra?", "opts": ["Kabutowari", "Samehada", "Kiba", "Hiramekarei"], "ans": 1},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the first person to become the jinchuriki of the Nine-Tails?", "opts": ["Kushina Uzumaki", "Mito Uzumaki", "Naruto Uzumaki", "Rin Nohara"], "ans": 1},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "Which of the following techniques is associated with the Uzumaki clan's sealing arts?", "opts": ["Adamantine Sealing Chains", "Flying Thunder God", "Shadow Possession", "Particle Style"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the first reincarnation of Asura Otsutsuki shown in the series?", "opts": ["Hashirama Senju", "Naruto Uzumaki", "Madara Uchiha", "Indra Otsutsuki"], "ans": 0},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the Third Kazekage's unique kekkei genkai?", "opts": ["Magnet Release", "Lava Release", "Scorch Release", "Explosion Release"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which two brothers were known as the Gold and Silver Brothers?", "opts": ["Indra and Asura", "Kinkaku and Ginkaku", "Hashirama and Tobirama", "Fugaku and Madara"], "ans": 1},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the technique used by the Third Hokage to seal Orochimaru's arms?", "opts": ["Reaper Death Seal", "Dead Demon Consuming Seal", "Four Symbols Seal", "Eight Trigrams Seal"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which member of the Hyuga clan was the father of Neji?", "opts": ["Hiashi Hyuga", "Hizashi Hyuga", "Hanabi Hyuga", "Tokuma Hyuga"], "ans": 1},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the forbidden Uchiha technique that rewrites reality at the cost of an eye?", "opts": ["Izanagi", "Izanami", "Tsukuyomi", "Kotoamatsukami"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which tailed beast is known as the Four-Tails?", "opts": ["Son Goku", "Kokuo", "Saiken", "Chomei"], "ans": 0},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "Who was the leader of the Hidden Rain Village during the original Akatsuki's early formation?", "opts": ["Hanzo", "Nagato", "Yahiko", "Konan"], "ans": 0},

    # ==================== BLEACH ====================

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the original Gotei 13 founder and first Captain-Commander?", "opts": ["Shunsui Kyoraku", "Genryusai Shigekuni Yamamoto", "Jushiro Ukitake", "Chojiro Sasakibe"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What was the original name of the Soul King?", "opts": ["Reio", "Yhwach", "The Soul King's personal name is not revealed", "Ichibe Hyosube"], "ans": 2},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which Squad Zero member is known as the creator of the Zanpakuto?", "opts": ["Tenjiro Kirinji", "Oetsu Nimaiya", "Senjumaru Shutara", "Kirio Hikifune"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of Yhwach's Schrift?", "opts": ["The Almighty", "The Balance", "The Antithesis", "The Miracle"], "ans": 0},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the original owner of the Hogyoku created by Kisuke Urahara?", "opts": ["Sosuke Aizen", "Kisuke Urahara", "Mayuri Kurotsuchi", "Yoruichi Shihouin"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of Ichibe Hyosube's Zanpakuto?", "opts": ["Ichimonji", "Benihime", "Shirafude", "Katen Kyokotsu"], "ans": 0},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which Quincy was known as the B during the Thousand-Year Blood War?", "opts": ["Jugram Haschwalth", "Bazz-B", "Bambietta Basterbine", "Askin Nakk Le Vaar"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the first Espada in Aizen's army?", "opts": ["Coyote Starrk", "Baraggan Louisenbairn", "Tier Harribel", "Ulquiorra Cifer"], "ans": 0},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the original captain of Squad 11 before Kenpachi Zaraki?", "opts": ["Retsu Unohana", "Sajin Komamura", "Ikkaku Madarame", "Yachiru Kusajishi"], "ans": 0},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of Uryu Ishida's Schrift?", "opts": ["The Antithesis", "The Balance", "The Deathdealing", "The Fear"], "ans": 0},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which character is the founder of the Shinigami Research and Development Institute?", "opts": ["Kisuke Urahara", "Mayuri Kurotsuchi", "Oetsu Nimaiya", "Senjumaru Shutara"], "ans": 0},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Urahara to seal Aizen after his evolution?", "opts": ["Kido: Bakudo 99", "A special seal created by Urahara", "Hado 90: Kurohitsugi", "The Almighty"], "ans": 1},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which Squad Zero member is responsible for the Royal Guard's healing hot springs?", "opts": ["Oetsu Nimaiya", "Tenjiro Kirinji", "Ichibe Hyosube", "Kirio Hikifune"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the technique that allows Shunsui Kyoraku's Bankai to affect everyone around him?", "opts": ["Katen Kyokotsu: Karamatsu Shinju", "Kageoni", "Irooni", "Bushogoma"], "ans": 0},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the first person to become a Visored?", "opts": ["Shinji Hirako", "Hiyori Sarugaki", "Kensei Muguruma", "The series does not identify a single first Visored"], "ans": 3},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the Quincy technique that allows the user to gather Reishi from the environment?", "opts": ["Blut Vene", "Hirenkyaku", "Ransotengai", "Sklaverei"], "ans": 3},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which member of the Espada possesses the aspect of death known as solitude?", "opts": ["Ulquiorra Cifer", "Coyote Starrk", "Nnoitra Gilga", "Zommari Rureaux"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the Quincy king's elite personal guard?", "opts": ["Sternritter", "Schutzstaffel", "Wandenreich", "Letzt Stil"], "ans": 1},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which member of the Gotei 13 was responsible for creating the Gikon technology used to separate souls from bodies?", "opts": ["Kisuke Urahara", "Mayuri Kurotsuchi", "Kurotsuchi Nemu", "The technology's individual creator is not clearly established"], "ans": 3},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the original form of Ichigo's Zanpakuto revealed during the Thousand-Year Blood War?", "opts": ["Zangetsu", "Tensa Zangetsu", "Zangetsu and the Hollow power as his true Zanpakuto", "Engetsu"], "ans": 2},

    # ==================== BIG 3 CROSSOVER ====================

    {"cat": "Big 3: Extreme", "diff": "Hard", "xp": 150, "q": "Which of these characters was NOT trained by a member of the legendary Sannin?", "opts": ["Naruto Uzumaki", "Sasuke Uchiha", "Sakura Haruno", "Kakashi Hatake"], "ans": 3},

    {"cat": "Big 3: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which of these abilities is NOT a form of spiritual or supernatural power in its respective series?", "opts": ["Haki", "Chakra", "Reiatsu", "Nen"], "ans": 3},

    {"cat": "Big 3: Extreme", "diff": "Hard", "xp": 150, "q": "Which character has a canonical connection to the title 'World's Strongest Swordsman'?", "opts": ["Kisuke Urahara", "Dracule Mihawk", "Kakashi Hatake", "Byakuya Kuchiki"], "ans": 1},

    {"cat": "Big 3: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which series features a historical period called the Void Century?", "opts": ["Naruto", "Bleach", "One Piece", "All three"], "ans": 2},

    {"cat": "Big 3: Extreme", "diff": "Hard", "xp": 150, "q": "Which character is associated with the title 'God of Shinobi'?", "opts": ["Madara Uchiha", "Hashirama Senju", "Hagoromo Otsutsuki", "Hiruzen Sarutobi"], "ans": 1},

    {"cat": "Big 3: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which of these characters has a power that can manipulate the future?", "opts": ["Yhwach", "Madara Uchiha", "Kaido", "Aizen"], "ans": 0},

    {"cat": "Big 3: Extreme", "diff": "Hard", "xp": 150, "q": "Which character was responsible for training the main protagonist in the art of swordsmanship during a major timeskip?", "opts": ["Silvers Rayleigh", "Jiraiya", "Kisuke Urahara", "All three trained their respective protagonists in different ways"], "ans": 3},

    {"cat": "Big 3: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which of these characters has been a captain in their respective organization?", "opts": ["Roronoa Zoro", "Kakashi Hatake", "Byakuya Kuchiki", "Both B and C"], "ans": 3},

    {"cat": "Big 3: Extreme", "diff": "Hard", "xp": 150, "q": "Which of these characters was born into a clan with a famous inherited eye ability?", "opts": ["Sasuke Uchiha", "Nico Robin", "Ichigo Kurosaki", "All three"], "ans": 0},

    {"cat": "Big 3: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which organization is responsible for maintaining the balance of souls in Bleach?", "opts": ["Wandenreich", "Gotei 13", "Xcution", "Espada"], "ans": 1},

    # ==================== EXTRA EXTREME BIG 3 ====================

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the doctor who treated Nami during the Drum Island arc?", "opts": ["Dr. Hiriluk", "Dr. Kureha", "Dr. Hogback", "Dr. Vegapunk"], "ans": 1},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the island where the Roger Pirates discovered the final Poneglyph?", "opts": ["Zou", "Fish-Man Island", "Laugh Tale", "Skypiea"], "ans": 1},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the first known user of the Yami Yami no Mi?", "opts": ["Marshall D. Teach", "Thatch", "The previous user is unknown", "Edward Newgate"], "ans": 2},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the giant who guarded the gates of Enies Lobby?", "opts": ["Oimo", "Kashii", "Both Oimo and Kashii", "Hajrudin"], "ans": 2},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the forbidden technique used by Danzo to control Shisui's eye?", "opts": ["Kotoamatsukami", "Izanagi", "Izanami", "Tsukuyomi"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which Hokage created the Shadow Clone Technique?", "opts": ["Hashirama Senju", "Tobirama Senju", "Hiruzen Sarutobi", "Minato Namikaze"], "ans": 1},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the organization that Orochimaru founded to conduct experiments?", "opts": ["Root", "Sound Village", "Akatsuki", "Kara"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "Which character was the first known Substitute Soul Reaper before Ichigo?", "opts": ["Kugo Ginjo", "Kisuke Urahara", "Isshin Kurosaki", "The title's earlier history is not fully established"], "ans": 0},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Mayuri to control his modified body?", "opts": ["Konjiki Ashisogi Jizo", "Shikai", "Body modification techniques", "Kido"], "ans": 2},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "Which Quincy was known as the X, representing the X-Axis?", "opts": ["Lille Barro", "Gerard Valkyrie", "Pernida Parnkgjas", "Askin Nakk Le Vaar"], "ans": 0},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient weapon associated with Shirahoshi?", "opts": ["Pluton", "Uranus", "Poseidon", "Neptune"], "ans": 2},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "Which character was the original wielder of the Kusanagi sword Orochimaru used?", "opts": ["Sasuke Uchiha", "Orochimaru", "The sword's earlier owner is not established", "Itachi Uchiha"], "ans": 2},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which Sternritter represents the letter M?", "opts": ["Gerard Valkyrie", "Mask De Masculine", "Gremmy Thoumeaux", "Meninas McAllon"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Who was the former owner of the Mera Mera no Mi before Ace?", "opts": ["Sabo", "The previous user is unknown", "Portgas D. Rouge", "Monkey D. Dragon"], "ans": 1},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which of the following is the name of the Sage Mode used by Kabuto?", "opts": ["Toad Sage Mode", "Snake Sage Mode", "Slug Sage Mode", "Six Paths Sage Mode"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the ability used by Pernida Parnkgjas?", "opts": ["The Compulsory", "The Miracle", "The Deathdealing", "The Fear"], "ans": 0},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the special tree whose wood was used to build the Thousand Sunny?", "opts": ["Treasure Tree Adam", "Sunlight Tree Eve", "Yggdrasil", "Giant Tree of Elbaf"], "ans": 0},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "Who was the first known user of the Flying Thunder God Technique?", "opts": ["Minato Namikaze", "Tobirama Senju", "Hiruzen Sarutobi", "Kakashi Hatake"], "ans": 1},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which character's Bankai is named Kannonbiraki Benihime Aratame?", "opts": ["Kisuke Urahara", "Shunsui Kyoraku", "Retsu Unohana", "Shinji Hirako"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Which of the following is NOT one of the three ancient weapons?", "opts": ["Pluton", "Poseidon", "Uranus", "Mother Flame"], "ans": 3},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "What was the name of the clan that produced the first jinchuriki of the Nine-Tails?", "opts": ["Senju Clan", "Uzumaki Clan", "Uchiha Clan", "Hyuga Clan"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "Which character possesses the Schrift known as The Miracle?", "opts": ["Gerard Valkyrie", "Lille Barro", "Jugram Haschwalth", "Pernida Parnkgjas"], "ans": 0},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the giant elephant that carries the island of Zou?", "opts": ["Zunesha", "Oars", "Nika", "Emeth"], "ans": 0},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "Which character used the Reaper Death Seal to seal the Nine-Tails during its attack on Konoha?", "opts": ["Hiruzen Sarutobi", "Minato Namikaze", "Tobirama Senju", "Kushina Uzumaki"], "ans": 1},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Ulquiorra when he releases his second form?", "opts": ["Resurreccion: Murcielago", "Segunda Etapa", "Gran Rey Cero", "Lanza del Relampago"], "ans": 1},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient city associated with the Poneglyphs on Jaya?", "opts": ["Shandora", "Alubarna", "Birkan", "Ohara"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the original owner of the Seven Ninja Swordsmen's Kubikiribocho?", "opts": ["Zabuza Momochi", "Juzo Biwa", "Mangetsu Hozuki", "Kisame Hoshigaki"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the Quincy king's son in the Thousand-Year Blood War arc?", "opts": ["Jugram Haschwalth", "Uryu Ishida", "Bazz-B", "Yhwach has no confirmed biological son in the story"], "ans": 3},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which character was the first known user of the Bara Bara no Mi?", "opts": ["Buggy", "The previous user is unknown", "Shanks", "Crocodile"], "ans": 1},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the technique that allows the user to teleport through dimensions using Kamui?", "opts": ["Flying Thunder God", "Kamui", "Amenotejikara", "Yomotsu Hirasaka"], "ans": 1},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which Espada has the aspect of death known as nothingness?", "opts": ["Ulquiorra Cifer", "Coyote Starrk", "Nnoitra Gilga", "Szayelaporro Granz"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the ship that carried the Straw Hats through the Grand Line before the Thousand Sunny?", "opts": ["Going Merry", "Oro Jackson", "Red Force", "Polar Tang"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the first person to master the Eight Inner Gates?", "opts": ["Might Guy", "Might Duy", "Rock Lee", "Kakashi Hatake"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "Which member of Squad Zero is known as the Great Weave Guard?", "opts": ["Senjumaru Shutara", "Kirio Hikifune", "Oetsu Nimaiya", "Tenjiro Kirinji"], "ans": 0},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the former Warlord who was also the ruler of Alabasta?", "opts": ["Crocodile", "Nefertari Cobra", "Donquixote Doflamingo", "Gecko Moria"], "ans": 1},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "Which of these characters was NOT a member of the original Team Minato?", "opts": ["Kakashi Hatake", "Obito Uchiha", "Rin Nohara", "Might Guy"], "ans": 3},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Aizen to manipulate the five senses?", "opts": ["Kyoka Suigetsu", "Kurohitsugi", "Kanzen Saimin", "Sakanade"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "Which member of the Straw Hat crew has the epithet 'Soul King'?", "opts": ["Franky", "Brook", "Jinbe", "Usopp"], "ans": 1},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "What was the name of the Third Raikage's son?", "opts": ["A", "B", "C", "Darui"], "ans": 1},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "Which of these characters was NOT a member of the original Gotei 13 shown in the Thousand-Year Blood War arc?", "opts": ["Yamamoto", "Unohana", "Ukitake", "Kisuke Urahara"], "ans": 3},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which character is known as the King of the Underworld in One Piece?", "opts": ["Silvers Rayleigh", "Stussy", "Du Feld", "Morgans"], "ans": 0},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "Which tailed beast is sealed inside Han?", "opts": ["Five-Tails", "Six-Tails", "Four-Tails", "Seven-Tails"], "ans": 0},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which character is the original wielder of the sword Nozarashi?", "opts": ["Kenpachi Zaraki", "Retsu Unohana", "Yachiru Kusajishi", "Ikkaku Madarame"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the giant tree on Elbaf that is central to its mythology?", "opts": ["Treasure Tree Adam", "Sunlight Tree Eve", "Yggdrasil", "Shandora Tree"], "ans": 2},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which member of the Akatsuki was known as the Puppet Master?", "opts": ["Sasori", "Deidara", "Hidan", "Kakuzu"], "ans": 0},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the technique that Uryu uses to reverse the effects of an event between two points?", "opts": ["Antithesis", "Blut Vene", "Letzt Stil", "Hirenkyaku"], "ans": 0},

    {"cat": "One Piece: Deep Lore", "diff": "Hard", "xp": 150, "q": "Who was the first person to reach Laugh Tale alongside Gol D. Roger?", "opts": ["Silvers Rayleigh", "Scopper Gaban", "Kozuki Oden", "All surviving Roger Pirates present on the final voyage"], "ans": 3},

    {"cat": "Naruto: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Kaguya to shift between dimensions?", "opts": ["Amenominaka", "Kamui", "Amenotejikara", "Izanagi"], "ans": 0},

    {"cat": "Bleach: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which member of the Espada is known as the Octava Espada?", "opts": ["Szayelaporro Granz", "Aaroniero Arruruerie", "Zommari Rureaux", "Nnoitra Gilga"], "ans": 0},

    {"cat": "One Piece: Extreme", "diff": "Hard", "xp": 150, "q": "What was the name of the doctor who accompanied the Roger Pirates during their final voyage?", "opts": ["Crocus", "Dr. Hiriluk", "Dr. Kureha", "Dr. Vegapunk"], "ans": 0},

    {"cat": "Naruto: Deep Lore", "diff": "Hard", "xp": 150, "q": "Which character was the first known user of the Truth-Seeking Orbs in the series?", "opts": ["Hagoromo Otsutsuki", "Madara Uchiha", "Obito Uchiha", "Naruto Uzumaki"], "ans": 0},

    {"cat": "Bleach: Extreme", "diff": "Hard", "xp": 150, "q": "What is the name of the Schrift possessed by Jugram Haschwalth?", "opts": ["The Balance", "The Almighty", "The Antithesis", "The Miracle"], "ans": 0},
        # 301–325: One Piece
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the ship that carried the Roger Pirates to Laugh Tale?", "opts": ["Oro Jackson", "Thousand Sunny", "Red Force", "Moby Dick"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which member of the Roger Pirates was known as the Dark King?", "opts": ["Scopper Gaban", "Silvers Rayleigh", "Kozuki Oden", "Douglas Bullet"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient weapon hidden beneath Alabasta?", "opts": ["Uranus", "Poseidon", "Pluton", "Mother Flame"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the first known user of the Gomu Gomu no Mi before Luffy?", "opts": ["Shanks", "Gol D. Roger", "Joy Boy", "Its previous owner is unknown"], "ans": 3},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which island was the location of the Ohara incident?", "opts": ["West Blue", "North Blue", "South Blue", "East Blue"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the scientist who created the Pacifista?", "opts": ["Caesar Clown", "Dr. Vegapunk", "Queen", "Judge Vinsmoke"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Road Poneglyph was located on Zou?", "opts": ["The one held by Big Mom", "The one held by Kaido", "The one guarded by the Minks", "The one hidden in Fish-Man Island"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who gave Shanks his famous straw hat?", "opts": ["Gol D. Roger", "Silvers Rayleigh", "Whitebeard", "Gol D. Roger"], "ans": 3},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the giant elephant carrying Zou?", "opts": ["Zunesha", "Surume", "Laboon", "Nola"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the captain of the Rumbar Pirates?", "opts": ["Brook", "Yorki", "Crocus", "Calico Yorki"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which CP9 member ate the Neko Neko no Mi, Model: Leopard?", "opts": ["Kaku", "Blueno", "Rob Lucci", "Jabra"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the island where Ace and Luffy grew up?", "opts": ["Dawn Island", "Goa Island", "Foosha Island", "Mount Colubo"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was responsible for giving Luffy the scar beneath his left eye?", "opts": ["Ace", "Luffy himself", "Sabo", "Garp"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the giant skull-shaped island where Kaido established his base?", "opts": ["Punk Hazard", "Onigashima", "Whole Cake Island", "Hachinosu"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which member of the Five Elders is associated with the title Saint Jaygarcia Saturn?", "opts": ["Warrior God of Finance", "Warrior God of Justice", "Warrior God of Science and Defense", "Warrior God of Agriculture"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient kingdom's enemy, according to the history revealed through the Poneglyphs?", "opts": ["The Ancient Kingdom's name is unknown", "The World Government", "The Lunarians", "The Great Kingdom of Elbaf"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the original owner of the Yami Yami no Mi before Blackbeard?", "opts": ["Whitebeard", "Its previous owner is unknown", "Rocks D. Xebec", "Shiki"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which member of the Straw Hats was trained by Dracule Mihawk during the two-year timeskip?", "opts": ["Sanji", "Usopp", "Zoro", "Franky"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the ability that allows a person to hear the voices of all things?", "opts": ["Voice of All Things", "Mantra", "Observation Haki", "Conqueror's Haki"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the ruler of Dressrosa before Doflamingo took control?", "opts": ["Riku Doldo III", "Kyros", "King Elizabello II", "Donquixote Homing"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was revealed to be the mother of Jewelry Bonney?", "opts": ["Ginny", "Conney", "Lily", "Shakuyaku"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the giant robot discovered on Egghead?", "opts": ["Emeth", "General Franky", "Pluton", "Iron Giant Atlas"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which ancient weapon is associated with Shirahoshi?", "opts": ["Pluton", "Poseidon", "Uranus", "Mother Flame"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the first person to join Luffy's crew?", "opts": ["Nami", "Usopp", "Zoro", "Sanji"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the prison beneath Impel Down's Level 5?", "opts": ["Newkama Land", "Level 5.5", "Level 6", "Eternal Hell"], "ans": 1},

    # 326–350: Naruto
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first known human to awaken the Rinnegan?", "opts": ["Hagoromo Otsutsuki", "Madara Uchiha", "Sasuke Uchiha", "Indra Otsutsuki"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Minato use to teleport away from the Ten-Tails' Tailed Beast Bomb?", "opts": ["Flying Thunder God Technique", "Body Flicker Technique", "Kamui", "Reverse Summoning"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the original leader of Akatsuki before Yahiko's death?", "opts": ["Nagato", "Yahiko", "Konan", "Obito"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which of the following is NOT one of the Six Paths of Pain?", "opts": ["Deva Path", "Asura Path", "Sage Path", "Human Path"], "ans": 2},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the forbidden technique used by the Second Hokage to summon the dead?", "opts": ["Reaper Death Seal", "Edo Tensei", "Impure World Reincarnation", "Living Corpse Reincarnation"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first person to successfully use the Eight Gates against Madara during the Fourth Great Ninja War?", "opts": ["Might Guy", "Rock Lee", "Might Duy", "Kakashi Hatake"], "ans": 2},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Uchiha was responsible for killing the strongest member of the Uchiha clan's police force during the massacre?", "opts": ["Itachi", "Obito", "Shisui", "Sasuke"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the sword wielded by the Third Raikage?", "opts": ["Kiba", "Samehada", "No named sword was established", "Kusanagi"], "ans": 2},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which tailed beast was sealed inside Yagura Karatachi?", "opts": ["Three-Tails", "Four-Tails", "Six-Tails", "Two-Tails"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who created the Rasengan?", "opts": ["Jiraiya", "Minato Namikaze", "Kakashi Hatake", "Hagoromo Otsutsuki"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which clan possesses the Ketsuryugan?", "opts": ["Chinoike Clan", "Yuki Clan", "Kurama Clan", "Fuma Clan"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the sword used by Kisame Hoshigaki?", "opts": ["Kubikiribocho", "Samehada", "Kiba", "Hiramekarei"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first Jinchuriki of the Nine-Tails?", "opts": ["Mito Uzumaki", "Kushina Uzumaki", "Naruto Uzumaki", "Bunpuku"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Hokage created the Shadow Clone Technique?", "opts": ["First Hokage", "Second Hokage", "Third Hokage", "Fourth Hokage"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the organization that experimented on children using Hashirama's cells?", "opts": ["Root", "Akatsuki", "Kara", "The organization was not a separate group"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which two chakra natures are combined to create Wood Release?", "opts": ["Water and Earth", "Water and Wind", "Earth and Fire", "Earth and Lightning"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first person to possess the Mangekyo Sharingan?", "opts": ["Indra Otsutsuki", "Madara Uchiha", "Shisui Uchiha", "Fugaku Uchiha"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the name of the technique that allows Kakashi to send targets to another dimension?", "opts": ["Izanagi", "Kamui", "Kotoamatsukami", "Tsukuyomi"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which village did Haku originally come from?", "opts": ["Hidden Mist Village", "Hidden Rain Village", "Hidden Sound Village", "Hidden Cloud Village"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first person to become the Ten-Tails' Jinchuriki?", "opts": ["Hagoromo Otsutsuki", "Madara Uchiha", "Obito Uchiha", "Kaguya Otsutsuki"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which character was known as the Legendary Sannin's strongest medical ninja?", "opts": ["Shizune", "Tsunade", "Sakura Haruno", "Chiyo"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the name of the technique that seals a target inside a gourd?", "opts": ["Six Paths: Chibaku Tensei", "Sealing Tag", "Benihisago's sealing ability", "Reaper Death Seal"], "ans": 2},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Uchiha was the first to awaken the Eternal Mangekyo Sharingan?", "opts": ["Madara Uchiha", "Sasuke Uchiha", "Izuna Uchiha", "Obito Uchiha"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the technique used by the Third Hokage to seal Orochimaru's arms?", "opts": ["Dead Demon Consuming Seal", "Reaper Death Seal", "Four Symbols Seal", "Eight Trigrams Seal"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which of the following was NOT one of the original seven Ninja Swordsmen of the Mist?", "opts": ["Zabuza Momochi", "Kisame Hoshigaki", "Chojuro", "Mangetsu Hozuki"], "ans": 2},

    # 351–375: Bleach
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the original Gotei 13 captain commander?", "opts": ["Shunsui Kyoraku", "Genryusai Shigekuni Yamamoto", "Jushiro Ukitake", "Retsu Unohana"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Squad did Rukia Kuchiki originally belong to?", "opts": ["Squad 13", "Squad 6", "Squad 4", "Squad 2"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of Kenpachi Zaraki's Zanpakuto?", "opts": ["Nozarashi", "Hozukimaru", "Sakanade", "Tachikaze"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who was the first Kenpachi?", "opts": ["Kenpachi Zaraki", "Retsu Unohana", "Kiganjo", "Azashiro"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Sternritter possesses the Schrift 'The Almighty'?", "opts": ["Jugram Haschwalth", "Yhwach", "Gerard Valkyrie", "Pernida Parnkgjas"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of Urahara's Zanpakuto?", "opts": ["Benihime", "Katen Kyokotsu", "Suzumushi", "Enrakyoten"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Espada represents the aspect of death known as Sacrifice?", "opts": ["Starrk", "Barragan", "Ulquiorra", "Yammy"], "ans": 2},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the Royal Guard member who created the Zanpakuto?", "opts": ["Ichibe Hyosube", "Tenjiro Kirinji", "Oetsu Nimaiya", "Senjumaru Shutara"], "ans": 2},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which squad did Kisuke Urahara captain before becoming the Captain of Squad 12?", "opts": ["Squad 2", "Squad 5", "Squad 8", "He was not a captain before Squad 12"], "ans": 3},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who was the former captain of Squad 12 before Kisuke Urahara?", "opts": ["Mayuri Kurotsuchi", "Kirio Hikifune", "Retsu Unohana", "Shinji Hirako"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of Byakuya Kuchiki's Bankai?", "opts": ["Senbonzakura Kageyoshi", "Sakashima Yokoshima Happofusagari", "Kannonbiraki Benihime Aratame", "Hakka no Togame"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which character is the host of the Hollow known as White?", "opts": ["Renji Abarai", "Ichigo Kurosaki", "Uryu Ishida", "Isshin Kurosaki"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the Quincy technique that allows the user to absorb Reishi from the surroundings?", "opts": ["Blut Vene", "Ransotengai", "Sklaverei", "Hirenkyaku"], "ans": 2},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who killed the original members of the Gotei 13 during the first Quincy war?", "opts": ["Yhwach and his forces", "Aizen", "The Soul King", "The Zero Division"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Sternritter has the Schrift 'The Miracle'?", "opts": ["Lille Barro", "Askin Nakk Le Vaar", "Gerard Valkyrie", "Bazz-B"], "ans": 2},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of Shunsui Kyoraku's Bankai?", "opts": ["Karamatsu Shinju", "Katen Kyokotsu: Karamatsu Shinju", "Minazuki", "Tensa Zangetsu"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which member of the Espada was known as the Primera Espada?", "opts": ["Coyote Starrk", "Baraggan Louisenbairn", "Tier Harribel", "Ulquiorra Cifer"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Ichibe Hyosube to erase a target's name and power?", "opts": ["Futen Taisatsuryo", "Ichimonji", "Shirafude Ichimonji", "Senri Tsutensho"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who was the original owner of Zangetsu's Quincy form?", "opts": ["Yhwach", "Jugram Haschwalth", "Ryuken Ishida", "Soken Ishida"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which captain was responsible for developing the Gotei 13's research and development institute?", "opts": ["Kisuke Urahara", "Mayuri Kurotsuchi", "Shinji Hirako", "Sosuke Aizen"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the technique that allows a Soul Reaper to move at high speed?", "opts": ["Hirenkyaku", "Sonido", "Shunpo", "Bringer Light"], "ans": 2},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Espada was revealed to be the former ruler of Hueco Mundo?", "opts": ["Starrk", "Barragan", "Nnoitra", "Szayelaporro"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the technique that Aizen used to create perfect illusions?", "opts": ["Kyoka Suigetsu", "Kurohitsugi", "Hadō 90", "Sakanade"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Squad was led by Sajin Komamura?", "opts": ["Squad 7", "Squad 9", "Squad 10", "Squad 11"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who is the creator of the Hogyoku?", "opts": ["Sosuke Aizen", "Kisuke Urahara", "Both Urahara and Aizen independently created versions", "Mayuri Kurotsuchi"], "ans": 2},

    # 376–400: Other Anime
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "What is the name of the Nen ability used by Chrollo Lucilfer?", "opts": ["Skill Hunter", "Bungee Gum", "Gallery Fake", "Sun and Moon"], "ans": 0},
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "Which Nen category is considered the most suitable for creating objects?", "opts": ["Enhancement", "Conjuration", "Emission", "Manipulation"], "ans": 1},
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "What is the name of Meruem's Royal Guard who possesses the ability Doctor Blythe?", "opts": ["Shaiapouf", "Menthuthuyoupi", "Neferpitou", "Colt"], "ans": 2},
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "Who was the first chairman of the Hunter Association?", "opts": ["Isaac Netero", "Beyond Netero", "Cheadle Yorkshire", "Pariston Hill"], "ans": 0},
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "Which member of the Phantom Troupe uses a vacuum cleaner named Blinky?", "opts": ["Machi", "Shizuku", "Pakunoda", "Kortopi"], "ans": 1},
    {"cat": "Jujutsu Kaisen", "diff": "Hard", "xp": 150, "q": "What is the name of Sukuna's original domain expansion?", "opts": ["Malevolent Shrine", "Unlimited Void", "Chimera Shadow Garden", "Self-Embodiment of Perfection"], "ans": 0},
    {"cat": "Jujutsu Kaisen", "diff": "Hard", "xp": 150, "q": "Who was the first person to inherit the Ten Shadows Technique in the Zenin clan?", "opts": ["Megumi Fushiguro", "Toji Fushiguro", "The previous inheritor is not named", "Naobito Zenin"], "ans": 2},
    {"cat": "Jujutsu Kaisen", "diff": "Hard", "xp": 150, "q": "What is the name of Yuta Okkotsu's cursed technique?", "opts": ["Copy", "Cursed Speech", "Boogie Woogie", "Ratio Technique"], "ans": 0},
    {"cat": "Attack on Titan", "diff": "Hard", "xp": 150, "q": "Which Titan power did Grisha Yeager possess before inheriting the Founding Titan?", "opts": ["Armored Titan", "Attack Titan", "Beast Titan", "War Hammer Titan"], "ans": 1},
    {"cat": "Attack on Titan", "diff": "Hard", "xp": 150, "q": "What was the name of the first king of the Walls?", "opts": ["Karl Fritz", "Uri Reiss", "Rod Reiss", "Frieda Reiss"], "ans": 0},
    {"cat": "Demon Slayer", "diff": "Hard", "xp": 150, "q": "Who was the first known user of Sun Breathing?", "opts": ["Tanjiro Kamado", "Yoriichi Tsugikuni", "Michikatsu Tsugikuni", "Sumiyoshi"], "ans": 1},
    {"cat": "Demon Slayer", "diff": "Hard", "xp": 150, "q": "Which Upper Moon was formerly a human named Hakuji?", "opts": ["Doma", "Akaza", "Kokushibo", "Gyokko"], "ans": 1},
    {"cat": "Dragon Ball", "diff": "Hard", "xp": 150, "q": "Who was the first character to achieve Super Saiyan 2 in the main Dragon Ball Z storyline?", "opts": ["Goku", "Vegeta", "Gohan", "Trunks"], "ans": 2},
    {"cat": "Dragon Ball", "diff": "Hard", "xp": 150, "q": "What is the name of the Kaioshin who was sealed inside the Z Sword?", "opts": ["Elder Kai", "Supreme Kai", "Grand Supreme Kai", "Chronoa"], "ans": 0},
    {"cat": "Death Note", "diff": "Hard", "xp": 150, "q": "What is the name of the Shinigami who originally owned the Death Note used by Light?", "opts": ["Rem", "Ryuk", "Gelus", "Sidoh"], "ans": 1},
    {"cat": "Fullmetal Alchemist", "diff": "Hard", "xp": 150, "q": "Which Homunculus represents the sin of Pride in Fullmetal Alchemist: Brotherhood?", "opts": ["Envy", "Wrath", "Pride", "Greed"], "ans": 2},
    {"cat": "Black Clover", "diff": "Hard", "xp": 150, "q": "What is the name of the devil residing within Asta's grimoire?", "opts": ["Zagred", "Lucifero", "Liebe", "Megicula"], "ans": 2},
    {"cat": "Fairy Tail", "diff": "Hard", "xp": 150, "q": "Who is the founder of Fairy Tail guild?", "opts": ["Mavis Vermillion", "Precht Gaebolg", "Yuri Dreyar", "Warrod Sequen"], "ans": 0},
    {"cat": "My Hero Academia", "diff": "Hard", "xp": 150, "q": "Which previous holder of One For All was known for the Quirk Float?", "opts": ["Nana Shimura", "Daigoro Banjo", "En", "Hikage Shinomori"], "ans": 0},
    {"cat": "Tokyo Ghoul", "diff": "Hard", "xp": 150, "q": "What is the name of the kagune type used by Rize Kamishiro?", "opts": ["Ukaku", "Koukaku", "Rinkaku", "Bikaku"], "ans": 2},
    {"cat": "Code Geass", "diff": "Hard", "xp": 150, "q": "What is the name of Lelouch's Geass power?", "opts": ["Absolute Obedience", "Future Sight", "Mind Reading", "Memory Manipulation"], "ans": 0},
    {"cat": "Fullmetal Alchemist", "diff": "Hard", "xp": 150, "q": "What is the name of the gate that appears when someone attempts human transmutation?", "opts": ["Gate of Truth", "Gate of Alchemy", "Gate of Equivalent Exchange", "Gate of Xerxes"], "ans": 0},
    {"cat": "Black Clover", "diff": "Hard", "xp": 150, "q": "Which magic attribute does Yami Sukehiro possess?", "opts": ["Dark Magic", "Shadow Magic", "Gravity Magic", "Spatial Magic"], "ans": 0},
    {"cat": "Attack on Titan", "diff": "Hard", "xp": 150, "q": "What was the name of the Titan inherited by Lara Tybur?", "opts": ["Female Titan", "War Hammer Titan", "Cart Titan", "Jaw Titan"], "ans": 1},
    {"cat": "Demon Slayer", "diff": "Hard", "xp": 150, "q": "Which Hashira was known as the former Flame Hashira before Kyojuro Rengoku?", "opts": ["Shinjuro Rengoku", "Tengen Uzui", "Jigoro Kuwajima", "Sakonji Urokodaki"], "ans": 0},
        # 401–425: One Piece — Extreme
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the giant straw hat stored in Mary Geoise?", "opts": ["Joy Boy's straw hat", "Roger's straw hat", "Nika's straw hat", "Shanks' straw hat"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the first known person to possess the Voice of All Things in the Roger Pirates?", "opts": ["Rayleigh", "Roger", "Oden", "Shanks"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the island where the God Valley incident occurred?", "opts": ["Hachinosu", "Beehive Island", "God Valley", "Fullalead"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which member of the Rocks Pirates was known as the Silver Axe?", "opts": ["Shiki", "Captain John", "Wang Zhi", "His identity remains unrevealed"], "ans": 3},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the ancient robot's first known activation period?", "opts": ["200 years ago", "800 years ago", "900 years ago", "100 years ago"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Gorosei member bears the title Warrior God of Finance?", "opts": ["Topman Warcury", "Ethanbaron V. Nusjuro", "Shepherd Ju Peter", "Marcus Mars"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the ability used by the Five Elders to summon themselves to Egghead?", "opts": ["Room", "Black Vortex", "Summoning Circle", "Paw-Paw Teleportation"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the first person to discover the true identity of Luffy's Devil Fruit?", "opts": ["Shanks", "Rayleigh", "Gorosei", "The exact first person is not confirmed"], "ans": 3},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was responsible for giving Kuma his Buccaneer bloodline?", "opts": ["His father, Clapp", "His mother", "Saturn", "Ginny"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient kingdom's technology-powered robot on Egghead?", "opts": ["Pacifista", "Emeth", "Seraphim", "Mark III"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which member of the Blackbeard Pirates possesses the Riki Riki no Mi?", "opts": ["Van Augur", "Burgess", "Doc Q", "Shiryu"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the island where the Revolutionary Army has its headquarters after leaving Baltigo?", "opts": ["Momoiro Island", "Kamabakka Kingdom", "Lulusia", "Karakuri Island"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the first known user of the Paw-Paw Fruit?", "opts": ["Kuma", "Bonney", "Its previous user is unknown", "Ivankov"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was known as the Witching Hour Boy in Wano?", "opts": ["Denjiro", "Kawamatsu", "Shinobu", "Kawamatsu's alias was not Witching Hour Boy"], "ans": 3},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the ship belonging to the Whitebeard Pirates?", "opts": ["Moby Dick", "Oro Jackson", "Red Force", "Polar Tang"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which member of the Roger Pirates was the samurai from Wano?", "opts": ["Kin'emon", "Kozuki Oden", "Denjiro", "Ashura Doji"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the giant tree on Elbaf?", "opts": ["Eve", "Adam", "Yggdrasil", "Treasure Tree Adam"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which ancient weapon was used to destroy Lulusia Kingdom?", "opts": ["Pluton", "Poseidon", "Uranus", "The weapon's identity is not officially confirmed"], "ans": 3},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the ruler of the Kingdom of Kamabakka?", "opts": ["Emporio Ivankov", "Inazuma", "Belo Betty", "Dragon"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was revealed to have the Toshi Toshi no Mi?", "opts": ["Ginny", "Jewelry Bonney", "Shakuyaku", "Conney"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the previous ruler of the Sorbet Kingdom before Kuma?", "opts": ["King Bekori", "King Riku", "King Cobra", "King Elizabello"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character's epithet is 'The Tyrant'?", "opts": ["Bartholomew Kuma", "Donquixote Doflamingo", "Gecko Moria", "Kaido"], "ans": 0},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Zoro to cut steel during the Alabasta arc?", "opts": ["Ashura", "Shishi Sonson", "Tatsumaki", "Oni Giri"], "ans": 1},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was the first known user of the Bara Bara no Mi?", "opts": ["Buggy", "Shanks", "Its previous user is unknown", "Crocodile"], "ans": 2},
    {"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the ancient kingdom's enemy alliance during the Void Century?", "opts": ["The Ancient Kingdom", "The World Government", "The 20 Kingdoms", "The exact alliance name is unknown"], "ans": 3},

    # 426–450: Naruto — Extreme
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Hagoromo's elder son?", "opts": ["Indra", "Asura", "Hamura", "Toneri"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Tobirama develop to counter the Uchiha's Sharingan in combat?", "opts": ["Flying Thunder God", "Shadow Clone Technique", "Reanimation Technique", "Water Dragon Bullet"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first person to awaken the Rinne Sharingan?", "opts": ["Hagoromo", "Madara", "Kaguya", "Sasuke"], "ans": 2},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which of the following was NOT one of the original six paths of Pain?", "opts": ["Animal Path", "Preta Path", "Naraka Path", "Ashura Path"], "ans": 3},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the technique that allowed Obito to pass through attacks?", "opts": ["Kamui", "Izanagi", "Izanami", "Kotoamatsukami"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Uchiha was the first to awaken the Mangekyo Sharingan in the clan's recorded history?", "opts": ["Madara", "Indra", "Izuna", "Shisui"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the name of the forbidden technique used by Danzo to control an opponent's mind?", "opts": ["Izanagi", "Izanami", "Kotoamatsukami", "Tsukuyomi"], "ans": 2},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first person to use the Six Paths: Chibaku Tensei sealing technique on Kaguya?", "opts": ["Naruto alone", "Sasuke alone", "Hagoromo and Hamura", "Naruto and Sasuke together"], "ans": 3},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which of the following is the name of the Third Kazekage's special ability?", "opts": ["Iron Sand", "Gold Dust", "Magnet Release: Gold Sand", "Sand Manipulation"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first jinchuriki of the Ten-Tails?", "opts": ["Madara", "Hagoromo", "Obito", "Naruto"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which clan did Kimimaro belong to?", "opts": ["Kaguya Clan", "Hozuki Clan", "Yuki Clan", "Fuma Clan"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the sword wielded by the Second Mizukage's summoned clam?", "opts": ["Samehada", "No sword; it used genjutsu", "Kubikiribocho", "Kiba"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which character possessed the ability to use the Shikotsumyaku kekkei genkai?", "opts": ["Haku", "Kimimaro", "Suigetsu", "Jugo"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the sealing technique used by Minato to split Kurama's chakra?", "opts": ["Eight Trigrams Seal", "Four Symbols Seal", "Dead Demon Consuming Seal", "Five Elements Seal"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which of the following was the name of the Fourth Raikage?", "opts": ["A", "Darui", "Killer B", "C"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first person to possess the Six Paths Senjutsu?", "opts": ["Hagoromo", "Naruto", "Madara", "Obito"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Itachi use to trap Kabuto in an endless loop?", "opts": ["Tsukuyomi", "Izanami", "Kotoamatsukami", "Amaterasu"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which character was the first to become the host of the Three-Tails after its revival?", "opts": ["Rin Nohara", "Yagura", "Isobu's host was not identified before Rin", "Kushina"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by the Second Hokage to create water from nothing?", "opts": ["Water Dragon Bullet", "Water Severing Wave", "Water Formation Wall", "Water Release: Water Formation Pillar"], "ans": 1},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which two chakra natures are combined to create Lava Release?", "opts": ["Fire and Earth", "Fire and Wind", "Earth and Water", "Water and Lightning"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the forbidden technique used by Orochimaru to transfer his consciousness into another body?", "opts": ["Living Corpse Reincarnation", "Edo Tensei", "Reaper Death Seal", "Eight Branches Technique"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which character was the original owner of the Kusanagi sword used by Orochimaru?", "opts": ["Orochimaru", "Sasuke", "The sword's original owner is unknown", "Itachi"], "ans": 2},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which of the following was NOT a member of the original Team Minato?", "opts": ["Obito", "Rin", "Kakashi", "Might Guy"], "ans": 3},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first person to master the Eight Gates?", "opts": ["Might Duy", "Might Guy", "Rock Lee", "Kakashi"], "ans": 0},
    {"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Otsutsuki was responsible for creating the Chakra Fruit on Earth?", "opts": ["Kaguya", "Hagoromo", "Momoshiki", "Isshiki"], "ans": 0},

    # 451–475: Bleach — Extreme
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What was the original name of the Soul King?", "opts": ["Reio", "His personal name is never revealed", "Yhwach", "Ichibe Hyosube"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who was the first person to become a Soul Reaper?", "opts": ["Ichigo", "Yamamoto", "The original first Soul Reaper is not established", "Ichibe"], "ans": 2},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Squad did Retsu Unohana originally captain?", "opts": ["Squad 4", "Squad 11", "Squad 2", "Squad 1"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What was the name of the original Gotei 13's most notorious criminal?", "opts": ["Unohana", "Yamamoto", "Kyoraku", "Ukitake"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which member of Squad Zero possesses the ability to manipulate the color black?", "opts": ["Oetsu Nimaiya", "Ichibe Hyosube", "Tenjiro Kirinji", "Senjumaru Shutara"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the Schrift possessed by Askin Nakk Le Vaar?", "opts": ["The Deathdealing", "The Balance", "The Miracle", "The Fear"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who was the first character to use Bankai in the Bleach manga?", "opts": ["Ichigo", "Byakuya", "Renji", "Yamamoto"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Espada had the aspect of death 'Emptiness'?", "opts": ["Starrk", "Ulquiorra", "Nnoitra", "Barragan"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the technique that allows Uryu Ishida to reverse events between two points?", "opts": ["Antithesis", "Sklaverei", "Blut Vene", "Ransotengai"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Sternritter possesses the Schrift 'The X-Axis'?", "opts": ["Gerard Valkyrie", "Lille Barro", "Askin Nakk Le Vaar", "Bazz-B"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the Royal Guard member who created the Oken?", "opts": ["Ichibe Hyosube", "Oetsu Nimaiya", "Senjumaru Shutara", "Tenjiro Kirinji"], "ans": 2},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which character was revealed to be the original wielder of the Kenpachi title?", "opts": ["Retsu Unohana", "Yachiru Kusajishi", "Kenpachi Zaraki", "Kiganjo"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Yamamoto's Bankai to summon the dead?", "opts": ["Zanka no Tachi: East", "Zanka no Tachi: West", "Zanka no Tachi: North", "Zanka no Tachi: South"], "ans": 3},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which character's Bankai is called Kannonbiraki Benihime Aratame?", "opts": ["Kisuke Urahara", "Shinji Hirako", "Mayuri Kurotsuchi", "Rojuro Otoribashi"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which member of the Espada was known as the Segunda Espada?", "opts": ["Coyote Starrk", "Baraggan Louisenbairn", "Tier Harribel", "Ulquiorra Cifer"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Ichibe to rename an object?", "opts": ["Shirafude Ichimonji", "Ichimonji", "Futen Taisatsuryo", "Senri Tsutensho"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who was the first person to wield the Zanpakuto Zangetsu?", "opts": ["Ichigo", "Isshin", "The original wielder is not established", "Yhwach"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Squad was formerly led by Gin Ichimaru?", "opts": ["Squad 3", "Squad 5", "Squad 9", "Squad 10"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which Sternritter was known as 'The Fear'?", "opts": ["Bambietta Basterbine", "As Nodt", "Mask De Masculine", "Pernida Parnkgjas"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What is the name of the technique used by Mayuri to alter his Bankai?", "opts": ["Konjiki Ashisogi Jizo: Matai Fukuin Shotai", "Hakka no Togame", "Kannonbiraki Benihime Aratame", "Shatatsu Karagara Shigarami no Tsuji"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Who was the first Quincy to receive a Schrift from Yhwach?", "opts": ["Jugram Haschwalth", "Lille Barro", "The exact first recipient is not established", "Bazz-B"], "ans": 2},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which character was responsible for creating the Visored?", "opts": ["Kisuke Urahara", "Sosuke Aizen", "Shinji Hirako", "Hiyori Sarugaki"], "ans": 1},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "What was the name of the first Hollow to evolve into a Vasto Lorde shown in the series?", "opts": ["Starrk", "Ulquiorra", "Grimmjow", "The first shown is not definitively established"], "ans": 3},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which character's Zanpakuto is named Sogyo no Kotowari?", "opts": ["Jushiro Ukitake", "Shunsui Kyoraku", "Retsu Unohana", "Sajin Komamura"], "ans": 0},
    {"cat": "Bleach", "diff": "Hard", "xp": 150, "q": "Which member of the Royal Guard is known as the Great Weave Guard?", "opts": ["Tenjiro Kirinji", "Senjumaru Shutara", "Oetsu Nimaiya", "Ichibe Hyosube"], "ans": 1},

    # 476–500: Other Anime — Extreme
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "What is the name of the Nen ability used by Knov to create portals?", "opts": ["Hide and Seek", "Scream", "Black Voice", "Deep Purple"], "ans": 0},
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "Which Phantom Troupe member has the Nen ability Sun and Moon?", "opts": ["Feitan", "Chrollo", "Shalnark", "Franklin"], "ans": 1},
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "What is the name of the Chimera Ant King?", "opts": ["Neferpitou", "Shaiapouf", "Meruem", "Menthuthuyoupi"], "ans": 2},
    {"cat": "Hunter x Hunter", "diff": "Hard", "xp": 150, "q": "Which character used the ability Crazy Slots?", "opts": ["Ging", "Kite", "Knuckle", "Morel"], "ans": 1},
    {"cat": "Jujutsu Kaisen", "diff": "Hard", "xp": 150, "q": "What is the name of Kenjaku's original cursed technique?", "opts": ["Body hopping through brain transplantation", "Cursed Spirit Manipulation", "Idle Transfiguration", "Ten Shadows"], "ans": 0},
    {"cat": "Jujutsu Kaisen", "diff": "Hard", "xp": 150, "q": "Which cursed technique belongs to Takako Uro?", "opts": ["Sky Manipulation", "Projection Sorcery", "Star Rage", "Cursed Speech"], "ans": 0},
    {"cat": "Jujutsu Kaisen", "diff": "Hard", "xp": 150, "q": "What was the name of the shikigami that Megumi summoned as his final trump card?", "opts": ["Mahoraga", "Agito", "Nue", "Divine Dogs"], "ans": 0},
    {"cat": "Attack on Titan", "diff": "Hard", "xp": 150, "q": "Which Titan power was held by the Tybur family for generations?", "opts": ["War Hammer Titan", "Attack Titan", "Beast Titan", "Cart Titan"], "ans": 0},
    {"cat": "Attack on Titan", "diff": "Hard", "xp": 150, "q": "What was the name of the first person to inherit the Attack Titan?", "opts": ["Eren Kruger", "The first holder's identity is unknown", "Grisha Yeager", "Eren Yeager"], "ans": 1},
    {"cat": "Demon Slayer", "diff": "Hard", "xp": 150, "q": "Which Upper Moon was responsible for killing Kanae Kocho?", "opts": ["Doma", "Akaza", "Kokushibo", "Gyutaro"], "ans": 0},
    {"cat": "Demon Slayer", "diff": "Hard", "xp": 150, "q": "What was the name of the first Breath of the Sun user?", "opts": ["Yoriichi Tsugikuni", "Sumiyoshi", "Tanjiro Kamado", "Michikatsu Tsugikuni"], "ans": 0},
    {"cat": "Dragon Ball", "diff": "Hard", "xp": 150, "q": "What is the name of the Kai who trained Goku in the Other World?", "opts": ["King Kai", "Supreme Kai", "Elder Kai", "Grand Kai"], "ans": 0},
    {"cat": "Dragon Ball", "diff": "Hard", "xp": 150, "q": "Which angel is assigned to Universe 7?", "opts": ["Vados", "Whis", "Marcarita", "Korn"], "ans": 1},
    {"cat": "Fullmetal Alchemist", "diff": "Hard", "xp": 150, "q": "What was the name of the country where the Xerxes civilization once existed?", "opts": ["Amestris", "Xerxes", "Drachma", "Creta"], "ans": 1},
    {"cat": "Black Clover", "diff": "Hard", "xp": 150, "q": "Which devil possesses the highest-ranking position among the Qliphoth devils?", "opts": ["Lucifero", "Zagred", "Megicula", "Liebe"], "ans": 0},
    {"cat": "Code Geass", "diff": "Hard", "xp": 150, "q": "What is the name of C.C.'s original Geass contract partner?", "opts": ["Lelouch", "Charles zi Britannia", "A young nun", "Marianne"], "ans": 2},
    {"cat": "Death Note", "diff": "Hard", "xp": 150, "q": "What is the name of the Shinigami who gave Misa her Death Note?", "opts": ["Ryuk", "Rem", "Gelus", "Sidoh"], "ans": 1},
    {"cat": "Tokyo Ghoul", "diff": "Hard", "xp": 150, "q": "Which investigator was known as the CCG's Reaper?", "opts": ["Kishou Arima", "Koutarou Amon", "Juuzou Suzuya", "Kureo Mado"], "ans": 0},
    {"cat": "My Hero Academia", "diff": "Hard", "xp": 150, "q": "What was the original Quirk of the first One For All holder?", "opts": ["Stockpiling", "Transference", "A Quirk that allowed him to pass on his power", "He originally had no Quirk"]
], "ans": 3},
    {"cat": "Fairy Tail", "diff": "Hard", "xp": 150, "q": "What was the name of the first master of Fairy Tail?", "opts": ["Mavis Vermillion", "Precht Gaebolg", "Makarov Dreyar", "Hades"], "ans": 0},
    {"cat": "Vinland Saga", "diff": "Hard", "xp": 150, "q": "What was the name of Thorfinn's father?", "opts": ["Thors", "Thorkell", "Askeladd", "Leif Erikson"], "ans": 0},
    {"cat": "Mob Psycho 100", "diff": "Hard", "xp": 150, "q": "What is the name of the spirit that possesses Mob's younger brother?", "opts": ["Dimple", "Toichiro Suzuki", "Ekubo", "No spirit permanently possesses Ritsu"], "ans": 3},
    {"cat": "JoJo's Bizarre Adventure", "diff": "Hard", "xp": 150, "q": "What is the name of Yoshikage Kira's Stand?", "opts": ["Killer Queen", "King Crimson", "The World", "Crazy Diamond"], "ans": 0},
    {"cat": "Chainsaw Man", "diff": "Hard", "xp": 150, "q": "Which devil is fused with Denji?", "opts": ["Blood Devil", "Chainsaw Devil", "Control Devil", "Gun Devil"], "ans": 1},
    {"cat": "Solo Leveling", "diff": "Hard", "xp": 150, "q": "What is the name of the first shadow soldier Sung Jinwoo obtains?", "opts": ["Igris", "Tank", "Iron", "Kaisel"], "ans": 0},

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
    
