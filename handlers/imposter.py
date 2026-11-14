import asyncio
import random
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatType
from database import ensure_user, record_progression

router = Router()

IMPOSTER_LOBBIES: dict[int, dict] = {}

# 1,000+ Unique Anime Characters Pool
ANIME_CHARACTERS = [
    # Naruto & Boruto (80)
    "Naruto Uzumaki", "Sasuke Uchiha", "Sakura Haruno", "Kakashi Hatake", "Itachi Uchiha",
    "Madara Uchiha", "Obito Uchiha", "Minato Namikaze", "Kushina Uzumaki", "Jiraiya",
    "Tsunade", "Orochimaru", "Nagato Uzumaki", "Pain", "Konan",
    "Kisame Hoshigaki", "Deidara", "Sasori", "Hidan", "Kakuzu",
    "Zetsu", "Gaara", "Temari", "Kankuro", "Rock Lee",
    "Neji Hyuga", "Hinata Hyuga", "Tenten", "Might Guy", "Shikamaru Nara",
    "Ino Yamanaka", "Choji Akimichi", "Asuma Sarutobi", "Kurenai Yuhi", "Kiba Inuzuka",
    "Shino Aburame", "Hiruzen Sarutobi", "Tobirama Senju", "Hashirama Senju", "Danzo Shimura",
    "Killer Bee", "A (Fourth Raikage)", "Mei Terumi", "Onoki", "Kabuto Yakushi",
    "Suigetsu Hozuki", "Karin", "Jugo", "Zabuza Momochi", "Haku",
    "Shisui Uchiha", "Rin Nohara", "Iruka Umino", "Konohamaru Sarutobi", "Yamato",
    "Sai", "Kaguya Otsutsuki", "Hagoromo Otsutsuki", "Hamura Otsutsuki", "Indra Otsutsuki",
    "Ashura Otsutsuki", "Momoshiki Otsutsuki", "Kinshiki Otsutsuki", "Isshiki Otsutsuki", "Boruto Uzumaki",
    "Sarada Uchiha", "Mitsuki", "Kawaki", "Himawari Uzumaki", "Shikadai Nara",
    "Inojin Yamanaka", "Chocho Akimichi", "Metal Lee", "Sumire Kakei", "Mirai Sarutobi",
    "Hanabi Hyuga", "Hiashi Hyuga", "Kurama", "Gyuki", "Shukaku",

    # One Piece (100)
    "Monkey D. Luffy", "Roronoa Zoro", "Nami", "Usopp", "Sanji",
    "Tony Tony Chopper", "Nico Robin", "Franky", "Brook", "Jinbe",
    "Portgas D. Ace", "Sabo", "Shanks", "Marshall D. Teach (Blackbeard)", "Edward Newgate (Whitebeard)",
    "Kaido", "Charlotte Linlin (Big Mom)", "Gol D. Roger", "Silvers Rayleigh", "Kozuki Oden",
    "Trafalgar D. Water Law", "Eustass Kid", "Killer", "Bepo", "Jewelry Bonney",
    "Capone Bege", "Basil Hawkins", "X Drake", "Scratchmen Apoo", "Urouge",
    "Dracule Mihawk", "Boa Hancock", "Donquixote Doflamingo", "Crocodile", "Bartholomew Kuma",
    "Gecko Moria", "Buggy the Clown", "Smoker", "Tashigi", "Koby",
    "Helmeppo", "Monkey D. Garp", "Monkey D. Dragon", "Sengoku", "Sakazuki (Akainu)",
    "Kuzan (Aokiji)", "Borsalino (Kizaru)", "Issho (Fujitora)", "Aramaki (Ryokugyu)", "Rob Lucci",
    "Kaku", "Kalifa", "Spandam", "Enel", "Vivi Nefertari",
    "Karoo", "Sir Crocodile", "Mr. 2 Bon Clay", "Mr. 3 Galdino", "Ivankov",
    "Inazuma", "Magellan", "Hannyabal", "Shiryu", "Marco the Phoenix",
    "Jozu", "Vista", "Izo", "Yamato", "Momonosuke",
    "Kin'emon", "Kanjuro", "Raizo", "Kikunojo", "Ashura Doji",
    "Denjiro", "Kawamatsu", "Inuarashi", "Nekomamushi", "Carrot",
    "Pedro", "Charlotte Katakuri", "Charlotte Perospero", "Charlotte Smoothie", "Charlotte Cracker",
    "Charlotte Pudding", "Vinsmoke Judge", "Vinsmoke Reiju", "Vinsmoke Ichiji", "Vinsmoke Niji",
    "Vinsmoke Yonji", "Caesar Clown", "Vergo", "Monet", "Sugar",
    "Senor Pink", "Bartolomeo", "Cavendish", "Rebecca", "Kyros",

    # Bleach (70)
    "Ichigo Kurosaki", "Rukia Kuchiki", "Orihime Inoue", "Uryu Ishida", "Yasutora Sado (Chad)",
    "Renji Abarai", "Byakuya Kuchiki", "Toshiro Hitsugaya", "Kenpachi Zaraki", "Yachiru Kusajishi",
    "Sosuke Aizen", "Gin Ichimaru", "Kaname Tosen", "Kisuke Urahara", "Yoruichi Shihoin",
    "Shunsui Kyoraku", "Jushiro Ukitake", "Genryusai Shigekuni Yamamoto", "Retsu Unohana", "Soi Fon",
    "Mayuri Kurotsuchi", "Nemu Kurotsuchi", "Sajin Komamura", "Izuru Kira", "Shuhei Hisagi",
    "Rangiku Matsumoto", "Ikkaku Madarame", "Yumichika Ayasegawa", "Momo Hinamori", "Nanao Ise",
    "Shinji Hirako", "Hiyori Sarugaki", "Kensei Muguruma", "Rojuro Otoribashi", "Love Aikawa",
    "Mashiro Kuna", "Hachigen Ushoda", "Lisa Yadomaru", "Ulquiorra Cifer", "Grimmjow Jaegerjaquez",
    "Coyote Starrk", "Baraggan Louisenbairn", "Tier Harribel", "Nnoitra Gilga", "Szayelaporro Granz",
    "Zommari Rureaux", "Aaroniero Arruruerie", "Yammy Llargo", "Nelliel Tu Odelschwanck", "Luppi Antenor",
    "Yhwach", "Jugram Haschwalth", "Uryu Ishida", "Bazz-B", "Askin Nakk Le Vaar",
    "Bambietta Basterbine", "Gremmy Thoumeaux", "Lille Barro", "Gerard Valkyrie", "Pernida Parnkgjas",
    "As Nodt", "Giselle Gewelle", "Candice Catnipp", "Meninas McAllon", "Liltotto Lamperd",
    "Isshin Kurosaki", "Masaki Kurosaki", "Karin Kurosaki", "Yuzu Kurosaki", "Kon",

    # Dragon Ball (60)
    "Son Goku", "Vegeta", "Son Gohan", "Piccolo", "Future Trunks",
    "Krillin", "Bulma", "Chi-Chi", "Master Roshi", "Yamcha",
    "Tien Shinhan", "Chiaotzu", "Android 18", "Android 17", "Android 16",
    "Cell", "Frieza", "Majin Buu", "Kid Buu", "Super Buu",
    "Mr. Satan (Hercule)", "Videl", "Goten", "Trunks", "Gotenks",
    "Vegito", "Gogeta", "Beerus", "Whis", "Champa",
    "Vados", "Zeno", "Grand Priest", "Jiren", "Toppo",
    "Dyspo", "Hit", "Cabba", "Caulifla", "Kale",
    "Kefla", "Goku Black", "Zamasu", "Fused Zamasu", "Broly",
    "Paragus", "Bardock", "Gine", "Raditz", "Nappa",
    "Captain Ginyu", "Recoome", "Burter", "Jeice", "Guldo",
    "Dabura", "Babidi", "Supreme Kai (Shin)", "Kibito", "Pan",

    # Jujutsu Kaisen (50)
    "Yuji Itadori", "Megumi Fushiguro", "Nobara Kugisaki", "Satoru Gojo", "Ryomen Sukuna",
    "Yuta Okkotsu", "Maki Zenin", "Toge Inumaki", "Panda", "Kento Nanami",
    "Suguru Geto", "Kenjaku", "Mahito", "Jogo", "Hanami",
    "Dagon", "Choso", "Eso", "Kechizu", "Toji Fushiguro",
    "Mei Mei", "Ui Ui", "Aoi Todo", "Mai Zenin", "Kasumi Miwa",
    "Kokichi Muta (Mechamaru)", "Noritoshi Kamo", "Momo Nishimiya", "Utahime Iori", "Masamichi Yaga",
    "Shoko Ieiri", "Yoshinobu Gakuganji", "Naobito Zenin", "Naoya Zenin", "Jinichi Zenin",
    "Ogi Zenin", "Rika Orimoto", "Kinji Hakari", "Kirara Hoshi", "Hiromi Higuruma",
    "Hajime Kashimo", "Ryu Ishigori", "Takako Uro", "Hana Kurusu", "Angel",
    "Uraume", "Tengen", "Yuki Tsukumo", "Takuma Ino", "Atsuya Kusakabe",

    # Demon Slayer (50)
    "Tanjiro Kamado", "Nezuko Kamado", "Zenitsu Agatsuma", "Inosuke Hashibira", "Giyu Tomioka",
    "Shinobu Kocho", "Kyojuro Rengoku", "Tengen Uzui", "Mitsuri Kanroji", "Muichiro Tokito",
    "Gyomei Himejima", "Obanai Iguro", "Sanemi Shinazugawa", "Kanao Tsuyuri", "Genya Shinazugawa",
    "Kagaya Ubuyashiki", "Amane Ubuyashiki", "Sakonji Urokodaki", "Jigoro Kuwajima", "Hotaru Haganezuka",
    "Aoi Kanzaki", "Sabito", "Makomo", "Yoriichi Tsugikuni", "Muzan Kibutsuji",
    "Kokushibo", "Doma", "Akaza", "Hantengu", "Gyokko",
    "Gyutaro", "Daki", "Kaigaku", "Nakime", "Enmu",
    "Rui", "Susamaru", "Yahaba", "Kyogai", "Tamayo",
    "Yushiro", "Murata", "Suma", "Makio", "Hinatsuru",
    "Senjuro Rengoku", "Shinjuro Rengoku", "Kanae Kocho", "Goto", "Chuntaro",

    # Attack on Titan (50)
    "Eren Yeager", "Mikasa Ackerman", "Armin Arlert", "Levi Ackerman", "Erwin Smith",
    "Hange Zoe", "Jean Kirstein", "Connie Springer", "Sasha Blouse", "Historia Reiss",
    "Ymir", "Reiner Braun", "Bertholdt Hoover", "Annie Leonhart", "Zeke Yeager",
    "Pieck Finger", "Porco Galliard", "Marcel Galliard", "Falco Grice", "Gabi Braun",
    "Colt Grice", "Udo", "Zofia", "Theo Magath", "Willy Tybur",
    "Lara Tybur", "Grisha Yeager", "Carla Yeager", "Dina Fritz", "Eren Kruger",
    "Kenny Ackerman", "Uri Reiss", "Rod Reiss", "Frieda Reiss", "Floch Forster",
    "Hitch Dreyse", "Marlowe Freudenberg", "Petra Ral", "Oluo Bozado", "Eld Jinn",
    "Gunther Schultz", "Mike Zacharias", "Nanaba", "Gelgar", "Moblit Berner",
    "Keith Shadis", "Dot Pixis", "Nile Dok", "Darius Zackly", "Ymir Fritz",

    # My Hero Academia (60)
    "Izuku Midoriya", "Katsuki Bakugo", "Shoto Todoroki", "Ochaco Uraraka", "Tenya Iida",
    "All Might", "Shota Aizawa (Eraser Head)", "Eijiro Kirishima", "Momo Yaoyorozu", "Denki Kaminari",
    "Tsuyu Asui", "Fumikage Tokoyami", "Kyoka Jiro", "Mina Ashido", "Hanta Sero",
    "Mashirao Ojiro", "Toru Hagakure", "Mezo Shoji", "Koji Koda", "Rikido Sato",
    "Yuga Aoyama", "Minoru Mineta", "Mirio Togata", "Nejire Hado", "Tamaki Amajiki",
    "Hitoshi Shinso", "Mei Hatsume", "Endeavor", "Hawks", "Best Jeanist",
    "Edgeshot", "Mirko", "Crust", "Kamui Woods", "Mt. Lady",
    "Gran Torino", "Sir Nighteye", "Fat Gum", "Gang Orca", "Present Mic",
    "Midnight", "Cementoss", "Ectoplasm", "Recovery Girl", "Principal Nezu",
    "Tomura Shigaraki", "All For One", "Dabi", "Himiko Toga", "Twice",
    "Spinner", "Mr. Compress", "Kurogiri", "Gigantomachia", "Overhaul",
    "Eri", "Stain", "Gentle Criminal", "La Brava", "Lady Nagant",

    # Hunter x Hunter (40)
    "Gon Freecss", "Killua Zoldyck", "Kurapika", "Leorio Paradinight", "Hisoka Morow",
    "Illumi Zoldyck", "Chrollo Lucilfer", "Isaac Netero", "Meruem", "Neferpitou",
    "Shaiapouf", "Menthuthuyoupi", "Komugi", "Biscuit Krueger", "Kite",
    "Knuckle Bine", "Shoot McMahon", "Morel Mackernasey", "Knov", "Palm Siberia",
    "Feitan Portor", "Phinks Magcub", "Shalnark", "Machi Komacine", "Nobunaga Hazama",
    "Uvogin", "Pakunoda", "Franklin Bordeau", "Shizuku Murasaki", "Bonolenov Ndongo",
    "Kortopi", "Silva Zoldyck", "Zeno Zoldyck", "Kikyo Zoldyck", "Milluki Zoldyck",
    "Alluka Zoldyck", "Kalluto Zoldyck", "Ging Freecss", "Pariston Hill", "Razor",

    # Fullmetal Alchemist (35)
    "Edward Elric", "Alphonse Elric", "Winry Rockbell", "Roy Mustang", "Riza Hawkeye",
    "Maes Hughes", "Alex Louis Armstrong", "Olivier Mira Armstrong", "Scar", "Izumi Curtis",
    "Sig Curtis", "Van Hohenheim", "Trisha Elric", "Pinako Rockbell", "Ling Yao",
    "Lan Fan", "Fu", "May Chang", "Shao May", "King Bradley (Wrath)",
    "Selim Bradley (Pride)", "Lust", "Gluttony", "Envy", "Greed",
    "Sloth", "Father", "Solf J. Kimblee", "Jean Havoc", "Heymans Breda",
    "Vato Falman", "Kain Fuery", "Maria Ross", "Denny Brosh", "Barry the Chopper",

    # Death Note & Code Geass (35)
    "Light Yagami", "L Lawliet", "Misa Amane", "Ryuk", "Rem",
    "Near", "Mello", "Soichiro Yagami", "Touta Matsuda", "Shuichi Aizawa",
    "Kanzo Mogi", "Hideki Ide", "Watari", "Teru Mikami", "Kiyomi Takada",
    "Naomi Misora", "Raye Penber", "Lelouch vi Britannia", "C.C.", "Suzaku Kururugi",
    "Kallen Stadtfeld", "Nunnally vi Britannia", "Shirley Fenette", "Milly Ashford", "Rivalz Cardemonde",
    "Nina Einstein", "Rolo Lamperouge", "Jeremiah Gottwald", "Cornelia li Britannia", "Euphemia li Britannia",
    "Schneizel el Britannia", "Charles zi Britannia", "V.V.", "Marianne vi Britannia", "Diethard Ried",

    # Tokyo Ghoul & Chainsaw Man (45)
    "Ken Kaneki", "Touka Kirishima", "Rize Kamishiro", "Hideyoshi Nagachika", "Juuzou Suzuya",
    "Kishou Arima", "Kotaro Amon", "Akira Mado", "Kureo Mado", "Shuu Tsukiyama",
    "Hinami Fueguchi", "Yoshimura", "Renji Yomo", "Uta", "Itori",
    "Nishiki Nishio", "Eto Yoshimura", "Tatara", "Noro", "Ayato Kirishima",
    "Yakumo Oomori (Jason)", "Nimura Furuta", "Haise Sasaki", "Kuki Urie", "Ginshi Shirazu",
    "Tooru Mutsuki", "Saiko Yonebayashi", "Denji", "Pochita", "Makima",
    "Aki Hayakawa", "Power", "Himeno", "Kobeni Higashiyama", "Hirokazu Arai",
    "Kishibe", "Angel Devil", "Beam", "Galgali (Violence Fiend)", "Prinz",
    "Quanxi", "Reze", "Santa Claus", "Katana Man", "Asa Mitaka",

    # Black Clover & Fairy Tail (60)
    "Asta", "Yuno Grinberryall", "Noelle Silva", "Yami Sukehiro", "Luck Voltia",
    "Magna Swing", "Vanessa Enoteca", "Finral Roulacase", "Charmy Pappitson", "Gauche Adlai",
    "Grey", "Gordon Agrippa", "Henry Legolant", "Zora Ideale", "Secre Swallowtail (Nero)",
    "Julius Novachrono", "Fuegoleon Vermillion", "Mereoleona Vermillion", "Leopold Vermillion", "Nozel Silva",
    "Solid Silva", "Nebra Silva", "Charlotte Roselei", "Jack the Ripper", "Rill Boismortier",
    "William Vangeance", "Langris Vaude", "Mimosa Vermillion", "Klaus Lunettes", "Liebe",
    "Natsu Dragneel", "Lucy Heartfilia", "Happy", "Gray Fullbuster", "Erza Scarlet",
    "Wendy Marvell", "Carla", "Gajeel Redfox", "Pantherlily", "Juvia Lockser",
    "Laxus Dreyar", "Mirajane Strauss", "Elfman Strauss", "Lisanna Strauss", "Makarov Dreyar",
    "Gildarts Clive", "Cana Alberona", "Levy McGarden", "Freed Justine", "Evergreen",
    "Bickslow", "Jellal Fernandes", "Ultear Milkovich", "Meredy", "Zeref Dragneel",
    "Mavis Vermillion", "Acnologia", "Igneel", "Sting Eucliffe", "Rogue Cheney",

    # Sword Art Online & Re:Zero (45)
    "Kirito (Kazuto Kirigaya)", "Asuna Yuuki", "Leafa (Suguha Kirigaya)", "Sinon (Shino Asada)", "Klein",
    "Agil", "Silica", "Lisbeth", "Yui", "Eugeo",
    "Alice Zuberg", "Akihiko Kayaba", "Heathcliff", "Oberon", "Death Gun",
    "Yuuki Konno", "Quinella (Administrator)", "Bercouli Synthesis One", "Subtlety", "Mito",
    "Subaru Natsuki", "Emilia", "Rem", "Ram", "Beatrice",
    "Roswaal L. Mathers", "Puck", "Felt", "Reinhard van Astrea", "Crusch Karsten",
    "Felix Argyle", "Wilhelm van Astrea", "Anastasia Hoshin", "Julius Juukulius", "Priscilla Barielle",
    "Aldebaran", "Echidna", "Satella", "Petelgeuse Romanee-Conti", "Regulus Corneas",
    "Garfiel Tinsel", "Frederica Baumann", "Otto Suwen", "Petra Leyte", "Elsa Granhiert",

    # JoJo's Bizarre Adventure (45)
    "Jonathan Joestar", "Dio Brando", "Joseph Joestar", "Caesar Anthonio Zeppeli", "Lisa Lisa",
    "Kars", "Esidisi", "Wamuu", "Rudol von Stroheim", "Jotaro Kujo",
    "Noriaki Kakyoin", "Jean Pierre Polnareff", "Muhammad Avdol", "Iggy", "Hol Horse",
    "Josuke Higashikata", "Okuyasu Nijimura", "Koichi Hirose", "Rohan Kishibe", "Yoshikage Kira",
    "Reimi Sugimoto", "Giorno Giovanna", "Bruno Bucciarati", "Guido Mista", "Narancia Ghirga",
    "Leone Abbacchio", "Pannacotta Fugo", "Trish Una", "Diavolo", "Vinegar Doppio",
    "Jolyne Cujoh", "Ermes Costello", "Foo Fighters", "Weather Report", "Narciso Anasui",
    "Emporio Alnino", "Enrico Pucci", "Johnny Joestar", "Gyro Zeppeli", "Diego Brando",
    "Funny Valentine", "Josuke Higashikata (Gappy)", "Yasuho Hirose", "Tooru", "Speedwagon",

    # One Punch Man & Mob Psycho 100 (35)
    "Saitama", "Genos", "Tatsumaki (Terrible Tornado)", "Fubuki (Blizzard of Hell)", "King",
    "Bang (Silver Fang)", "Bomb", "Atomic Samurai", "Child Emperor", "Metal Knight",
    "Zombieman", "Drive Knight", "Pig God", "Superalloy Darkshine", "Watchdog Man",
    "Flashy Flash", "Tanktop Master", "Metal Bat", "Puri-Puri Prisoner", "Mumen Rider",
    "Speed-o'-Sound Sonic", "Garou", "Lord Boros", "Psyko", "Orochi",
    "Shigeo Kageyama (Mob)", "Arataka Reigen", "Dimple", "Ritsu Kageyama", "Teruki Hanazawa",
    "Tome Kurata", "Tsubomi Takane", "Sho Suzuki", "Toichiro Suzuki", "Katsuya Serizawa",

    # Isekai Quartet: Konosuba, Overlord, Slime, Shield Hero (60)
    "Kazuma Satou", "Aqua", "Megumin", "Darkness", "Wiz",
    "Yunyun", "Vanir", "Chris", "Eris", "Chomusuke",
    "Ainz Ooal Gown", "Albedo", "Shalltear Bloodfallen", "Demiurge", "Cocytus",
    "Aura Bella Fiora", "Mare Bello Fiore", "Sebas Tian", "Pandora's Actor", "Narberal Gamma",
    "Yuri Alpha", "Lupusregina Beta", "CZ2128 Delta", "Solution Epsilon", "Entoma Vasilissa Zeta",
    "Gazef Stronoff", "Brain Unglaus", "Climb", "Renner", "Momon",
    "Rimuru Tempest", "Veldora Tempest", "Shion", "Benimaru", "Shuna",
    "Souei", "Hakurou", "Kurobe", "Gobta", "Ranga",
    "Milim Nava", "Diablo", "Shizue Izawa", "Guy Crimson", "Leon Cromwell",
    "Ramiris", "Luminous Valentine", "Hinatas Sakaguchi", "Gabiru", "Geld",
    "Naofumi Iwatani", "Raphtalia", "Filo", "Melty Q. Melromarc", "Motoyasu Kitamura",
    "Ren Amaki", "Itsuki Kawasumi", "Mirellia Q. Melromarc", "Glass", "Fitoria",

    # Fate, Evangelion, Cowboy Bebop, Berserk, Vinland Saga (65)
    "Saber (Artoria Pendragon)", "Shirou Emiya", "Rin Tohsaka", "Archer (EMIYA)", "Gilgamesh",
    "Lancer (Cu Chulainn)", "Rider (Medusa)", "Caster (Medea)", "Berserker (Heracles)", "Illyasviel von Einzbern",
    "Kirei Kotomine", "Kiritsugu Emiya", "Irisviel von Einzbern", "Iskandar", "Waver Velvet",
    "Jeanne d'Arc", "Astolfo", "Mordred", "Karna", "Siegfried",
    "Shinji Ikari", "Rei Ayanami", "Asuka Langley Soryu", "Misato Katsuragi", "Kaworu Nagisa",
    "Gendo Ikari", "Ritsuko Akagi", "Mari Illustrious Makinami", "Toji Suzuhara", "Kensuke Aida",
    "Spike Spiegel", "Jet Black", "Faye Valentine", "Edward Wong Hau Pepelu Tivrusky IV", "Ein",
    "Vicious", "Julia", "Guts", "Griffith", "Casca",
    "Puck (Berserk)", "Farnese", "Serpico", "Isidro", "Schierke",
    "Skull Knight", "Zodd", "Judeau", "Pippin", "Corkus",
    "Thorfinn", "Askeladd", "Thors", "Canute", "Thorkell",
    "Bjorn", "Floki", "Einar", "Arnheid", "Ketil",
    "Snake", "Leif Erikson", "Ylva", "Helga", "Gardar",

    # Sports & Modern Hits: Haikyuu, Blue Lock, Spy x Family, Frieren, Solo Leveling (65)
    "Shoyo Hinata", "Tobio Kageyama", "Daichi Sawamura", "Koshi Sugawara", "Asahi Azumane",
    "Yu Nishinoya", "Ryunosuke Tanaka", "Kei Tsukishima", "Tadashi Yamaguchi", "Toru Oikawa",
    "Hajime Iwaizumi", "Kenma Kozume", "Tetsuro Kuroo", "Kotaro Bokuto", "Keiji Akaashi",
    "Wakatoshi Ushijima", "Satori Tendo", "Atsumu Miya", "Osamu Miya", "Shinsuke Kita",
    "Yoichi Isagi", "Meguru Bachira", "Rensuke Kunigami", "Hyoma Chigiri", "Shoei Barou",
    "Seishiro Nagi", "Reo Mikage", "Rin Itoshi", "Sae Itoshi", "Jinpachi Ego",
    "Loid Forger (Twilight)", "Yor Forger (Thorn Princess)", "Anya Forger", "Bond Forger", "Yuri Briar",
    "Damian Desmond", "Becky Blackbell", "Franky Franklin", "Sylvia Sherwood", "Henry Henderson",
    "Frieren", "Fern", "Stark", "Himmel", "Heiter",
    "Eisen", "Serie", "Flamme", "Aura the Guillotine", "Ubel",
    "Land", "Denken", "Sein", "Kraft", "Lugner",
    "Sung Jinwoo", "Cha Hae-In", "Yoo Jinho", "Choi Jong-In", "Baek Yoonho",
    "Go Gunhee", "Woo Jinchul", "Igris", "Beru", "Tusk",

    # Classics & Others: Gintama, Soul Eater, Fire Force, Dr. Stone, Bungo Stray Dogs, Classroom of the Elite (60)
    "Gintoki Sakata", "Shinpachi Shimura", "Kagura", "Sadaharu", "Toshiro Hijikata",
    "Sougo Okita", "Isao Kondo", "Kotaro Katsura", "Elizabeth", "Shinsuke Takasugi",
    "Maka Albarn", "Soul Eater Evans", "Black Star", "Tsubaki Nakatsukasa", "Death the Kid",
    "Liz Thompson", "Patty Thompson", "Franken Stein", "Lord Death", "Crona",
    "Shinra Kusakabe", "Arthur Boyle", "Tamaki Kotatsu", "Maki Oze", "Takehisa Hinawa",
    "Akitaru Obi", "Iris", "Benimaru Shinmon", "Joker", "Sho Kusakabe",
    "Senku Ishigami", "Taiju Oki", "Yuzuriha Ogawa", "Tsukasa Shishio", "Gen Asagiri",
    "Kohaku", "Chrome", "Suika", "Kinro", "Ginro",
    "Atsushi Nakajima", "Osamu Dazai", "Doppo Kunikida", "Ranpo Edogawa", "Akiko Yosano",
    "Kenji Miyazawa", "Kyoka Izumi", "Yukichi Fukuzawa", "Ryunosuke Akutagawa", "Chuya Nakahara",
    "Kiyotaka Ayanokoji", "Suzune Horikita", "Kikyo Kushida", "Kei Karuizawa", "Honami Ichinose",
    "Arisu Sakayanagi", "Kakeru Ryuen", "Rokusuke Koenji", "Ken Sudo", "Yosuke Hirata",
]


def is_group_chat(message: Message) -> bool:
    return message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]


def get_imposter_lobby_text(host_name: str, host_id: int, mode: str, players_dict: dict) -> str:
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
        f"👥 **Agents Joined ({len(players_dict)}/10):** (Min 3 required)\n"
        f"{player_list}\n\n"
        f"⚠️ *Every player must start the bot privately first so secret characters can be d
