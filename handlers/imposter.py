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
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 **Host:** {host_mention}\n"
        f"👥 **Agents Joined ({len(players_dict)}/10):** (Min 3 required)\n"
        f"{player_list}\n\n"
        "⚠️ *Every player must start the bot privately first so secret characters can be delivered via DM!*\n\n"
        "👉 Type `/join` to enter • `/startgame` to begin!"
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

    args = message.text.split()
    mode = args[1].lower() if len(args) > 1 and args[1].lower() in {"classic", "double", "blind"} else "classic"
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    IMPOSTER_LOBBIES[chat_id] = {
        "host": message.from_user.id,
        "host_name": message.from_user.full_name,
        "mode": mode,
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
        players_dict=IMPOSTER_LOBBIES[chat_id]["players"],
    )
    await message.answer(lobby_text, parse_mode="Markdown")


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
    lobby["alive"] = set(player_ids)

    imp_count = 2 if (lobby["mode"] == "double" and len(player_ids) >= 5) else 1
    imposters = set(random.sample(player_ids, k=imp_count))
    lobby["imposters"] = imposters

    crew_char, imp_char = random.sample(ANIME_CHARACTERS, k=2)
    lobby["crew_char"] = crew_char
    lobby["imp_char"] = imp_char

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

    asyncio.create_task(run_imposter_phases(message, chat_id))


async def run_imposter_phases(message: Message, chat_id: int):
    lobby = IMPOSTER_LOBBIES.get(chat_id)
    if not lobby:
        return

    await message.answer(
        "📩 **SECRET ANIME CHARACTERS SENT VIA DM!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Check your private messages! Each round, describe your character in chat (or lock in a clue with `/hint`) before voting begins.",
        parse_mode="Markdown",
    )

    while chat_id in IMPOSTER_LOBBIES:
        lobby["round_num"] += 1
        lobby["phase"] = "DESCRIBING"
        lobby["hints"] = {}
        lobby["votes"] = {}

        alive_mentions = ", ".join(
            f"[{lobby['players'][uid]}](tg://user?id={uid})" for uid in lobby["alive"]
        )

        await message.answer(
            f"🗣️ **ROUND {lobby['round_num']} — CHARACTER DESCRIPTION (45s)**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Alive Players ({len(lobby['alive'])}):** {alive_mentions}\n\n"
            f"Describe your character in the chat now! (Optional: `/hint your clue`)",
            parse_mode="Markdown",
        )
        await asyncio.sleep(45)
        if chat_id not in IMPOSTER_LOBBIES:
            return

        if lobby["hints"]:
            hint_lines = "\n".join(
                f"• **{lobby['players'][uid]}:** _{clue}_" for uid, clue in lobby["hints"].items() if uid in lobby["alive"]
            )
            await message.answer(f"📝 **Locked-In Clues:**\n{hint_lines}", parse_mode="Markdown")

        lobby["phase"] = "VOTING"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"🗳️ Vote {lobby['players'][uid]}", callback_data=f"impvote:{chat_id}:{uid}")]
                for uid in lobby["alive"]
            ]
        )
        await message.answer(
            f"🗳️ **ROUND {lobby['round_num']} — ELIMINATION VOTING (30s)**\n"
            f"Who is describing a different character? Tap below to vote!",
            reply_markup=kb,
            parse_mode="Markdown",
        )
        await asyncio.sleep(30)
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
            return await finalize_imposter_match(message, chat_id, crew_won=True)

        if len(alive_imps) >= len(alive_crew):
            return await finalize_imposter_match(message, chat_id, crew_won=False)

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
        f"🏆 **{'CREWMATES WIN! All Imposters caught!' if crew_won else 'IMPOSTERS WIN! They outlasted the Crew!'}**\n\n"
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
        
