import asyncio
import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatType
from database import ensure_user, record_progression

router = Router()

QUIZ_LOBBIES: dict[int, dict] = {}
ACTIVE_QUIZZES: dict[int, dict] = {}

# Comprehensive Anime Quiz Question Bank with Category Tags
QUESTION_BANK = [
    # Naruto
    {"q": "What is the name of Naruto's signature jutsu learned from Jiraiya?", "options": ["Chidori", "Rasengan", "Shadow Clone", "Fire Ball"], "ans": 1, "cat": "naruto", "diff": "Easy"},
    {"q": "Which clan is Sasuke Uchiha a proud survivor of?", "options": ["Hyuga Clan", "Uchiha Clan", "Senju Clan", "Uzumaki Clan"], "ans": 1, "cat": "naruto", "diff": "Easy"},
    {"q": "Who is the leader of Akatsuki working from the shadows for most of Shippuden?", "options": ["Pain", "Obito / Madara", "Orochimaru", "Black Zetsu"], "ans": 1, "cat": "naruto", "diff": "Medium"},
    {"q": "What tailed beast is sealed inside Naruto Uzumaki?", "options": ["One-Tail Shukaku", "Nine-Tails Kurama", "Eight-Tails Gyuki", "Three-Tails Isobu"], "ans": 1, "cat": "naruto", "diff": "Easy"},
    {"q": "What is Kakashi Hatake's famous nickname in the ninja world?", "options": ["The Yellow Flash", "Copy Ninja Kakashi", "Noble Beast", "White Fang"], "ans": 1, "cat": "naruto", "diff": "Easy"},
    # NARUTO — FRESH QUESTION BANK (100 QUESTIONS)

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first person to awaken the Mangekyo Sharingan in the Uchiha clan's recorded history?", "opts": ["Indra Otsutsuki", "Madara Uchiha", "Izuna Uchiha", "Tajima Uchiha"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Madara Uchiha's younger brother?", "opts": ["Tajima", "Izuna", "Fugaku", "Shisui"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which eyes did Madara transplant into himself to obtain the Eternal Mangekyo Sharingan?", "opts": ["Obito's eyes", "Shisui's eyes", "Izuna's eyes", "Fugaku's eyes"], "ans": 2},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the Uchiha who possessed the Kotoamatsukami technique?", "opts": ["Shisui Uchiha", "Itachi Uchiha", "Fugaku Uchiha", "Izuna Uchiha"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who gave Danzo the right eye of Shisui Uchiha?", "opts": ["Itachi", "Orochimaru", "Danzo stole it himself", "Hiruzen"], "ans": 2},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Mangekyo Sharingan ability allowed Obito to transport himself and others to another dimension?", "opts": ["Amaterasu", "Kamui", "Tsukuyomi", "Kotoamatsukami"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which eye of Obito possessed the long-range version of Kamui?", "opts": ["Right eye", "Left eye", "Both eyes had identical ranges", "Neither eye"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which eye of Obito allowed him to make physical contact with objects while using Kamui?", "opts": ["Left eye", "Right eye", "Both eyes", "Neither eye"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was Itachi's Susanoo equipped with that made it exceptionally difficult to defeat?", "opts": ["Kusanagi and Samehada", "Totsuka Blade and Yata Mirror", "Kusanagi and Yata Mirror", "Totsuka Blade and Gunbai"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Sasuke's black-flame manipulation technique?", "opts": ["Kagutsuchi", "Amaterasu", "Susanoo", "Izanagi"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique allows an Uchiha to rewrite reality at the cost of one Sharingan eye?", "opts": ["Izanami", "Izanagi", "Kotoamatsukami", "Tsukuyomi"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique was created to counter the misuse of Izanagi?", "opts": ["Izanami", "Kamui", "Kotoamatsukami", "Tsukuyomi"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who trapped Kabuto inside the Izanami loop?", "opts": ["Sasuke", "Itachi", "Naruto", "Madara"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the Uchiha police force's headquarters in Konoha?", "opts": ["Naka Shrine", "Police Headquarters", "Hokage Residence", "Academy Hall"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Uchiha clan member was known as the 'Shisui of the Body Flicker'?", "opts": ["Itachi", "Shisui", "Madara", "Obito"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first person to awaken the Rinnegan in the known history of the shinobi world?", "opts": ["Madara Uchiha", "Hagoromo Otsutsuki", "Indra Otsutsuki", "Nagato"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "How did Madara awaken his Rinnegan?", "opts": ["By combining Hashirama's chakra with his own", "By receiving it from Hagoromo directly", "By absorbing the Ten-Tails", "By transplanting Nagato's eyes"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who originally possessed the Rinnegan that Nagato used?", "opts": ["Obito", "Madara", "Hagoromo", "Black Zetsu"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which of the Six Paths techniques allows the user to absorb chakra and ninjutsu?", "opts": ["Deva Path", "Preta Path", "Asura Path", "Animal Path"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Rinnegan path allows the user to summon the King of Hell?", "opts": ["Human Path", "Naraka Path", "Animal Path", "Preta Path"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Nagato use to revive the people killed during his attack on Konoha?", "opts": ["Chibaku Tensei", "Rinne Rebirth", "Summoning: Impure World Reincarnation", "Creation Rebirth"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the name of the technique that creates a miniature gravitational singularity to trap an opponent?", "opts": ["Shinra Tensei", "Chibaku Tensei", "Bansho Tenin", "Tengai Shinsei"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which character used the technique called Limbo: Border Jail?", "opts": ["Obito", "Madara", "Nagato", "Sasuke"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "How many Limbo shadows could Madara create after obtaining the Six Paths power?", "opts": ["One", "Two", "Four", "Six"], "ans": 2},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Rinnegan ability did Sasuke use to exchange places with objects and people?", "opts": ["Amenotejikara", "Limbo", "Bansho Tenin", "Shinra Tensei"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the name of Sasuke's space-time technique that opens portals between dimensions?", "opts": ["Amenotejikara", "Sasuke's Space-Time Dojutsu", "Kamui", "Kaguya's Yomotsu Hirasaka"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the first jinchuriki of the Ten-Tails?", "opts": ["Hagoromo Otsutsuki", "Hamura Otsutsuki", "Madara Uchiha", "Obito Uchiha"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Hagoromo's brother?", "opts": ["Indra", "Hamura", "Ashura", "Toneri"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which son of Hagoromo inherited his powerful chakra and visual prowess?", "opts": ["Ashura", "Indra", "Hamura", "Toneri"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which son of Hagoromo inherited his father's belief in love and cooperation?", "opts": ["Indra", "Ashura", "Hamura", "Kaguya"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the reincarnation of Indra immediately before Sasuke?", "opts": ["Madara", "Izuna", "Obito", "Shisui"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the reincarnation of Ashura immediately before Naruto?", "opts": ["Hashirama", "Tobirama", "Hiruzen", "Minato"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which two characters were the reincarnations of Indra and Ashura during the Warring States Period?", "opts": ["Madara and Hashirama", "Izuna and Tobirama", "Sasuke and Naruto", "Obito and Kakashi"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who sealed Kaguya Otsutsuki using the Six Paths: Chibaku Tensei?", "opts": ["Hagoromo and Hamura", "Naruto and Sasuke", "Hagoromo and Indra", "Hashirama and Madara"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was Kaguya's original reason for coming to Earth?", "opts": ["To protect humanity", "To cultivate a chakra fruit", "To destroy the shinobi world", "To find Hagoromo"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Kaguya's clan partner who arrived on Earth with her?", "opts": ["Isshiki Otsutsuki", "Momoshiki Otsutsuki", "Kinshiki Otsutsuki", "Urashiki Otsutsuki"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What form did Isshiki Otsutsuki take after being betrayed by Kaguya?", "opts": ["He became a Ten-Tails jinchuriki", "He secretly entered Jigen's body", "He became a Karma seal", "He merged with the God Tree"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the name of Isshiki's ability to shrink himself and objects?", "opts": ["Daikokuten", "Sukunahikona", "Amenominaka", "Yomotsu Hirasaka"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which ability allowed Isshiki to store shrunken objects in a dimension where time does not flow?", "opts": ["Sukunahikona", "Daikokuten", "Kamui", "Amenotejikara"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Otsutsuki possessed the ability to absorb and return chakra-based attacks through his Rinnegan?", "opts": ["Momoshiki", "Isshiki", "Kinshiki", "Urashiki"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Momoshiki's partner before he absorbed him?", "opts": ["Kinshiki", "Isshiki", "Urashiki", "Toneri"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which character destroyed the Tenseigan during The Last: Naruto the Movie?", "opts": ["Naruto", "Sasuke", "Hinata", "Toneri"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Otsutsuki was responsible for creating the Tenseigan through the Byakugan and Hamura's chakra?", "opts": ["Toneri", "Momoshiki", "Isshiki", "Kaguya"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Minato use to teleport himself and others using marked locations?", "opts": ["Flying Thunder God Technique", "Body Flicker Technique", "Reverse Summoning", "Space-Time Barrier"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who developed the Flying Thunder God Technique?", "opts": ["Minato Namikaze", "Tobirama Senju", "Hashirama Senju", "Hiruzen Sarutobi"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Hokage developed the Shadow Clone Technique?", "opts": ["Tobirama Senju", "Hashirama Senju", "Hiruzen Sarutobi", "Minato Namikaze"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Tobirama develop to revive the dead as controlled combatants?", "opts": ["Reaper Death Seal", "Summoning: Impure World Reincarnation", "Creation Rebirth", "Dead Soul Technique"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Hokage created the Tandem Paper Bomb technique?", "opts": ["Hashirama", "Tobirama", "Hiruzen", "Minato"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the sealing technique Minato used to divide Kurama's chakra into two halves?", "opts": ["Eight Trigrams Sealing Style", "Dead Demon Consuming Seal", "Four Symbols Seal", "Reaper Death Seal"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which half of Kurama was sealed inside Naruto at birth?", "opts": ["Yin half", "Yang half", "Both halves equally", "Neither half"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which half of Kurama was sealed inside Minato?", "opts": ["Yin half", "Yang half", "Both halves equally", "Neither half"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Minato's father?", "opts": ["Never revealed", "Jiraiya", "Hiruzen Sarutobi", "Danzo Shimura"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which clan did Tsunade descend from through her grandmother?", "opts": ["Uchiha", "Uzumaki", "Hyuga", "Nara"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was Tsunade's younger brother?", "opts": ["Nawaki", "Dan", "Sakumo", "Kagami"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Tsunade's lover who died during the Second Great Ninja War?", "opts": ["Dan Kato", "Nawaki", "Sakumo Hatake", "Chiyo"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which medical technique allows Tsunade to continuously regenerate her cells by releasing stored chakra?", "opts": ["Creation Rebirth", "Mystical Palm Technique", "Strength of a Hundred Seal", "Chakra Scalpel"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the name of the seal on Tsunade's forehead?", "opts": ["Strength of a Hundred Seal", "Eight Trigrams Seal", "Cursed Seal of Heaven", "Diamond Seal"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which member of the Akatsuki was known as the 'Artist of the Explosion'?", "opts": ["Sasori", "Deidara", "Kakuzu", "Hidan"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Deidara's explosive clay technique that created a microscopic bomb?", "opts": ["C4 Karura", "C3", "C2 Dragon", "C0"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Deidara's final self-destructive explosion technique?", "opts": ["C0", "C4 Karura", "C3", "C2 Dragon"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Akatsuki member was the original owner of the Third Kazekage puppet?", "opts": ["Sasori", "Chiyo", "Kankuro", "Deidara"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which puppet did Sasori use as his own body?", "opts": ["Hiruko", "Third Kazekage", "Sasori of the Red Sand", "Mother and Father"], "ans": 2},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was Sasori's nickname?", "opts": ["Sasori of the Red Sand", "The Puppet Master", "The Sand Demon", "The Crimson Scorpion"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Akatsuki member could use five different chakra natures through stolen hearts?", "opts": ["Kakuzu", "Hidan", "Sasori", "Kisame"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "How many hearts could Kakuzu maintain in his body at once?", "opts": ["Three", "Four", "Five", "Six"], "ans": 2},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Akatsuki member worshipped the deity Jashin?", "opts": ["Kakuzu", "Hidan", "Deidara", "Sasori"], "ans": 1},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of Hidan's ritual technique?", "opts": ["Curse Technique: Death Controlling Possessed Blood", "Reaper Death Seal", "Soul Removal Technique", "Dead Demon Consuming Seal"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Akatsuki member wielded the Samehada sword?", "opts": ["Kisame Hoshigaki", "Zabuza Momochi", "Suigetsu Hozuki", "Mangetsu Hozuki"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the original owner of Samehada before Kisame?", "opts": ["Fuguki Suikazan", "Zabuza Momochi", "Mangetsu Hozuki", "Chojuro"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which member of the Seven Ninja Swordsmen wielded the Kubikiribocho?", "opts": ["Zabuza Momochi", "Kisame Hoshigaki", "Jinin Akebino", "Jinpachi Munashi"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which sword of the Seven Ninja Swordsmen can absorb and store lightning chakra?", "opts": ["Kiba", "Samehada", "Kabutowari", "Nuibari"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which sword of the Seven Ninja Swordsmen is known as the Sewing Needle?", "opts": ["Nuibari", "Kiba", "Hiramekarei", "Shibuki"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which sword is known as the Bluntsword and consists of a hammer and axe?", "opts": ["Kabutowari", "Shibuki", "Nuibari", "Hiramekarei"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which member of the Seven Ninja Swordsmen wielded Hiramekarei?", "opts": ["Chojuro", "Zabuza", "Kisame", "Jinpachi"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What was the name of the Kaguya clan's unique bone-manipulation Kekkei Genkai?", "opts": ["Shikotsumyaku", "Kekkei Genkai: Ice Release", "Jugo's Clan Curse", "Wood Release"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which character was the last known surviving member of the Kaguya clan?", "opts": ["Kimimaro", "Haku", "Jugo", "Suigetsu"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which clan was responsible for the unique ability to manipulate shadows?", "opts": ["Nara", "Yamanaka", "Akimichi", "Aburame"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which clan specializes in mind-transfer techniques?", "opts": ["Yamanaka", "Nara", "Akimichi", "Inuzuka"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which clan uses insects as part of its fighting style?", "opts": ["Aburame", "Nara", "Yamanaka", "Hyuga"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the name of the special insect species Shino's clan commonly uses?", "opts": ["Kikaichu", "Rinkaichu", "Nano Bugs", "Kumogakure Beetles"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which insect species was used by Torune Aburame?", "opts": ["Rinkaichu", "Kikaichu", "Nano Bugs", "Kumogakure Beetles"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Hyuga technique blocks an opponent's chakra points using precise strikes?", "opts": ["Gentle Fist", "Eight Gates", "Shadow Imitation", "Chakra Scalpel"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "How many chakra points does the Byakugan allow a user to see in the human body?", "opts": ["361", "365", "360", "108"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which Hyuga technique creates a rotating defensive chakra barrier?", "opts": ["Eight Trigrams Palms Revolving Heaven", "Eight Trigrams Sixty-Four Palms", "Gentle Fist Art", "Eight Trigrams Vacuum Palm"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was the leader of the Hyuga clan during Naruto's childhood?", "opts": ["Hiashi Hyuga", "Hizashi Hyuga", "Neji Hyuga", "Hanabi Hyuga"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who was Neji's father?", "opts": ["Hizashi Hyuga", "Hiashi Hyuga", "Hiruzen Sarutobi", "Kizashi Haruno"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Neji use to strike all 64 chakra points of an opponent?", "opts": ["Eight Trigrams Sixty-Four Palms", "Eight Trigrams Palms Revolving Heaven", "Vacuum Palm", "Gentle Step Twin Lion Fists"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which character created the Rasengan?", "opts": ["Minato Namikaze", "Jiraiya", "Tobirama Senju", "Kakashi Hatake"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Who completed the addition of elemental nature transformation to the Rasengan by creating the Wind Style: Rasenshuriken?", "opts": ["Naruto Uzumaki", "Minato Namikaze", "Kakashi Hatake", "Jiraiya"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which nature transformation did Naruto add to the Rasengan?", "opts": ["Wind Release", "Lightning Release", "Fire Release", "Water Release"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Kakashi use to create a concentrated lightning blade?", "opts": ["Chidori", "Rasengan", "Raikiri: Kamui", "Lightning Release: False Darkness"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "What is the other name commonly used for Kakashi's Chidori?", "opts": ["Raikiri", "Kirin", "Raiden", "Lightning Fang"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Sasuke use to summon a massive lightning strike from the natural atmosphere?", "opts": ["Kirin", "Chidori Nagashi", "Amaterasu", "Kagutsuchi"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which technique did Jiraiya use to enter Sage Mode?", "opts": ["Toad Sage Mode", "Snake Sage Mode", "Six Paths Sage Mode", "Perfect Sage Mode of Slugs"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Where did Naruto learn to use Sage Mode?", "opts": ["Mount Myoboku", "Ryuchi Cave", "Shikkotsu Forest", "Valley of the End"], "ans": 0},

{"cat": "Naruto", "diff": "Hard", "xp": 150, "q": "Which sage taught Naruto how to gather natural energy?", "opts": ["Fukasaku", "Shima", "Gamabunta", "Gamamaru"], "ans": 0},

    # One Piece
    {"q": "What is the ultimate treasure sought by pirates in One Piece called?", "options": ["All Blue", "One Piece", "Poneglyph", "Ancient Weapon"], "ans": 1, "cat": "one piece", "diff": "Easy"},
    {"q": "What type of Devil Fruit did Luffy accidentally eat?", "options": ["Logia", "Zoan", "Paramecia (Gomu Gomu no Mi)", "Mythical Zoan"], "ans": 2, "cat": "one piece", "diff": "Easy"},
    {"q": "Who is the swordsman of the Straw Hat Pirates aiming to be the world's greatest?", "options": ["Sanji", "Zoro", "Brook", "Shanks"], "ans": 1, "cat": "one piece", "diff": "Easy"},
    {"q": "What is the name of Sanji's royal family lineage?", "options": ["Donquixote Family", "Vinsmoke Family", "Kozuki Family", "Charlotte Family"], "ans": 1, "cat": "one piece", "diff": "Medium"},
    {"q": "Which Marine Admiral possesses the Magma-Magma fruit powers?", "options": ["Aokiji", "Kizaru", "Akainu", "Fujitora"], "ans": 2, "cat": "one piece", "diff": "Medium"},
    # ONE PIECE — FRESH QUESTION BANK (100 QUESTIONS)

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which sword did Zoro receive from the village of Shimotsuki?", "opts": ["Sandai Kitetsu", "Wado Ichimonji", "Yubashiri", "Shusui"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who gave Zoro the Sandai Kitetsu?", "opts": ["Ipponmatsu", "Tashigi", "Kuina", "Koshiro"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the grade of Mihawk's sword Yoru?", "opts": ["Great Grade", "Skillful Grade", "Supreme Grade", "Ordinary Grade"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which sword did Ryuma originally wield before it became Zoro's?", "opts": ["Enma", "Shusui", "Yoru", "Ame no Habakiri"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who is the creator of the Wado Ichimonji?", "opts": ["Shimotsuki Kozaburo", "Tenguyama Hitetsu", "Kozuki Sukiyaki", "Koushirou"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which of these is NOT one of the 21 Great Grade swords?", "opts": ["Enma", "Wado Ichimonji", "Shusui", "Yoru"], "ans": 3},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the technique Zoro used against King that involved his three swords being coated in Conqueror's Haki?", "opts": ["Sanzen Sekai", "King of Hell: Three Sword Serpent", "Ashura: Ichibugin", "Oni Giri"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which member of the Worst Generation has the epithet 'Roar of the Sea'?", "opts": ["Eustass Kid", "Scratchmen Apoo", "Capone Bege", "Basil Hawkins"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of Eustass Kid's Devil Fruit?", "opts": ["Jiki Jiki no Mi", "Giro Giro no Mi", "Buki Buki no Mi", "Pamu Pamu no Mi"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Worst Generation member is also known as the 'Magician'?", "opts": ["X Drake", "Basil Hawkins", "Urouge", "Apoo"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of Urouge's homeland?", "opts": ["Sky Island", "Birkan", "Weatheria", "Skypiea"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Worst Generation pirate was formerly a Marine rear admiral?", "opts": ["Killer", "X Drake", "Capone Bege", "Jewelry Bonney"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of X Drake's secret Marine organization?", "opts": ["SWORD", "CIPHER POL", "Aegis Zero", "G-5"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which organization did Rob Lucci belong to before joining CP0?", "opts": ["SWORD", "CP9", "G-1", "Revolutionary Army"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the former leader of CP9 before Spandam?", "opts": ["Rob Lucci", "Spandine", "Blueno", "Kaku"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Rokushiki technique allows its user to move at extremely high speeds?", "opts": ["Tekkai", "Geppo", "Soru", "Rankyaku"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Rokushiki technique creates flying air blades?", "opts": ["Shigan", "Rankyaku", "Kami-e", "Rokuogan"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which CP9 member developed the technique known as Rokuogan?", "opts": ["Kaku", "Jabra", "Rob Lucci", "Blueno"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the island where the World Government's judicial headquarters is located?", "opts": ["Enies Lobby", "Impel Down", "Marineford", "Mary Geoise"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which sea train station is located closest to Enies Lobby?", "opts": ["Blue Station", "Shift Station", "Kingbull Station", "Sea Train Terminal"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the former owner of the Kaku's Devil Fruit?", "opts": ["It was never previously owned; Kaku ate it", "Rob Lucci", "Spandam", "Jabra"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the model of Kaku's Devil Fruit?", "opts": ["Giraffe", "Brachiosaurus", "Pteranodon", "Allosaurus"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Devil Fruit allows Blueno to create doors on virtually any surface?", "opts": ["Door Door Fruit", "Warp Warp Fruit", "Pocket Pocket Fruit", "Mirror Mirror Fruit"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the ancient kingdom's archaeologist who was Nico Robin's mother?", "opts": ["Olvia", "Bell-mère", "Clover", "Lily"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the head archaeologist of Ohara?", "opts": ["Professor Clover", "Professor Vegapunk", "Professor Hiriluk", "Professor Tsukimi"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Marine ordered the Buster Call on Ohara?", "opts": ["Akainu", "Aokiji", "Sengoku", "Kizaru"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the Marine vice admiral who secretly helped Robin escape Ohara?", "opts": ["Jaguar D. Saul", "Monkey D. Garp", "Kuzan", "Tsuru"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the giant who became Robin's friend on Ohara?", "opts": ["Hajrudin", "Jaguar D. Saul", "Oimo", "Kashii"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which island was destroyed by the Buster Call that Robin survived as a child?", "opts": ["Ohara", "God Valley", "Flevance", "Jaya"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the poneglyph that records the history of the Void Century?", "opts": ["Road Poneglyph", "Rio Poneglyph", "Historical Poneglyph", "Blue Poneglyph"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "How many Road Poneglyphs are needed to locate Laugh Tale?", "opts": ["Two", "Three", "Four", "Five"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character is known as the 'Man Marked by Flames'?", "opts": ["Jaguar D. Saul", "Scopper Gaban", "Unknown identity", "Monkey D. Dragon"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was responsible for teaching the Kozuki clan how to read and write Poneglyphs?", "opts": ["Kozuki Sukiyaki", "Kozuki Oden", "Kozuki Toki", "Kozuki Momonosuke"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient weapon hidden in Wano?", "opts": ["Uranus", "Poseidon", "Pluton", "Noah"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Where is the ancient weapon Pluton believed to be located?", "opts": ["Under Wano", "Under Alabasta", "Inside Fish-Man Island", "At Laugh Tale"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who revealed the location of Pluton to Robin?", "opts": ["Kozuki Sukiyaki", "Momonosuke", "Oden", "Kaido"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which ancient weapon is associated with the ability to command Sea Kings?", "opts": ["Pluton", "Uranus", "Poseidon", "Noah"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the ancient kingdom's enemy alliance during the Void Century?", "opts": ["The Twenty Kingdoms", "The Ancient Alliance", "The World Pirates", "The Five Elders"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which family among the original Twenty Kingdoms did NOT move to Mary Geoise?", "opts": ["Nefertari", "Donquixote", "Figarland", "Jaygarcia"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the title given to the highest-ranking Celestial Dragons who govern the World Government?", "opts": ["Holy Knights", "Five Elders", "God's Knights", "World Nobles"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the mysterious ruler who sits on the Empty Throne?", "opts": ["Imu", "Joy Boy", "Nerona D. Imu", "Saint Saturn"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which of the Five Elders is known as the Warrior God of Finance?", "opts": ["Topman Warcury", "Ethanbaron V. Nusjuro", "Marcus Mars", "Shepherd Ju Peter"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Elder is known as the Warrior God of Environment?", "opts": ["Marcus Mars", "Saint Saturn", "Topman Warcury", "Shepherd Ju Peter"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Elder was the Warrior God of Science and Defense?", "opts": ["Saint Saturn", "Topman Warcury", "Marcus Mars", "Ethanbaron V. Nusjuro"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the ancient robot that attacked Mary Geoise 200 years ago?", "opts": ["Emeth", "Emet", "Iron Giant", "General Franky"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the ancient robot waiting for during the events of Egghead?", "opts": ["Joy Boy", "Nika", "Imu", "Luffy's father"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the scientist who created the Mother Flame?", "opts": ["Vegapunk", "Caesar Clown", "Judge Vinsmoke", "Queen"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Vegapunk satellite represents his evil side?", "opts": ["Lilith", "Shaka", "Edison", "Pythagoras"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Vegapunk satellite represents his wisdom?", "opts": ["Shaka", "Lilith", "York", "Atlas"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Vegapunk satellite represents his greed?", "opts": ["York", "Atlas", "Edison", "Pythagoras"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Vegapunk satellite represents his violence?", "opts": ["Atlas", "Lilith", "Shaka", "York"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Vegapunk satellite represents his thinking?", "opts": ["Pythagoras", "Edison", "York", "Shaka"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Vegapunk satellite represents his creativity?", "opts": ["Edison", "Pythagoras", "Atlas", "Lilith"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Vegapunk satellite was responsible for recording and broadcasting the message about the world's future?", "opts": ["Shaka", "Lilith", "Stella", "York"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the island where Vegapunk's main laboratory is located?", "opts": ["Egghead", "Karai Bari", "Baltigo", "Punk Hazard"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was responsible for creating the Seraphim?", "opts": ["Dr. Vegapunk", "Judge Vinsmoke", "Caesar Clown", "Queen"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What race's lineage factor was used to give the Seraphim their special durability?", "opts": ["Lunarian", "Giant", "Mink", "Buccaneer"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Seraphim is based on Dracule Mihawk?", "opts": ["S-Hawk", "S-Snake", "S-Bear", "S-Shark"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Seraphim is based on Boa Hancock?", "opts": ["S-Snake", "S-Hawk", "S-Bear", "S-Shark"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Seraphim is based on Jinbe?", "opts": ["S-Shark", "S-Hawk", "S-Snake", "S-Bear"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Seraphim is based on Bartholomew Kuma?", "opts": ["S-Bear", "S-Hawk", "S-Snake", "S-Shark"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the special authority chip used to command Pacifistas and Seraphim?", "opts": ["Authority Chip", "Control Dial", "Command Core", "Pacifista Key"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character possesses the Toshi Toshi no Mi?", "opts": ["Jewelry Bonney", "Shakky", "Stussy", "Ginny"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of Kuma's home kingdom?", "opts": ["Sorbet Kingdom", "Goa Kingdom", "Lulusia Kingdom", "Prodence Kingdom"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was Kuma's father's name?", "opts": ["Clapp", "Ginny", "Bukan", "Bartholomew"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which race did Kuma belong to?", "opts": ["Buccaneer", "Lunarian", "Mink", "Giant"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the former owner of the Paw-Paw Fruit before Kuma?", "opts": ["Unknown", "Ivankov", "Dragon", "Vegapunk"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the revolutionary who was Kuma's close friend and later became Bonney's mother?", "opts": ["Ginny", "Koala", "Belo Betty", "Inazuma"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Revolutionary Army commander controls the East Army?", "opts": ["Belo Betty", "Morley", "Karasu", "Lindbergh"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Revolutionary Army commander controls the West Army?", "opts": ["Morley", "Belo Betty", "Karasu", "Lindbergh"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Revolutionary Army commander controls the North Army?", "opts": ["Karasu", "Morley", "Lindbergh", "Belo Betty"], "ans": 1},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Revolutionary Army commander controls the South Army?", "opts": ["Lindbergh", "Karasu", "Morley", "Belo Betty"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the Revolutionary Army's chief of staff?", "opts": ["Sabo", "Koala", "Hack", "Dragon"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character trained Sabo in the use of the Dragon Claw Fist?", "opts": ["Monkey D. Dragon", "Emporio Ivankov", "Hack", "Koala"], "ans": 2},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of Sabo's signature fighting technique?", "opts": ["Dragon Claw Fist", "Rokuogan", "Fish-Man Karate", "Hasshoken"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Devil Fruit did Sabo inherit from Ace?", "opts": ["Mera Mera no Mi", "Hie Hie no Mi", "Magu Magu no Mi", "Goro Goro no Mi"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the kingdom where Sabo, Ace, and Luffy grew up?", "opts": ["Goa Kingdom", "Sorbet Kingdom", "Lvneel Kingdom", "Dawn Kingdom"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the first person to give Luffy his iconic straw hat?", "opts": ["Shanks", "Gol D. Roger", "Rayleigh", "Garp"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who originally owned the straw hat before Shanks?", "opts": ["Gol D. Roger", "Joy Boy", "Rocks D. Xebec", "Silvers Rayleigh"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Where was the giant straw hat seen in the story kept?", "opts": ["Mary Geoise", "Impel Down", "Punk Hazard", "Laugh Tale"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient figure whose will is connected to the giant straw hat?", "opts": ["Joy Boy", "Rocks D. Xebec", "Nika", "Imu"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which kingdom was ruled by the Nefertari family?", "opts": ["Alabasta", "Dressrosa", "Drum Kingdom", "Prodence Kingdom"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the Alabasta king who was framed by Crocodile?", "opts": ["Nefertari Cobra", "Nefertari Titi", "Nefertari D. Lili", "Nefertari Kobra"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which organization did Crocodile secretly lead in Alabasta?", "opts": ["Baroque Works", "Donquixote Family", "Germa 66", "Cross Guild"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the codename of Nico Robin when she worked for Baroque Works?", "opts": ["Miss All Sunday", "Miss Doublefinger", "Miss Goldenweek", "Miss Valentine"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was Mr. 1's partner in Baroque Works?", "opts": ["Miss Doublefinger", "Miss All Sunday", "Miss Goldenweek", "Miss Merry Christmas"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the Devil Fruit that allows Daz Bonez to turn his body into blades?", "opts": ["Supa Supa no Mi", "Buki Buki no Mi", "Kama Kama no Mi", "Toge Toge no Mi"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Baroque Works agent possessed the Kilo Kilo no Mi?", "opts": ["Miss Valentine", "Miss Doublefinger", "Miss Goldenweek", "Miss Merry Christmas"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Baroque Works agent possessed the Toge Toge no Mi?", "opts": ["Miss Doublefinger", "Miss Valentine", "Miss Goldenweek", "Miss Monday"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Baroque Works agent was actually a painter and used colors to manipulate emotions?", "opts": ["Miss Goldenweek", "Miss Valentine", "Miss Doublefinger", "Miss Merry Christmas"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the giant duck ridden by Vivi?", "opts": ["Karoo", "Pierre", "Matsuge", "Bunbuku"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which animal served as the leader of the Super Spot-Billed Duck Troops?", "opts": ["Karoo", "Matsuge", "Pierre", "Chouchou"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the kingdom where Chopper was born?", "opts": ["Drum Kingdom", "Alabasta", "Sakura Kingdom", "Lvneel Kingdom"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was Dr. Hiriluk's dream for Drum Island?", "opts": ["To cure the country's hearts", "To become Pirate King", "To discover the One Piece", "To defeat the World Government"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the mushroom Chopper mistakenly believed could cure Hiriluk?", "opts": ["Amiudake", "Sakura Mushroom", "Rumble Mushroom", "Blue Mushroom"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which doctor became Chopper's mentor after Hiriluk's death?", "opts": ["Dr. Kureha", "Dr. Hogback", "Dr. Vegapunk", "Dr. Tsukimi"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of Chopper's transformation-enhancing medicine?", "opts": ["Rumble Ball", "Energy Steroid", "SAD", "Blue Pill"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Devil Fruit did Brook eat?", "opts": ["Yomi Yomi no Mi", "Horo Horo no Mi", "Kage Kage no Mi", "Soru Soru no Mi"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the Rumbar Pirates' captain before Brook?", "opts": ["Yorki", "Laboon", "Crocus", "Lafitte"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which island did the Rumbar Pirates originally come from?", "opts": ["West Blue", "North Blue", "South Blue", "East Blue"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character is known as the 'Soul King'?", "opts": ["Brook", "Gecko Moria", "Hody Jones", "Scratchmen Apoo"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of Brook's sword?", "opts": ["Soul Solid", "Shusui", "Yoru", "Enma"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which island did the Straw Hats visit immediately after leaving Fish-Man Island?", "opts": ["Punk Hazard", "Dressrosa", "Zou", "Wano"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the samurai whose torso appeared on Punk Hazard?", "opts": ["Kin'emon", "Kanjuro", "Raizo", "Denjiro"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was revealed to be the traitor who leaked information to Orochi?", "opts": ["Kanjuro", "Kin'emon", "Denjiro", "Ashura Doji"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the legendary swordsman from Wano whose corpse was stolen from his grave?", "opts": ["Shimotsuki Ryuma", "Kozuki Oden", "Shimotsuki Ushimaru", "Kozuki Sukiyaki"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which sword was known as the national treasure of Wano?", "opts": ["Shusui", "Enma", "Ame no Habakiri", "Nidai Kitetsu"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the daimyo of Kuri before Kaido took control of Wano?", "opts": ["Kozuki Oden", "Denjiro", "Ashura Doji", "Shimotsuki Ushimaru"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which member of the Nine Red Scabbards was also known as Kyoshiro?", "opts": ["Denjiro", "Kin'emon", "Kawamatsu", "Raizo"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the weapon used by Kozuki Oden to fight Kaido?", "opts": ["Enma and Ame no Habakiri", "Shusui and Yoru", "Wado Ichimonji and Enma", "Nidai Kitetsu and Sandai Kitetsu"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the first person to wound Kaido permanently?", "opts": ["Kozuki Oden", "Whitebeard", "Shanks", "Garp"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of Kaido's strongest known attack against Luffy?", "opts": ["Flaming Drum Dragon", "Thunder Bagua", "Death Destroyer Thunder Bagua", "Boro Breath"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which member of the Worst Generation helped Luffy and Law defeat Kaido and Big Mom?", "opts": ["Eustass Kid", "Urouge", "Apoo", "Hawkins"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the technique Law used to silence Big Mom?", "opts": ["Silence", "Gamma Knife", "Injection Shot", "Counter Shock"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which technique did Kid use to assign magnetic polarity to Big Mom?", "opts": ["Assign", "Punk Gibson", "Damned Punk", "Punk Rotten"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of Luffy's awakened Devil Fruit form?", "opts": ["Gear Fifth", "Gear Fourth", "Nightmare Luffy", "Gear Sixth"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the true name of Luffy's Devil Fruit?", "opts": ["Hito Hito no Mi, Model: Nika", "Gomu Gomu no Mi", "Hito Hito no Mi, Model: Daibutsu", "Mera Mera no Mi"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which organization concealed the true identity of Luffy's Devil Fruit for centuries?", "opts": ["World Government", "Revolutionary Army", "Cross Guild", "Marines"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the ancient warrior associated with the Sun God Nika?", "opts": ["Joy Boy", "Rocks D. Xebec", "Noland", "Davy Jones"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character is known as the 'Strongest Creature in the World'?", "opts": ["Kaido", "Whitebeard", "Big Mom", "Blackbeard"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character is known as the 'World's Strongest Swordsman'?", "opts": ["Dracule Mihawk", "Shanks", "Roronoa Zoro", "Silvers Rayleigh"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the pirate crew that once included Kaido, Big Mom, and Whitebeard?", "opts": ["Rocks Pirates", "Roger Pirates", "Beasts Pirates", "Golden Lion Pirates"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who defeated the Rocks Pirates at God Valley alongside Garp?", "opts": ["Gol D. Roger", "Sengoku", "Rayleigh", "Shiki"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the captain of the Rocks Pirates?", "opts": ["Rocks D. Xebec", "Gol D. Roger", "Edward Newgate", "Shiki"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which Marine earned the title 'Hero of the Marines' after the God Valley incident?", "opts": ["Monkey D. Garp", "Sengoku", "Tsuru", "Kong"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which former Rocks Pirates member became the captain of the Golden Lion Pirates?", "opts": ["Shiki", "Kaido", "Whitebeard", "Big Mom"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What was the name of the island where Roger was executed?", "opts": ["Loguetown", "Shells Town", "Foosha Village", "Baterilla"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Who was the Marine officer who executed Gol D. Roger?", "opts": ["Unknown executioners", "Monkey D. Garp", "Sengoku", "Smoker"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which pirate was the first known person to reach Laugh Tale with Roger?", "opts": ["Silvers Rayleigh", "Shanks", "Buggy", "Crocus"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What did Roger's crew discover on Laugh Tale?", "opts": ["The true history and the One Piece", "The location of the All Blue", "The ancient weapon Uranus", "The secret of Devil Fruit creation"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Why did Roger's crew laugh after discovering the treasure on Laugh Tale?", "opts": ["The exact reason has not been fully revealed", "They found no treasure", "They were tricked by Joy Boy", "They discovered the world was empty"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which character was too young to understand what happened at Laugh Tale?", "opts": ["Shanks", "Rayleigh", "Crocus", "Scopper Gaban"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of Roger's first mate?", "opts": ["Silvers Rayleigh", "Scopper Gaban", "Kozuki Oden", "Crocus"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "Which former Roger Pirates member became the doctor of the Rumbar Pirates?", "opts": ["Crocus", "Rayleigh", "Gaban", "Oden"], "ans": 0},

{"cat": "One Piece", "diff": "Hard", "xp": 150, "q": "What is the name of the giant tree on Elbaf?", "opts": ["Treasure Tree Adam", "Sunlight Tree Eve", "Yggdrasil", "Ohara Tree of Knowledge"], "ans": 2},    

    # Bleach
    {"q": "What is the name of Ichigo Kurosaki's iconic zanpakuto in its initial Shikai state?", "options": ["Zangetsu", "Senbonzakura", "Kyoka Suigetsu", "Hyorinmaru"], "ans": 0, "cat": "bleach", "diff": "Easy"},
    {"q": "Who is the captain of Squad 10 known for his ice-type Zanpakuto?", "options": ["Byakuya Kuchiki", "Toshiro Hitsugaya", "Kenpachi Zaraki", "Shunsui Kyoraku"], "ans": 1, "cat": "bleach", "diff": "Easy"},
    {"q": "What race are the spiritual beings residing in Hueco Mundo?", "options": ["Soul Reapers", "Quincys", "Hollows / Arrancar", "Bounts"], "ans": 2, "cat": "bleach", "diff": "Easy"},

    # Dragon Ball
    {"q": "What is the name of Goku's signature energy attack taught by Master Roshi?", "options": ["Spirit Bomb", "Kamehameha", "Final Flash", "Special Beam Cannon"], "ans": 1, "cat": "dragon ball", "diff": "Easy"},
    {"q": "What is Vegeta's royal title?", "options": ["Prince of all Saiyans", "King of Earth", "Emperor of Universe 7", "Lord of Space"], "ans": 0, "cat": "dragon ball", "diff": "Easy"},
    {"q": "How many Dragon Balls must be gathered to summon Shenron?", "options": ["5", "7", "10", "3"], "ans": 1, "cat": "dragon ball", "diff": "Easy"},

    # Jujutsu Kaisen
    {"q": "What cursed object does Yuji Itadori swallow at the beginning of the series?", "options": ["Sukuna's Finger", "Prison Realm", "Cursed Womb", "Death Painting"], "ans": 0, "cat": "jujutsu kaisen", "diff": "Easy"},
    {"q": "What is Satoru Gojo's signature innate technique category?", "options": ["Ten Shadows", "Limitless (Infinity)", "Blood Manipulation", "Idle Transfiguration"], "ans": 1, "cat": "jujutsu kaisen", "diff": "Easy"},
    {"q": "Who is known as the King of Curses?", "options": ["Mahito", "Kenjaku", "Ryomen Sukuna", "Suguru Geto"], "ans": 2, "cat": "jujutsu kaisen", "diff": "Easy"},

    # Demon Slayer
    {"q": "What is the name of Tanjiro's breathing style taught by Urokodaki?", "options": ["Thunder Breathing", "Water Breathing", "Sun Breathing", "Flame Breathing"], "ans": 1, "cat": "demon slayer", "diff": "Easy"},
    {"q": "What substance allows demons to survive sunlight in small doses or grow stronger?", "options": ["Blue Spider Lily", "Wisteria Flower", "Human Blood", "Muzan's Cells"], "ans": 0, "cat": "demon slayer", "diff": "Medium"},

    # Attack on Titan
    {"q": "Inside which circular defensive wall does humanity live at the start of AOT?", "options": ["Wall Maria", "Wall Rose", "Wall Sina", "All of the above"], "ans": 3, "cat": "attack on titan", "diff": "Easy"},
    {"q": "What is the proper name of the elite squad led by Levi Ackerman?", "options": ["Survey Corps", "Military Police", "Garrison Regiment", "Yeagerists"], "ans": 0, "cat": "attack on titan", "diff": "Easy"}
]


def is_group_chat(message: Message) -> bool:
    return message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]


def get_quiz_lobby_text(host_name: str, host_id: int, category: str, players_dict: dict) -> str:
    if players_dict:
        player_list = "\n".join(
            [f"{idx}. 🧠 [{name}](tg://user?id={uid})" for idx, (uid, name) in enumerate(players_dict.items(), 1)]
        )
    else:
        player_list = "• *Waiting for challengers to join...*"

    host_mention = f"[{host_name}](tg://user?id={host_id})"

    return (
        f"🧠 **ANIME QUIZ — MATCH LOBBY**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 **Host:** {host_mention}\n"
        f"📚 **Category:** `{category.title()}` (10 Questions)\n"
        f"👥 **Joined Challengers ({len(players_dict)}/10):**\n"
        f"{player_list}\n\n"
        f"👉 Type `/join` to enter • `/startgame` to begin!"
    )


@router.message(Command("quiz"))
async def cmd_quiz_create(message: Message):
    if not is_group_chat(message):
        return await message.answer(
            "❌ **Anime Quiz can only be played inside group chats!** Add me to a group to host a match.",
            parse_mode="Markdown",
        )

    chat_id = message.chat.id
    if chat_id in QUIZ_LOBBIES or chat_id in ACTIVE_QUIZZES:
        return await message.reply("⚠️ A quiz match or lobby is already active in this group!")

    args = message.text.split(maxsplit=1)
    category = args[1].lower() if len(args) > 1 else "all animes"

    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    QUIZ_LOBBIES[chat_id] = {
        "host": message.from_user.id,
        "host_name": message.from_user.full_name,
        "category": category,
        "players": {message.from_user.id: message.from_user.full_name},
    }

    lobby_text = get_quiz_lobby_text(
        host_name=message.from_user.full_name,
        host_id=message.from_user.id,
        category=category,
        players_dict=QUIZ_LOBBIES[chat_id]["players"],
    )
    await message.answer(lobby_text, parse_mode="Markdown")


@router.message(Command("quizanimes"))
async def cmd_list_quiz_animes(message: Message):
    categories = sorted(list(set(q["cat"] for q in QUESTION_BANK)))
    text = (
        f"📚 **QUIZ CATEGORIES & DATABASE**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• `All Animes` (Default mixed questions)\n"
        + "".join(f"• `{c.title()}`\n" for c in categories) +
        f"\n👉 *Usage example:* `/quiz naruto`"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("join"))
async def cmd_quiz_join(message: Message):
    if not is_group_chat(message):
        return await message.reply("❌ Lobbies can only be joined inside group chats.")

    chat_id = message.chat.id
    lobby = QUIZ_LOBBIES.get(chat_id)
    if not lobby:
        return await message.reply("❌ No waiting quiz lobby found. Start one with `/quiz`.")

    uid = message.from_user.id
    if uid in lobby["players"]:
        return await message.reply("✅ You already joined the lobby!")
    if len(lobby["players"]) >= 10:
        return await message.reply("🚫 Lobby full (10/10).")

    await ensure_user(uid, message.from_user.username, message.from_user.full_name)
    lobby["players"][uid] = message.from_user.full_name

    lobby_text = get_quiz_lobby_text(
        host_name=lobby["host_name"],
        host_id=lobby["host"],
        category=lobby["category"],
        players_dict=lobby["players"],
    )
    await message.answer(
        f"🧠 **{message.from_user.full_name}** joined the Quiz lobby!\n\n{lobby_text}",
        parse_mode="Markdown",
    )


@router.message(Command("startgame"))
async def cmd_quiz_startgame(message: Message):
    chat_id = message.chat.id
    lobby = QUIZ_LOBBIES.get(chat_id)
    if not lobby:
        return

    if message.from_user.id != lobby["host"]:
        return await message.reply("⚠️ Only the host can start the quiz match.")

    QUIZ_LOBBIES.pop(chat_id, None)

    cat = lobby["category"]
    if cat == "all animes":
        filtered_questions = QUESTION_BANK
    else:
        filtered_questions = [q for q in QUESTION_BANK if cat in q["cat"].lower()]
        if len(filtered_questions) < 5:
            filtered_questions = QUESTION_BANK  # Fallback if category has too few questions

    # Pick 10 questions (or max available)
    selected_questions = random.sample(filtered_questions, k=min(10, len(filtered_questions)))

    ACTIVE_QUIZZES[chat_id] = {
        "players": lobby["players"],
        "scores": {uid: 0 for uid in lobby["players"]},
        "questions": selected_questions,
        "current_q": 0,
        "answered": set(),
        "correct_user": None,
    }

    await message.answer(
        f"🚀 **ANIME QUIZ MATCH STARTED!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Total Questions: **{len(selected_questions)}**\n"
        f"Get ready for Question 1!",
        parse_mode="Markdown",
    )
    await asyncio.sleep(2)
    await send_next_quiz_question(message, chat_id)


async def send_next_quiz_question(message: Message, chat_id: int):
    quiz = ACTIVE_QUIZZES.get(chat_id)
    if not quiz:
        return

    q_idx = quiz["current_q"]
    if q_idx >= len(quiz["questions"]):
        return await finalize_quiz_match(message, chat_id)

    q_data = quiz["questions"][q_idx]
    quiz["answered"] = set()
    quiz["correct_user"] = None

    options_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"quizans:{chat_id}:{i}")]
            for i, opt in enumerate(q_data["options"])
        ]
    )

    q_text = (
        f"🧠 **QUESTION {q_idx + 1} / {len(quiz['questions'])}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"❓ **{q_data['q']}**\n\n"
        f"⏱️ *You have 15 seconds to answer!*"
    )
    
    await message.answer(q_text, reply_markup=options_kb, parse_mode="Markdown")
    await asyncio.sleep(15)

    # After 15 seconds check if answered, else move to next
    if chat_id in ACTIVE_QUIZZES and quiz["current_q"] == q_idx:
        quiz["current_q"] += 1
        correct_ans_text = q_data["options"][q_data["ans"]]
        await message.answer(
            f"⏰ **Time's up for Question {q_idx + 1}!**\n"
            f"✅ Correct Answer was: **{correct_ans_text}**",
            parse_mode="Markdown",
        )
        await asyncio.sleep(2)
        await send_next_quiz_question(message, chat_id)


@router.callback_query(F.data.startswith("quizans:"))
async def cb_quiz_answer(callback: CallbackQuery):
    _, chat_id_s, opt_idx_s = callback.data.split(":")
    chat_id = int(chat_id_s)
    quiz = ACTIVE_QUIZZES.get(chat_id)

    if not quiz:
        return await callback.answer("Quiz is not active.", show_alert=True)

    uid = callback.from_user.id
    if uid not in quiz["players"]:
        return await callback.answer("You are not part of this quiz match!", show_alert=True)

    if uid in quiz["answered"]:
        return await callback.answer("You already answered this question!", show_alert=True)

    quiz["answered"].add(uid)
    q_idx = quiz["current_q"]
    q_data = quiz["questions"][q_idx]
    chosen_ans = int(opt_idx_s)

    if chosen_ans == q_data["ans"]:
        quiz["scores"][uid] += 10
        p_name = quiz["players"][uid]
        await callback.answer("🎉 Correct Answer!", show_alert=True)
        
        # Instantly lock question and move forward
        quiz["current_q"] += 1
        correct_ans_text = q_data["options"][q_data["ans"]]
        await callback.message.edit_text(
            f"🧠 **QUESTION {q_idx + 1} — ANSWERED!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"❓ **{q_data['q']}**\n\n"
            f"🏆 **First Correct:** [{p_name}](tg://user?id={uid}) (+10 pts)\n"
            f"✅ Answer: **{correct_ans_text}**",
            parse_mode="Markdown",
        )
        await asyncio.sleep(2)
        await send_next_quiz_question(callback.message, chat_id)
    else:
        await callback.answer("❌ Wrong Answer!", show_alert=True)


async def finalize_quiz_match(message: Message, chat_id: int):
    quiz = ACTIVE_QUIZZES.pop(chat_id, None)
    if not quiz:
        return

    sorted_scores = sorted(quiz["scores"].items(), key=lambda x: x[1], reverse=True)
    
    score_board = ""
    for rank, (uid, pts) in enumerate(sorted_scores, 1):
        name = quiz["players"][uid]
        medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
        score_board += f"{medal} **{name}** — `{pts} points`\n"

        # Distribute Rewards (XP & Coins based on rank/points)
        is_winner = (rank == 1 and pts > 0)
        await record_progression(
            uid,
            chat_id,
            xp=300 if is_winner else (150 if pts > 0 else 50),
            coins=120 if is_winner else (50 if pts > 0 else 10),
            won_mode="quiz" if is_winner else None,
        )

    await message.answer(
        f"🏆 **ANIME QUIZ — FINAL RESULTS**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{score_board}\n\n"
        f"🎁 Rewards and XP have been distributed to all participants!",
        parse_mode="Markdown",
    )
    
