# ──────────────────────────────────────────────
# GamePulse — Main Application (فاز ۳ — نسخه نهایی)
# معماری: On-Demand + category-aware + dedup + proxy
# ──────────────────────────────────────────────

from flask import Flask, render_template, jsonify, request
import sqlite3
import hashlib
import threading
import time
import re
import os
from datetime import datetime, timedelta
from feeds import GAMING_FEEDS, PLATFORM_KEYWORDS, VIDEO_KEYWORDS, CONTENT_TYPE_KEYWORDS

# سنگین‌ها lazy load میشن
feedparser = None
req = None
GoogleTranslator = None

def _import_feedparser():
    global feedparser
    if feedparser is None:
        import feedparser as _fp
        feedparser = _fp

def _import_requests():
    global req
    if req is None:
        import requests as _req
        req = _req

def _import_translator():
    global GoogleTranslator
    if GoogleTranslator is None:
        from deep_translator import GoogleTranslator as _gt
        GoogleTranslator = _gt

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "database", "gamepulse.db")

# ──────── پروکسی ────────
PROXY_URL = os.environ.get('PROXY_URL', '')
PROXIES   = {'http': PROXY_URL, 'https': PROXY_URL} if PROXY_URL else {}

# ──────── متغیرهای لایو ────────
last_update_time     = None
new_articles_count   = 0
last_urgent_articles = []
trends_cache         = {}
trends_last_update   = None

# ──────── زمان‌بندی ────────
_last_feed_fetch   = 0
_last_translation  = 0
_last_trends_fetch = 0

FEED_INTERVAL      = 120
TRANSLATE_INTERVAL = 30
TRENDS_INTERVAL    = 7200

# ──────── فلگ‌های ایمن ────────
_feed_running      = False
_translate_running = False
_trends_running    = False
_feed_started_at   = 0
_translate_started = 0
_trends_started    = 0
_MAX_RUN_TIME      = 600

# ──────── رتبه‌بندی اعتبار منابع ────────
SOURCE_AUTHORITY = {
    'IGN': 1, 'IGN Reviews': 1,
    'GameSpot': 1, 'GameSpot Reviews': 1,
    'PlayStation Blog': 1, 'Xbox Wire': 1,
    'Kotaku': 2,
    'Polygon': 2, 'Polygon Reviews': 2,
    'PC Gamer': 2, 'PC Gamer Reviews': 2, 'PC Gamer Features': 2,
    'Eurogamer': 2,
    'GamesRadar': 3,
    'VG247': 3, 'VG247 Reviews': 3,
    'VGC': 3, 'Gematsu': 3,
    'Push Square': 3, 'Push Square Reviews': 3,
    'Push Square Features': 3, 'Push Square Guides': 3,
    'Pure Xbox': 3, 'Pure Xbox Reviews': 3,
    'Pure Xbox Features': 3, 'Pure Xbox Guides': 3,
    'Nintendo Life': 3, 'Nintendo Life Reviews': 3,
    'Nintendo Life Features': 3, 'Nintendo Life Guides': 3,
    'Rock Paper Shotgun': 3, 'RPS Reviews': 3, 'RPS Deals': 3,
    'Game Rant': 4, 'Game Rant Reviews': 4, 'Game Rant Guides': 4,
    'TheGamer': 4, 'TheGamer Guides': 4, 'TheGamer Features': 4,
    'DualShockers': 4, 'DualShockers Reviews': 4,
    'DualShockers Guides': 4, 'DualShockers Features': 4,
    'Wccftech': 4, 'Shacknews': 4, 'Shacknews Guides': 4,
    'PCGamesN': 4,
    'TouchArcade': 4, 'TouchArcade Reviews': 4,
    'Pocket Gamer': 4, 'Pocket Gamer iOS': 4,
    'Pocket Gamer Android': 4, 'Pocket Gamer Guides': 4,
    'GamingBolt News': 4, 'GamingBolt Articles': 4,
    'GamingBolt Reviews': 4, 'GamingBolt Guides': 4,
    'Screen Rant News': 4, 'Screen Rant Features': 4, 'Screen Rant Guides': 4,
    'MP1st': 5, 'DSOGaming': 5,
    'Game Developer': 5, 'GamesIndustry.biz': 5,
    'GamingDeals Reddit': 5, 'PS Deals Reddit': 5, 'Xbox Deals Reddit': 5,
}

DUPLICATE_THRESHOLD = 0.6
HOT_NEWS_THRESHOLD  = 4

GAME_NAMES = [
    "GTA VI", "GTA 6", "Grand Theft Auto", "Elden Ring", "Bloodborne",
    "God of War", "Spider-Man", "Marvel's Spider-Man", "The Last of Us",
    "Horizon", "Ghost of Tsushima", "Demon's Souls", "Ratchet & Clank",
    "Halo", "Forza", "Fable", "Avowed", "Indiana Jones", "Starfield",
    "Fallout", "Elder Scrolls", "Skyrim", "Doom", "Wolfenstein",
    "Zelda", "Mario", "Metroid", "Pokémon", "Pokemon", "Splatoon",
    "Animal Crossing", "Kirby", "Donkey Kong", "Fire Emblem",
    "Cyberpunk", "The Witcher", "Baldur's Gate", "Dragon Age",
    "Mass Effect", "Dead Space", "Resident Evil", "Devil May Cry",
    "Monster Hunter", "Street Fighter", "Final Fantasy", "Kingdom Hearts",
    "Dragon Ball", "Naruto", "One Piece", "Assassin's Creed",
    "Far Cry", "Watch Dogs", "Rainbow Six", "Call of Duty", "Warzone",
    "Battlefield", "FIFA", "EA FC", "NBA 2K", "Madden",
    "Apex Legends", "Fortnite", "PUBG", "Valorant", "Overwatch",
    "League of Legends", "Dota", "Counter-Strike", "CS2",
    "Minecraft", "Terraria", "Stardew Valley", "Hollow Knight",
    "Silksong", "Lies of P", "Stellar Blade", "Black Myth",
    "Wukong", "Death Stranding", "Silent Hill", "Metal Gear",
    "Castlevania", "Tekken", "Mortal Kombat",
    "Diablo", "Path of Exile", "World of Warcraft",
    "Destiny", "Returnal", "Deathloop", "Alan Wake",
    "Control", "Hellblade", "Senua's Saga",
    "Little Nightmares", "Plague Tale", "Kena", "Stray",
    "Cuphead", "Hades", "Disco Elysium", "Outer Wilds",
    "Batman", "Superman", "Star Wars", "Harry Potter", "Hogwarts Legacy",
]

STUDIO_PUBLISHER = [
    "Sony", "PlayStation Studios", "Naughty Dog", "Insomniac", "Guerrilla",
    "Santa Monica Studio", "Sucker Punch", "Bluepoint", "Housemarque",
    "Microsoft", "Xbox Game Studios", "Bethesda", "id Software",
    "MachineGames", "Arkane", "Obsidian", "Ninja Theory", "Rare",
    "Playground Games", "Turn 10", "Double Fine", "The Coalition",
    "Nintendo", "Game Freak", "HAL Laboratory", "Monolith Soft",
    "Retro Studios", "Intelligent Systems",
    "EA", "Electronic Arts", "DICE", "BioWare", "Respawn",
    "Ubisoft", "Massive", "Activision", "Blizzard",
    "Treyarch", "Infinity Ward", "Sledgehammer",
    "2K Games", "Rockstar", "Firaxis", "Gearbox",
    "Square Enix", "Crystal Dynamics", "Capcom", "FromSoftware",
    "Bandai Namco", "Konami", "Sega", "Atlus",
    "CD Projekt", "CD Projekt Red", "Larian Studios",
    "Devolver Digital", "Annapurna", "Epic Games", "Valve",
    "Take-Two", "Rocksteady", "Warner Bros", "WB Games",
    "miHoYo", "HoYoverse", "NetEase", "Tencent",
]

URGENCY_KEYWORDS = {
    "high": [
        "breaking", "exclusive", "just announced", "world premiere",
        "first look", "reveal", "leaked", "leak", "confirmed",
        "official", "release date", "launches today", "out now",
        "game of the year", "goty", "award", "banned", "controversy",
        "acquisition", "acquired", "shutdown", "closed", "bankrupt",
    ],
    "medium": [
        "announced", "revealed", "trailer", "gameplay", "preview",
        "hands-on", "review", "score", "update", "patch", "dlc",
        "expansion", "sequel", "remake", "remaster", "port",
    ],
}

# ──────────── دیتابیس ────────────

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def init_db():
    os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE,
            title TEXT,
            link TEXT,
            summary TEXT,
            summary_fa TEXT DEFAULT '',
            source TEXT,
            source_platform TEXT,
            detected_platforms TEXT,
            content_type TEXT,
            has_video INTEGER DEFAULT 0,
            image_url TEXT,
            published TEXT,
            fetched_at TEXT,
            is_read INTEGER DEFAULT 0,
            is_bookmarked INTEGER DEFAULT 0,
            custom_tag TEXT DEFAULT '',
            urgency TEXT DEFAULT 'normal',
            game_tags TEXT DEFAULT '',
            studio_tags TEXT DEFAULT '',
            duplicate_count INTEGER DEFAULT 1,
            related_sources TEXT DEFAULT '',
            is_primary INTEGER DEFAULT 1,
            parent_hash TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feed_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT UNIQUE,
            last_fetch TEXT,
            status TEXT,
            article_count INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS translation_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_hash TEXT UNIQUE,
            translated TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS custom_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            url TEXT,
            platform TEXT DEFAULT 'General',
            source_type TEXT DEFAULT 'general',
            feed_category TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            added_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wallpapers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            data TEXT,
            added_at TEXT
        )
    """)

    # اضافه کردن ستون feed_category اگه وجود نداره (برای DB قدیمی)
    try:
        conn.execute("ALTER TABLE custom_sources ADD COLUMN feed_category TEXT DEFAULT ''")
        conn.commit()
    except:
        pass

    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM custom_sources").fetchone()[0]
    if count == 0:
        for platform_name, platform_data in GAMING_FEEDS.items():
            for source_name, source_info in platform_data['sources'].items():
                conn.execute("""
                    INSERT OR IGNORE INTO custom_sources
                    (name, url, platform, source_type, feed_category, is_active, added_at)
                    VALUES (?,?,?,?,?,1,?)
                """, (
                    source_name,
                    source_info['url'],
                    platform_name,
                    platform_data['type'],
                    source_info.get('category', ''),
                    datetime.now().isoformat()
                ))
        conn.commit()
    else:
        # آپدیت feed_category برای منابع موجود
        for platform_name, platform_data in GAMING_FEEDS.items():
            for source_name, source_info in platform_data['sources'].items():
                conn.execute("""
                    UPDATE custom_sources SET feed_category=?, url=?
                    WHERE name=?
                """, (
                    source_info.get('category', ''),
                    source_info['url'],
                    source_name
                ))
        conn.commit()

    conn.close()

# ── همیشه اجرا میشه — هم لوکال هم سرور ──
init_db()

def get_active_sources():
    conn    = get_db()
    sources = conn.execute(
        "SELECT * FROM custom_sources WHERE is_active=1"
    ).fetchall()
    conn.close()
    return [dict(s) for s in sources]

# ──────────── تشخیص هوشمند ────────────

def detect_platforms(title, summary=""):
    text     = (title + " " + summary).lower()
    detected = []
    for platform, keywords in PLATFORM_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                detected.append(platform)
                break
    return detected if detected else ["General"]

def detect_content_type(title, summary=""):
    text = (title + " " + summary).lower()
    for content_type, keywords in CONTENT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return content_type
    return "news"

def detect_video(title, summary=""):
    text = (title + " " + summary).lower()
    for keyword in VIDEO_KEYWORDS:
        if keyword.lower() in text:
            return True
    return False

def detect_urgency(title, summary=""):
    text = (title + " " + summary).lower()
    for keyword in URGENCY_KEYWORDS["high"]:
        if keyword.lower() in text:
            return "high"
    for keyword in URGENCY_KEYWORDS["medium"]:
        if keyword.lower() in text:
            return "medium"
    return "normal"

def detect_games(title, summary=""):
    text  = title + " " + summary
    found = []
    for game in GAME_NAMES:
        if game.lower() in text.lower():
            found.append(game)
    return list(set(found))[:5]

def detect_studios(title, summary=""):
    text  = title + " " + summary
    found = []
    for studio in STUDIO_PUBLISHER:
        if studio.lower() in text.lower():
            found.append(studio)
    return list(set(found))[:5]

def extract_image(entry):
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0].get('url', '')
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                return enc.get('href', '')
    if hasattr(entry, 'content') and entry.content:
        html      = entry.content[0].get('value', '')
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        if img_match:
            return img_match.group(1)
    summary   = entry.get('summary', '')
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
    if img_match:
        return img_match.group(1)
    return ''

def clean_summary(summary):
    if not summary:
        return ""
    clean = re.sub(r'<[^>]+>', '', summary)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:300] + "..." if len(clean) > 300 else clean

def generate_hash(title, link):
    return hashlib.md5(f"{title}{link}".encode()).hexdigest()

# ──────────── تشخیص خبر تکراری ────────────

def normalize_title(title):
    title = title.lower().strip()
    title = re.sub(r'[^\w\s]', '', title)
    stop  = {
        'the','a','an','is','are','was','were','to','for',
        'in','on','at','by','with','from','and','or','but',
        'of','it','its','this','that','has','have','been',
        'will','be','can','could','would','should','may',
        'how','what','when','who','why','where','not','no',
    }
    return set(w for w in title.split() if w not in stop and len(w) > 2)

def title_similarity(title1, title2):
    w1 = normalize_title(title1)
    w2 = normalize_title(title2)
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / min(len(w1), len(w2))

def deduplicate_articles():
    conn    = get_db()
    cutoff  = (datetime.now() - timedelta(hours=6)).isoformat()
    rows    = conn.execute(
        "SELECT id, title, source, hash FROM articles WHERE fetched_at>? ORDER BY id",
        (cutoff,)
    ).fetchall()

    if not rows:
        conn.close()
        return

    articles = [dict(r) for r in rows]
    groups   = []
    used     = set()

    for art1 in articles:
        if art1['id'] in used:
            continue
        group = [art1]
        used.add(art1['id'])
        for art2 in articles:
            if art2['id'] in used or art1['source'] == art2['source']:
                continue
            if title_similarity(art1['title'], art2['title']) >= DUPLICATE_THRESHOLD:
                group.append(art2)
                used.add(art2['id'])
        groups.append(group)

    hot_count = dup_count = 0

    for group in groups:
        if len(group) == 1:
            conn.execute(
                "UPDATE articles SET is_primary=1, duplicate_count=1 WHERE id=?",
                (group[0]['id'],)
            )
            continue

        group.sort(key=lambda x: SOURCE_AUTHORITY.get(x['source'], 99))
        primary      = group[0]
        count        = len(group)
        source_names = [a['source'] for a in group]
        dup_count   += count - 1

        if count >= HOT_NEWS_THRESHOLD:
            conn.execute("""
                UPDATE articles SET is_primary=1, duplicate_count=?,
                    related_sources=?, urgency='high'
                WHERE id=?
            """, (count, ','.join(source_names), primary['id']))
            hot_count += 1
        else:
            conn.execute("""
                UPDATE articles SET is_primary=1, duplicate_count=?,
                    related_sources=?
                WHERE id=?
            """, (count, ','.join(source_names), primary['id']))

        for other in group[1:]:
            conn.execute("""
                UPDATE articles SET is_primary=0, parent_hash=?, duplicate_count=?
                WHERE id=?
            """, (primary['hash'], count, other['id']))

    conn.commit()
    conn.close()
    print(f"[DEDUP] ✅ {len(groups)} گروه | {dup_count} تکراری | {hot_count} داغ")

# ──────────── ترجمه ────────────

def translate_to_persian(text, article_hash):
    _import_translator()
    if not text or len(text) < 10:
        return ""
    try:
        conn   = get_db()
        cached = conn.execute(
            "SELECT translated FROM translation_cache WHERE original_hash=?",
            (article_hash,)
        ).fetchone()
        conn.close()
        if cached:
            return cached['translated']

        translated = GoogleTranslator(source='en', target='fa').translate(text[:200])

        conn = get_db()
        conn.execute(
            "INSERT OR IGNORE INTO translation_cache (original_hash, translated, created_at) VALUES (?,?,?)",
            (article_hash, translated, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return translated
    except:
        return ""

def translate_articles_background():
    try:
        conn     = get_db()
        articles = conn.execute(
            "SELECT id, hash, summary FROM articles "
            "WHERE summary_fa='' AND summary!='' AND is_primary=1 LIMIT 10"
        ).fetchall()
        conn.close()
        for article in articles:
            translated = translate_to_persian(article['summary'], article['hash'])
            if translated:
                conn = get_db()
                conn.execute(
                    "UPDATE articles SET summary_fa=? WHERE id=?",
                    (translated, article['id'])
                )
                conn.commit()
                conn.close()
            time.sleep(1)
    except Exception as e:
        print(f"[TRANSLATE ERROR] {e}")

# ──────────── Google Trends ────────────

def fetch_google_trends():
    global trends_cache, trends_last_update
    try:
        from trendspy import Trends  # ← اینجا import میشه نه موقع شروع
        print("[TRENDS] در حال دریافت Google Trends...")
        tr = Trends(request_delay=2.0)

        trend_data = {}
        try:
            keywords = ['gaming', 'video games', 'PlayStation', 'Xbox', 'Nintendo']
            interest = tr.interest_over_time(keywords, timeframe='now 7-d')
            if not interest.empty:
                for col in interest.columns:
                    if col != 'isPartial':
                        trend_data[col] = int(interest[col].mean())
        except Exception as e:
            print(f"[TRENDS] ترند جهانی: {e}")

        iran_trends = {}
        try:
            gaming_fa   = ['بازی', 'گیمینگ', 'پلی استیشن']
            interest_ir = tr.interest_over_time(gaming_fa, timeframe='now 7-d', geo='IR')
            if not interest_ir.empty:
                for col in interest_ir.columns:
                    if col != 'isPartial':
                        iran_trends[col] = int(interest_ir[col].mean())
        except Exception as e:
            print(f"[TRENDS] ترند ایران: {e}")

        related = []
        try:
            rq = tr.related_queries(
                'gaming', timeframe='now 7-d',
                headers={'referer': 'https://www.google.com/'}
            )
            if rq and 'top' in rq and rq['top'] is not None and not rq['top'].empty:
                related = rq['top'].head(10).to_dict('records')
        except Exception as e:
            print(f"[TRENDS] related queries: {e}")

        trends_cache = {
            'global'    : trend_data,
            'iran'      : iran_trends,
            'related'   : related,
            'updated_at': datetime.now().isoformat(),
        }
        trends_last_update = datetime.now()
        print("[TRENDS] ✅ آپدیت شد!")
    except Exception as e:
        print(f"[TRENDS ERROR] {e}")

# ──────────── دریافت فیدها ────────────

def fetch_single_feed(source_name, feed_url, platform_name, forced_category=''):
    _import_feedparser()
    _import_requests()
    articles = []

    # ── تأخیر برای Reddit (جلوگیری از 429) ──
    is_reddit = 'reddit.com' in feed_url
    if is_reddit:
        time.sleep(3)

    try:
        headers = {'User-Agent': 'GamePulse/1.0 (Gaming News Dashboard)'}
        try:
            if PROXIES.get('http'):
                response = req.get(feed_url, timeout=15, headers=headers, proxies=PROXIES)
            else:
                response = req.get(feed_url, timeout=15, headers=headers)

            if response.status_code == 429:
                print(f"  ⏳ {source_name}: rate limit — رد شد")
                return articles
            if response.status_code != 200:
                print(f"  ⚠️  {source_name}: HTTP {response.status_code}")
                return articles

            feed = feedparser.parse(response.content)

        except req.exceptions.Timeout:
            print(f"  ⏱️  {source_name}: timeout")
            return articles
        except req.exceptions.ConnectionError:
            print(f"  🚫 {source_name}: اتصال برقرار نشد")
            return articles
        except req.exceptions.RequestException as e:
            print(f"  ❌ {source_name}: {e}")
            return articles

        if not feed.entries:
            print(f"  📭 {source_name}: فید خالی")
            return articles

        for entry in feed.entries[:20]:
            title        = entry.get('title', 'No Title')
            link         = entry.get('link', '')
            summary      = clean_summary(entry.get('summary', ''))
            published    = entry.get('published', '')
            image        = extract_image(entry)
            detected     = detect_platforms(title, summary)
            has_video    = 1 if detect_video(title, summary) else 0
            urgency      = detect_urgency(title, summary)
            games        = detect_games(title, summary)
            studios      = detect_studios(title, summary)
            article_hash = generate_hash(title, link)

            # اگه فید category داره → از اون استفاده کن
            # اگه نداره → keyword detection
            if forced_category:
                content_type = forced_category
            else:
                content_type = detect_content_type(title, summary)

            articles.append({
                'hash'              : article_hash,
                'title'             : title,
                'link'              : link,
                'summary'           : summary,
                'source'            : source_name,
                'source_platform'   : platform_name,
                'detected_platforms': ','.join(detected),
                'content_type'      : content_type,
                'has_video'         : has_video,
                'image_url'         : image,
                'published'         : published,
                'fetched_at'        : datetime.now().isoformat(),
                'urgency'           : urgency,
                'game_tags'         : ','.join(games),
                'studio_tags'       : ','.join(studios),
            })

    except Exception as e:
        print(f"[ERROR] {source_name}: {e}")

    return articles

def fetch_all_feeds():
    global last_update_time, new_articles_count, last_urgent_articles

    print(f"\n{'='*52}")
    print(f"[FETCHING] شروع — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*52}")

    conn          = get_db()
    total_new     = 0
    urgent_new    = []
    success_count = 0
    fail_count    = 0

    sources = get_active_sources()
    print(f"[INFO] منابع فعال: {len(sources)}")
    print(f"[INFO] پروکسی: {'فعال ✅' if PROXIES.get('http') else 'غیرفعال ⚠️'}")

    for source in sources:
        forced_cat = source.get('feed_category', '') or ''
        articles   = fetch_single_feed(
            source['name'], source['url'], source['platform'], forced_cat
        )

        if articles:
            success_count += 1
        else:
            fail_count += 1

        new_count = 0
        for article in articles:
            try:
                cursor = conn.execute("""
                    INSERT OR IGNORE INTO articles
                    (hash, title, link, summary, source, source_platform,
                     detected_platforms, content_type, has_video, image_url,
                     published, fetched_at, urgency, game_tags, studio_tags)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    article['hash'], article['title'], article['link'],
                    article['summary'], article['source'],
                    article['source_platform'], article['detected_platforms'],
                    article['content_type'], article['has_video'],
                    article['image_url'], article['published'],
                    article['fetched_at'], article['urgency'],
                    article['game_tags'], article['studio_tags']
                ))
                if cursor.rowcount > 0:
                    new_count += 1
                    if article['urgency'] == 'high':
                        urgent_new.append({
                            'title' : article['title'],
                            'source': article['source'],
                            'link'  : article['link'],
                        })
            except:
                pass

        conn.execute("""
            INSERT OR REPLACE INTO feed_status
            (source, last_fetch, status, article_count)
            VALUES (?,?,?,?)
        """, (
            source['name'],
            datetime.now().isoformat(),
            'ok' if articles else 'error',
            len(articles)
        ))

        total_new += new_count
        if new_count > 0:
            cat_label = f"[{forced_cat}]" if forced_cat else ""
            print(f"  ✅ {source['name']} {cat_label}: {new_count} جدید (از {len(articles)})")

    conn.commit()
    conn.close()

    deduplicate_articles()

    last_update_time     = datetime.now().isoformat()
    new_articles_count   = total_new
    last_urgent_articles = urgent_new

    print(f"\n{'='*52}")
    print(f"[DONE] ✅ {success_count} موفق | ❌ {fail_count} ناموفق | 🆕 {total_new} جدید")
    print(f"{'='*52}\n")

# ──────────── on-demand manager ────────────

def _run_feeds():
    global _feed_running, _last_feed_fetch
    try:
        fetch_all_feeds()
        _last_feed_fetch = time.time()
    except Exception as e:
        print(f"[feeds error] {e}")
    finally:
        _feed_running = False

def _run_translate():
    global _translate_running, _last_translation
    try:
        translate_articles_background()
        _last_translation = time.time()
    except Exception as e:
        print(f"[translate error] {e}")
    finally:
        _translate_running = False

def _run_trends():
    global _trends_running, _last_trends_fetch
    try:
        fetch_google_trends()
        _last_trends_fetch = time.time()
    except Exception as e:
        print(f"[trends error] {e}")
    finally:
        _trends_running = False

def maybe_update():
    global _feed_running, _translate_running, _trends_running
    global _feed_started_at, _translate_started, _trends_started
    now = time.time()

    if _feed_running and now - _feed_started_at > _MAX_RUN_TIME:
        _feed_running = False
    if _translate_running and now - _translate_started > _MAX_RUN_TIME:
        _translate_running = False
    if _trends_running and now - _trends_started > _MAX_RUN_TIME:
        _trends_running = False

    if now - _last_feed_fetch >= FEED_INTERVAL and not _feed_running:
        _feed_running    = True
        _feed_started_at = now
        threading.Thread(target=_run_feeds, daemon=True).start()

    if now - _last_translation >= TRANSLATE_INTERVAL and not _translate_running:
        _translate_running = True
        _translate_started = now
        threading.Thread(target=_run_translate, daemon=True).start()

    if now - _last_trends_fetch >= TRENDS_INTERVAL and not _trends_running:
        _trends_running = True
        _trends_started = now
        threading.Thread(target=_run_trends, daemon=True).start()

# ──────────── روت‌های اصلی ────────────

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/live-status')
def api_live_status():
    maybe_update()
    return jsonify({
        'last_update'  : last_update_time,
        'new_count'    : new_articles_count,
        'urgent_alerts': last_urgent_articles,
        'server_time'  : datetime.now().isoformat(),
        'feed_running' : _feed_running,
    })

@app.route('/api/news')
def api_news():
    maybe_update()

    platform     = request.args.get('platform', 'all')
    content_type = request.args.get('type', 'all')
    time_filter  = request.args.get('time', '24h')
    search       = request.args.get('search', '')
    bookmarked   = request.args.get('bookmarked', 'false')
    urgency      = request.args.get('urgency', 'all')
    page         = int(request.args.get('page', 1))
    per_page     = 30

    conn   = get_db()
    query  = "SELECT * FROM articles WHERE is_primary=1"
    params = []

    if platform != 'all':
        query += " AND (source_platform=? OR detected_platforms LIKE ?)"
        params.extend([platform, f"%{platform}%"])
    if content_type != 'all':
        query += " AND content_type=?"
        params.append(content_type)
    if bookmarked == 'true':
        query += " AND is_bookmarked=1"
    if urgency != 'all':
        query += " AND urgency=?"
        params.append(urgency)
    if search:
        query += " AND (title LIKE ? OR summary LIKE ? OR game_tags LIKE ? OR studio_tags LIKE ?)"
        params.extend([f"%{search}%"] * 4)

    time_map = {
        '1h' : timedelta(hours=1),
        '6h' : timedelta(hours=6),
        '24h': timedelta(hours=24),
        '7d' : timedelta(days=7),
    }
    if time_filter in time_map:
        query += " AND fetched_at>?"
        params.append((datetime.now() - time_map[time_filter]).isoformat())

    query += " ORDER BY fetched_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    articles = conn.execute(query, params).fetchall()
    total    = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE is_primary=1"
    ).fetchone()[0]
    conn.close()

    return jsonify({
        'articles': [dict(a) for a in articles],
        'total'   : total,
        'page'    : page,
        'has_more': len(articles) == per_page,
    })

@app.route('/api/urgent')
def api_urgent():
    conn = get_db()
    arts = conn.execute("""
        SELECT * FROM articles
        WHERE urgency='high' AND is_primary=1 AND fetched_at>?
        ORDER BY fetched_at DESC LIMIT 10
    """, ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchall()
    conn.close()
    return jsonify([dict(a) for a in arts])

@app.route('/api/trending-games')
def api_trending_games():
    conn = get_db()
    rows = conn.execute("""
        SELECT game_tags FROM articles
        WHERE fetched_at>? AND game_tags!=''
    """, ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchall()
    conn.close()

    game_count = {}
    for row in rows:
        for game in row['game_tags'].split(','):
            game = game.strip()
            if game:
                game_count[game] = game_count.get(game, 0) + 1

    top = sorted(game_count.items(), key=lambda x: x[1], reverse=True)[:15]
    return jsonify([{'name': g[0], 'count': g[1]} for g in top])

# ──────────── روت‌های ترندز ────────────

@app.route('/api/trends')
def api_trends():
    maybe_update()
    return jsonify(trends_cache if trends_cache else {
        'global': {}, 'iran': {}, 'related': [],
        'updated_at': None, 'message': 'در حال دریافت ترندها...',
    })

@app.route('/api/trends/compare')
def api_trends_compare():
    from trendspy import Trends  # ← lazy import
    kw1 = request.args.get('kw1', 'PlayStation')
    kw2 = request.args.get('kw2', 'Xbox')
    try:
        tr = Trends(request_delay=2.0)
        df = tr.interest_over_time([kw1, kw2], timeframe='now 7-d')
        if df.empty:
            return jsonify({'error': 'داده‌ای یافت نشد'})
        result = {
            kw1: int(df[kw1].mean()) if kw1 in df else 0,
            kw2: int(df[kw2].mean()) if kw2 in df else 0,
            'timeline': [
                {'date': str(idx), kw1: int(row.get(kw1, 0)), kw2: int(row.get(kw2, 0))}
                for idx, row in df.iterrows()
            ]
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/trends/internal')
def api_trends_internal():
    conn     = get_db()
    articles = conn.execute("""
        SELECT title, source_platform FROM articles WHERE fetched_at>?
    """, ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchall()
    conn.close()

    stop_words = {
        'the','a','an','is','are','was','were','to','for','in','on','at',
        'by','with','from','and','or','but','of','it','its','this','that',
        'will','be','has','have','had','not','as','up','out','how','what',
        'when','who','why','can','get','all','new','more','your','our',
        'their','about','after','could','would','should','than','into',
        'over','also','back','first',
    }
    word_count      = {}
    platform_trends = {p: {} for p in ['PlayStation','Xbox','Nintendo','PC','Mobile','General']}

    for article in articles:
        words    = re.findall(r'\b[a-zA-Z]{3,}\b', article['title'].lower())
        platform = article['source_platform']
        for word in words:
            if word not in stop_words:
                word_count[word] = word_count.get(word, 0) + 1
                if platform in platform_trends:
                    platform_trends[platform][word] = platform_trends[platform].get(word, 0) + 1

    top_words    = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:20]
    platform_top = {
        p: [{'word': w, 'count': c} for w, c in sorted(d.items(), key=lambda x: x[1], reverse=True)[:5]]
        for p, d in platform_trends.items()
    }
    return jsonify({
        'top_words'      : [{'word': w, 'count': c} for w, c in top_words],
        'platform_trends': platform_top,
        'total_articles' : len(articles),
    })

# ──────────── روت‌های والپیپر ────────────

@app.route('/api/wallpapers', methods=['GET'])
def get_wallpapers():
    conn = get_db()
    wps  = conn.execute(
        "SELECT id, filename, added_at FROM wallpapers ORDER BY added_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(w) for w in wps])

@app.route('/api/wallpapers/upload', methods=['POST'])
def upload_wallpaper():
    data       = request.json
    filename   = data.get('filename', '')
    image_data = data.get('data', '')
    if not filename or not image_data:
        return jsonify({'success': False, 'error': 'داده ناقص'})
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO wallpapers (filename, data, added_at) VALUES (?,?,?)",
            (filename, image_data, datetime.now().isoformat())
        )
        conn.commit()
        wp_id = conn.execute(
            "SELECT id FROM wallpapers WHERE filename=?", (filename,)
        ).fetchone()['id']
        conn.close()
        return jsonify({'success': True, 'id': wp_id})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/wallpapers/<int:wallpaper_id>', methods=['GET'])
def get_wallpaper(wallpaper_id):
    conn = get_db()
    wp   = conn.execute("SELECT * FROM wallpapers WHERE id=?", (wallpaper_id,)).fetchone()
    conn.close()
    return jsonify(dict(wp)) if wp else (jsonify({'error': 'یافت نشد'}), 404)

@app.route('/api/wallpapers/delete', methods=['POST'])
def delete_wallpaper():
    conn = get_db()
    conn.execute("DELETE FROM wallpapers WHERE id=?", (request.json.get('id'),))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ──────────── روت‌های منابع ────────────

@app.route('/api/sources')
def api_sources():
    conn    = get_db()
    sources = conn.execute("""
        SELECT cs.*, fs.last_fetch, fs.article_count, fs.status
        FROM custom_sources cs
        LEFT JOIN feed_status fs ON cs.name=fs.source
        ORDER BY cs.platform, cs.name
    """).fetchall()
    conn.close()
    return jsonify([dict(s) for s in sources])

@app.route('/api/sources/add', methods=['POST'])
def add_source():
    data     = request.json
    name     = data.get('name', '').strip()
    url      = data.get('url', '').strip()
    platform = data.get('platform', 'General')
    if not name or not url:
        return jsonify({'success': False, 'error': 'نام و آدرس RSS الزامیست'})
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO custom_sources (name, url, platform, source_type, feed_category, is_active, added_at)
            VALUES (?,?,?,'general','',1,?)
        """, (name, url, platform, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except:
        conn.close()
        return jsonify({'success': False, 'error': 'این منبع قبلاً اضافه شده'})

@app.route('/api/sources/edit', methods=['POST'])
def edit_source():
    data      = request.json or {}
    source_id = data.get('id')
    name      = (data.get('name') or '').strip()
    url       = (data.get('url')  or '').strip()
    platform  = data.get('platform') or 'General'
    if not source_id:
        return jsonify({'success': False, 'error': 'ID ارسال نشده'})
    if not name or not url:
        return jsonify({'success': False, 'error': 'نام و آدرس الزامیست'})
    try:
        conn = get_db()
        cur  = conn.execute(
            "UPDATE custom_sources SET name=?, url=?, platform=? WHERE id=?",
            (name, url, platform, int(source_id))
        )
        if cur.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'منبع پیدا نشد'})
        conn.execute("DELETE FROM feed_status WHERE source=?", (name,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sources/delete', methods=['POST'])
def delete_source():
    conn = get_db()
    conn.execute("DELETE FROM custom_sources WHERE id=?", (request.json.get('id'),))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/sources/toggle', methods=['POST'])
def toggle_source():
    data   = request.json
    conn   = get_db()
    source = conn.execute(
        "SELECT is_active FROM custom_sources WHERE id=?", (data.get('id'),)
    ).fetchone()
    if source:
        conn.execute(
            "UPDATE custom_sources SET is_active=? WHERE id=?",
            (0 if source['is_active'] else 1, data.get('id'))
        )
        conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/bookmark', methods=['POST'])
def toggle_bookmark():
    data       = request.json
    article_id = data.get('id')
    conn       = get_db()
    article    = conn.execute(
        "SELECT is_bookmarked FROM articles WHERE id=?", (article_id,)
    ).fetchone()
    new_val = 0
    if article:
        new_val = 0 if article['is_bookmarked'] else 1
        conn.execute(
            "UPDATE articles SET is_bookmarked=? WHERE id=?", (new_val, article_id)
        )
        conn.commit()
    conn.close()
    return jsonify({'success': True, 'bookmarked': new_val})

@app.route('/api/tag', methods=['POST'])
def set_tag():
    data = request.json
    conn = get_db()
    conn.execute(
        "UPDATE articles SET custom_tag=? WHERE id=?",
        (data.get('tag', ''), data.get('id'))
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stats')
def api_stats():
    conn       = get_db()
    cutoff_24h = (datetime.now() - timedelta(hours=24)).isoformat()
    return jsonify({
        'total'            : conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
        'today'            : conn.execute("SELECT COUNT(*) FROM articles WHERE fetched_at>?", (cutoff_24h,)).fetchone()[0],
        'bookmarked'       : conn.execute("SELECT COUNT(*) FROM articles WHERE is_bookmarked=1").fetchone()[0],
        'sources'          : conn.execute("SELECT COUNT(DISTINCT source) FROM articles").fetchone()[0],
        'video_count'      : conn.execute("SELECT COUNT(*) FROM articles WHERE has_video=1 AND fetched_at>?", (cutoff_24h,)).fetchone()[0],
        'urgent_count'     : conn.execute("SELECT COUNT(*) FROM articles WHERE urgency='high' AND fetched_at>? AND is_primary=1", (cutoff_24h,)).fetchone()[0],
        'duplicates_removed': conn.execute("SELECT COUNT(*) FROM articles WHERE is_primary=0 AND fetched_at>?", (cutoff_24h,)).fetchone()[0],
    })

@app.route('/api/refresh', methods=['POST'])
def manual_refresh():
    global _feed_running, _feed_started_at
    if _feed_running:
        return jsonify({'success': True, 'message': 'در حال بروزرسانی...'})
    _feed_running    = True
    _feed_started_at = time.time()
    threading.Thread(target=_run_feeds, daemon=True).start()
    return jsonify({'success': True})

@app.route('/api/feed-status')
def feed_status():
    conn     = get_db()
    statuses = conn.execute("SELECT * FROM feed_status ORDER BY last_fetch DESC").fetchall()
    conn.close()
    return jsonify([dict(s) for s in statuses])

# ──────────── اجرا ────────────

if __name__ == '__main__':
    print("\n🎮 GamePulse — فاز ۳ در حال راه‌اندازی...")
    print("🌐 داشبورد: http://127.0.0.1:5000\n")
    app.run(debug=False, host='0.0.0.0', port=5000)