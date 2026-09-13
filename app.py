# ──────────────────────────────────────────────
# GamePulse — Main Application (فاز ۳)
# ──────────────────────────────────────────────

from flask import Flask, render_template, jsonify, request
import feedparser
import sqlite3
import hashlib
import threading
import time
import re
import os
import json
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from pytrends.request import TrendReq
from feeds import GAMING_FEEDS, PLATFORM_KEYWORDS, VIDEO_KEYWORDS, CONTENT_TYPE_KEYWORDS

app = Flask(__name__)
DB_PATH = os.path.join("database", "gamepulse.db")

# ──────── متغیرهای لایو ────────
last_update_time = None
new_articles_count = 0
last_urgent_articles = []
trends_cache = {}
trends_last_update = None

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
    "Castlevania", "Contra", "Tekken", "Mortal Kombat",
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
    "high": ["breaking", "exclusive", "just announced", "world premiere",
             "first look", "reveal", "leaked", "leak", "confirmed",
             "official", "release date", "launches today", "out now",
             "game of the year", "goty", "award", "banned", "controversy",
             "acquisition", "acquired", "shutdown", "closed", "bankrupt"],
    "medium": ["announced", "revealed", "trailer", "gameplay", "preview",
               "hands-on", "review", "score", "update", "patch", "dlc",
               "expansion", "sequel", "remake", "remaster", "port"],
}

# ──────────── دیتابیس ────────────

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def init_db():
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
            related_sources TEXT DEFAULT ''
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
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM custom_sources").fetchone()[0]
    if count == 0:
        for platform_name, platform_data in GAMING_FEEDS.items():
            for source_name, source_info in platform_data['sources'].items():
                conn.execute("""
                    INSERT OR IGNORE INTO custom_sources
                    (name, url, platform, source_type, is_active, added_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (source_name, source_info['url'], platform_name,
                      platform_data['type'], datetime.now().isoformat()))
        conn.commit()

    conn.close()

def get_active_sources():
    conn = get_db()
    sources = conn.execute(
        "SELECT * FROM custom_sources WHERE is_active = 1"
    ).fetchall()
    conn.close()
    return [dict(s) for s in sources]

# ──────────── تشخیص هوشمند ────────────

def detect_platforms(title, summary=""):
    text = (title + " " + summary).lower()
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
    text = title + " " + summary
    found = []
    for game in GAME_NAMES:
        if game.lower() in text.lower():
            found.append(game)
    return list(set(found))[:5]

def detect_studios(title, summary=""):
    text = title + " " + summary
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
        content_html = entry.content[0].get('value', '')
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
        if img_match:
            return img_match.group(1)
    summary = entry.get('summary', '')
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

# ──────────── ترجمه فارسی ────────────

def translate_to_persian(text, article_hash):
    if not text or len(text) < 10:
        return ""
    try:
        conn = get_db()
        cached = conn.execute(
            "SELECT translated FROM translation_cache WHERE original_hash = ?",
            (article_hash,)
        ).fetchone()
        conn.close()
        if cached:
            return cached['translated']

        translator = GoogleTranslator(source='en', target='fa')
        translated = translator.translate(text[:200])

        conn = get_db()
        conn.execute(
            "INSERT OR IGNORE INTO translation_cache (original_hash, translated, created_at) VALUES (?, ?, ?)",
            (article_hash, translated, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return translated
    except:
        return ""

def translate_articles_background():
    while True:
        try:
            conn = get_db()
            articles = conn.execute(
                "SELECT id, hash, summary FROM articles WHERE summary_fa = '' AND summary != '' LIMIT 10"
            ).fetchall()
            conn.close()
            for article in articles:
                translated = translate_to_persian(article['summary'], article['hash'])
                if translated:
                    conn = get_db()
                    conn.execute(
                        "UPDATE articles SET summary_fa = ? WHERE id = ?",
                        (translated, article['id'])
                    )
                    conn.commit()
                    conn.close()
                time.sleep(1)
        except Exception as e:
            print(f"[TRANSLATE ERROR] {e}")
        time.sleep(30)

# ──────────── Google Trends ────────────

def fetch_google_trends():
    global trends_cache, trends_last_update
    try:
        print("[TRENDS] در حال دریافت Google Trends...")
        time.sleep(10)
        pytrends = TrendReq(hl='en-US', tz=210, retries=2, backoff_factor=1)

        gaming_keywords = [
            'gaming', 'video games', 'PlayStation', 'Xbox', 'Nintendo'
        ]

        pytrends.build_payload(
            gaming_keywords[:5],
            cat=0,
            timeframe='now 1-d',
            geo='',
            gprop='',
        )
        interest_df = pytrends.interest_over_time()

        trend_data = {}
        if not interest_df.empty:
            for col in interest_df.columns:
                if col != 'isPartial':
                    trend_data[col] = int(interest_df[col].mean())

        # ترند ایران
        pytrends_ir = TrendReq(hl='fa', tz=210)
        gaming_fa = ['بازی', 'گیمینگ', 'پلی استیشن']
        pytrends_ir.build_payload(
            gaming_fa[:3],
            cat=0,
            timeframe='now 1-d',
            geo='IR',
            gprop='',
        )
        interest_ir = pytrends_ir.interest_over_time()
        iran_trends = {}
        if not interest_ir.empty:
            for col in interest_ir.columns:
                if col != 'isPartial':
                    iran_trends[col] = int(interest_ir[col].mean())

        # Related queries
        related = {}
        try:
            pytrends2 = TrendReq(hl='en-US', tz=210)
            pytrends2.build_payload(['gaming'], timeframe='now 1-d')
            related_queries = pytrends2.related_queries()
            if 'gaming' in related_queries and related_queries['gaming']['top'] is not None:
                top_queries = related_queries['gaming']['top'].head(10)
                related = top_queries.to_dict('records')
        except:
            pass

        trends_cache = {
            'global': trend_data,
            'iran': iran_trends,
            'related': related,
            'updated_at': datetime.now().isoformat()
        }
        trends_last_update = datetime.now()
        print(f"[TRENDS] ✅ آپدیت شد!")

    except Exception as e:
        print(f"[TRENDS ERROR] {e}")

def trends_updater():
    while True:
        try:
            fetch_google_trends()
        except Exception as e:
            print(f"[TRENDS BG ERROR] {e}")
        time.sleep(7200)  # هر ۲ ساعت

# ──────────── دریافت فیدها ────────────

def fetch_single_feed(source_name, feed_url, platform_name):
    articles = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:20]:
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            summary = clean_summary(entry.get('summary', ''))
            published = entry.get('published', '')
            image = extract_image(entry)
            detected = detect_platforms(title, summary)
            content_type = detect_content_type(title, summary)
            has_video = 1 if detect_video(title, summary) else 0
            urgency = detect_urgency(title, summary)
            games = detect_games(title, summary)
            studios = detect_studios(title, summary)
            article_hash = generate_hash(title, link)

            articles.append({
                'hash': article_hash,
                'title': title,
                'link': link,
                'summary': summary,
                'source': source_name,
                'source_platform': platform_name,
                'detected_platforms': ','.join(detected),
                'content_type': content_type,
                'has_video': has_video,
                'image_url': image,
                'published': published,
                'fetched_at': datetime.now().isoformat(),
                'urgency': urgency,
                'game_tags': ','.join(games),
                'studio_tags': ','.join(studios),
            })
    except Exception as e:
        print(f"[ERROR] {source_name}: {e}")
    return articles

def fetch_all_feeds():
    global last_update_time, new_articles_count, last_urgent_articles

    print(f"\n[FETCHING] شروع — {datetime.now().strftime('%H:%M:%S')}")
    conn = get_db()
    total_new = 0
    urgent_new = []

    sources = get_active_sources()

    for source in sources:
        articles = fetch_single_feed(
            source['name'], source['url'], source['platform']
        )

        new_count = 0
        for article in articles:
            try:
                cursor = conn.execute("""
                    INSERT OR IGNORE INTO articles
                    (hash, title, link, summary, source, source_platform,
                     detected_platforms, content_type, has_video, image_url,
                     published, fetched_at, urgency, game_tags, studio_tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            'title': article['title'],
                            'source': article['source'],
                            'link': article['link']
                        })
            except:
                pass

        conn.execute("""
            INSERT OR REPLACE INTO feed_status
            (source, last_fetch, status, article_count)
            VALUES (?, ?, ?, ?)
        """, (source['name'], datetime.now().isoformat(), 'ok', len(articles)))

        total_new += new_count
        if new_count > 0:
            print(f"  ✅ {source['name']}: {new_count} خبر جدید")

    conn.commit()
    conn.close()

    last_update_time = datetime.now().isoformat()
    new_articles_count = total_new
    last_urgent_articles = urgent_new

    print(f"[DONE] مجموع: {total_new}\n")

def background_updater():
    while True:
        try:
            fetch_all_feeds()
        except Exception as e:
            print(f"[BG ERROR] {e}")
        time.sleep(120)

# ──────────── روت‌های اصلی ────────────

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/live-status')
def api_live_status():
    return jsonify({
        'last_update': last_update_time,
        'new_count': new_articles_count,
        'urgent_alerts': last_urgent_articles,
        'server_time': datetime.now().isoformat()
    })

@app.route('/api/news')
def api_news():
    platform = request.args.get('platform', 'all')
    content_type = request.args.get('type', 'all')
    time_filter = request.args.get('time', '24h')
    search = request.args.get('search', '')
    bookmarked = request.args.get('bookmarked', 'false')
    urgency = request.args.get('urgency', 'all')
    page = int(request.args.get('page', 1))
    per_page = 30

    conn = get_db()
    query = "SELECT * FROM articles WHERE 1=1"
    params = []

    if platform != 'all':
        query += " AND (source_platform = ? OR detected_platforms LIKE ?)"
        params.extend([platform, f"%{platform}%"])
    if content_type != 'all':
        query += " AND content_type = ?"
        params.append(content_type)
    if bookmarked == 'true':
        query += " AND is_bookmarked = 1"
    if urgency != 'all':
        query += " AND urgency = ?"
        params.append(urgency)
    if search:
        query += " AND (title LIKE ? OR summary LIKE ? OR game_tags LIKE ? OR studio_tags LIKE ?)"
        params.extend([f"%{search}%"] * 4)

    if time_filter == '1h':
        query += " AND fetched_at > ?"
        params.append((datetime.now() - timedelta(hours=1)).isoformat())
    elif time_filter == '6h':
        query += " AND fetched_at > ?"
        params.append((datetime.now() - timedelta(hours=6)).isoformat())
    elif time_filter == '24h':
        query += " AND fetched_at > ?"
        params.append((datetime.now() - timedelta(hours=24)).isoformat())
    elif time_filter == '7d':
        query += " AND fetched_at > ?"
        params.append((datetime.now() - timedelta(days=7)).isoformat())

    query += " ORDER BY fetched_at DESC"
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    articles = conn.execute(query, params).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    conn.close()

    return jsonify({
        'articles': [dict(a) for a in articles],
        'total': total,
        'page': page,
        'has_more': len(articles) == per_page
    })

@app.route('/api/urgent')
def api_urgent():
    conn = get_db()
    articles = conn.execute("""
        SELECT * FROM articles WHERE urgency = 'high'
        AND fetched_at > ? ORDER BY fetched_at DESC LIMIT 10
    """, ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchall()
    conn.close()
    return jsonify([dict(a) for a in articles])

@app.route('/api/trending-games')
def api_trending_games():
    conn = get_db()
    rows = conn.execute("""
        SELECT game_tags FROM articles
        WHERE fetched_at > ? AND game_tags != ''
    """, ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchall()
    conn.close()

    game_count = {}
    for row in rows:
        for game in row['game_tags'].split(','):
            game = game.strip()
            if game:
                game_count[game] = game_count.get(game, 0) + 1

    sorted_games = sorted(game_count.items(), key=lambda x: x[1], reverse=True)[:15]
    return jsonify([{'name': g[0], 'count': g[1]} for g in sorted_games])

# ──────────── روت‌های ترندز ────────────

@app.route('/api/trends')
def api_trends():
    return jsonify(trends_cache if trends_cache else {
        'global': {},
        'iran': {},
        'related': [],
        'updated_at': None,
        'message': 'در حال دریافت ترندها...'
    })

@app.route('/api/trends/compare')
def api_trends_compare():
    kw1 = request.args.get('kw1', 'PlayStation')
    kw2 = request.args.get('kw2', 'Xbox')
    try:
        pytrends = TrendReq(hl='en-US', tz=210)
        pytrends.build_payload([kw1, kw2], timeframe='now 7-d')
        df = pytrends.interest_over_time()
        if df.empty:
            return jsonify({'error': 'داده‌ای یافت نشد'})

        result = {
            kw1: int(df[kw1].mean()) if kw1 in df else 0,
            kw2: int(df[kw2].mean()) if kw2 in df else 0,
            'timeline': []
        }

        for idx, row in df.iterrows():
            result['timeline'].append({
                'date': str(idx),
                kw1: int(row[kw1]) if kw1 in row else 0,
                kw2: int(row[kw2]) if kw2 in row else 0,
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/trends/internal')
def api_trends_internal():
    """ترندیاب داخلی — بر اساس داده‌های خودمون"""
    conn = get_db()

    # پرتکرارترین کلمات توی عناوین ۲۴ ساعت گذشته
    articles = conn.execute("""
        SELECT title, source_platform FROM articles
        WHERE fetched_at > ?
    """, ((datetime.now() - timedelta(hours=24)).isoformat(),)).fetchall()
    conn.close()

    word_count = {}
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'for',
                  'in', 'on', 'at', 'by', 'with', 'from', 'and', 'or', 'but',
                  'of', 'it', 'its', 'this', 'that', 'will', 'be', 'has',
                  'have', 'had', 'not', 'as', 'up', 'out', 'how', 'what',
                  'when', 'who', 'why', 'can', 'get', 'all', 'new', 'more',
                  'your', 'our', 'their', 'about', 'after', 'could', 'would',
                  'should', 'than', 'into', 'over', 'also', 'back', 'first'}

    platform_trends = {
        'PlayStation': {}, 'Xbox': {}, 'Nintendo': {},
        'PC': {}, 'Mobile': {}, 'General': {}
    }

    for article in articles:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', article['title'].lower())
        platform = article['source_platform']

        for word in words:
            if word not in stop_words:
                word_count[word] = word_count.get(word, 0) + 1
                if platform in platform_trends:
                    platform_trends[platform][word] = platform_trends[platform].get(word, 0) + 1

    top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:20]

    platform_top = {}
    for platform, words in platform_trends.items():
        top = sorted(words.items(), key=lambda x: x[1], reverse=True)[:5]
        platform_top[platform] = [{'word': w[0], 'count': w[1]} for w in top]

    return jsonify({
        'top_words': [{'word': w[0], 'count': w[1]} for w in top_words],
        'platform_trends': platform_top,
        'total_articles': len(articles)
    })

# ──────────── روت‌های والپیپر ────────────

@app.route('/api/wallpapers', methods=['GET'])
def get_wallpapers():
    conn = get_db()
    wallpapers = conn.execute(
        "SELECT id, filename, added_at FROM wallpapers ORDER BY added_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(w) for w in wallpapers])

@app.route('/api/wallpapers/upload', methods=['POST'])
def upload_wallpaper():
    data = request.json
    filename = data.get('filename', '')
    image_data = data.get('data', '')

    if not filename or not image_data:
        return jsonify({'success': False, 'error': 'داده ناقص'})

    conn = get_db()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO wallpapers (filename, data, added_at)
            VALUES (?, ?, ?)
        """, (filename, image_data, datetime.now().isoformat()))
        conn.commit()
        wallpaper_id = conn.execute(
            "SELECT id FROM wallpapers WHERE filename = ?", (filename,)
        ).fetchone()['id']
        conn.close()
        return jsonify({'success': True, 'id': wallpaper_id})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/wallpapers/<int:wallpaper_id>', methods=['GET'])
def get_wallpaper(wallpaper_id):
    conn = get_db()
    wp = conn.execute(
        "SELECT * FROM wallpapers WHERE id = ?", (wallpaper_id,)
    ).fetchone()
    conn.close()
    if wp:
        return jsonify(dict(wp))
    return jsonify({'error': 'یافت نشد'}), 404

@app.route('/api/wallpapers/delete', methods=['POST'])
def delete_wallpaper():
    data = request.json
    wp_id = data.get('id')
    conn = get_db()
    conn.execute("DELETE FROM wallpapers WHERE id = ?", (wp_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ──────────── روت‌های منابع ────────────

@app.route('/api/sources')
def api_sources():
    conn = get_db()
    sources = conn.execute(
        "SELECT cs.*, fs.last_fetch, fs.article_count, fs.status FROM custom_sources cs "
        "LEFT JOIN feed_status fs ON cs.name = fs.source "
        "ORDER BY cs.platform, cs.name"
    ).fetchall()
    conn.close()
    return jsonify([dict(s) for s in sources])

@app.route('/api/sources/add', methods=['POST'])
def add_source():
    data = request.json
    name = data.get('name', '').strip()
    url = data.get('url', '').strip()
    platform = data.get('platform', 'General')

    if not name or not url:
        return jsonify({'success': False, 'error': 'نام و آدرس RSS الزامیست'})

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO custom_sources (name, url, platform, source_type, is_active, added_at)
            VALUES (?, ?, ?, 'general', 1, ?)
        """, (name, url, platform, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except:
        conn.close()
        return jsonify({'success': False, 'error': 'این منبع قبلاً اضافه شده'})

@app.route('/api/sources/edit', methods=['POST'])
def edit_source():
    data = request.json or {}

    source_id = data.get('id')
    name = (data.get('name') or '').strip()
    url = (data.get('url') or '').strip()
    platform = data.get('platform') or 'General'

    if not source_id:
        return jsonify({'success': False, 'error': 'ID ارسال نشده'})

    if not name or not url:
        return jsonify({'success': False, 'error': 'نام و آدرس RSS الزامیست'})

    try:
        conn = get_db()

        cur = conn.execute("""
            UPDATE custom_sources
            SET name = ?, url = ?, platform = ?
            WHERE id = ?
        """, (name, url, platform, int(source_id)))

        if cur.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'منبع پیدا نشد'})

        conn.execute("DELETE FROM feed_status WHERE source = ?", (name,))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sources/delete', methods=['POST'])
def delete_source():
    data = request.json
    conn = get_db()
    conn.execute("DELETE FROM custom_sources WHERE id = ?", (data.get('id'),))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/sources/toggle', methods=['POST'])
def toggle_source():
    data = request.json
    conn = get_db()
    source = conn.execute(
        "SELECT is_active FROM custom_sources WHERE id = ?", (data.get('id'),)
    ).fetchone()
    if source:
        new_val = 0 if source['is_active'] else 1
        conn.execute(
            "UPDATE custom_sources SET is_active = ? WHERE id = ?",
            (new_val, data.get('id'))
        )
        conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/bookmark', methods=['POST'])
def toggle_bookmark():
    data = request.json
    article_id = data.get('id')
    conn = get_db()
    article = conn.execute(
        "SELECT is_bookmarked FROM articles WHERE id = ?", (article_id,)
    ).fetchone()
    new_val = 0
    if article:
        new_val = 0 if article['is_bookmarked'] else 1
        conn.execute(
            "UPDATE articles SET is_bookmarked = ? WHERE id = ?",
            (new_val, article_id)
        )
        conn.commit()
    conn.close()
    return jsonify({'success': True, 'bookmarked': new_val})

@app.route('/api/tag', methods=['POST'])
def set_tag():
    data = request.json
    conn = get_db()
    conn.execute(
        "UPDATE articles SET custom_tag = ? WHERE id = ?",
        (data.get('tag', ''), data.get('id'))
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stats')
def api_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    cutoff_24h = (datetime.now() - timedelta(hours=24)).isoformat()
    today = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE fetched_at > ?", (cutoff_24h,)
    ).fetchone()[0]
    bookmarked = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE is_bookmarked = 1"
    ).fetchone()[0]
    sources = conn.execute(
        "SELECT COUNT(DISTINCT source) FROM articles"
    ).fetchone()[0]
    video_count = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE has_video = 1 AND fetched_at > ?",
        (cutoff_24h,)
    ).fetchone()[0]
    urgent_count = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE urgency = 'high' AND fetched_at > ?",
        (cutoff_24h,)
    ).fetchone()[0]
    conn.close()
    return jsonify({
        'total': total, 'today': today, 'bookmarked': bookmarked,
        'sources': sources, 'video_count': video_count,
        'urgent_count': urgent_count
    })

@app.route('/api/refresh', methods=['POST'])
def manual_refresh():
    thread = threading.Thread(target=fetch_all_feeds)
    thread.start()
    return jsonify({'success': True})

@app.route('/api/feed-status')
def feed_status():
    conn = get_db()
    statuses = conn.execute(
        "SELECT * FROM feed_status ORDER BY last_fetch DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(s) for s in statuses])

# ──────────── اجرا ────────────

if __name__ == '__main__':
    init_db()
    print("\n🎮 GamePulse — فاز ۳ در حال راه‌اندازی...")
    print("⚡ لایو ترک: هر ۲ دقیقه")
    print("📈 Google Trends: هر ۱ ساعت")
    print("📡 شروع دریافت فیدها...\n")

    fetch_thread = threading.Thread(target=fetch_all_feeds, daemon=True)
    fetch_thread.start()

    updater_thread = threading.Thread(target=background_updater, daemon=True)
    updater_thread.start()

    translate_thread = threading.Thread(target=translate_articles_background, daemon=True)
    translate_thread.start()

    trends_thread = threading.Thread(target=fetch_google_trends, daemon=True)
    trends_thread.start()

    trends_bg_thread = threading.Thread(target=trends_updater, daemon=True)
    trends_bg_thread.start()

    print("🌐 داشبورد: http://127.0.0.1:5000\n")
    app.run(debug=False, host='0.0.0.0', port=5000)