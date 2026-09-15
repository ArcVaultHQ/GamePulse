# ══════════════════════════════════════════════
# GamePulse — feeds.py (نسخه نهایی — فقط فیدهای سالم)
# ══════════════════════════════════════════════

GAMING_FEEDS = {

    'PlayStation': {
        'type': 'console',
        'sources': {
            'Push Square':          {'url': 'https://www.pushsquare.com/feeds/latest',  'category': 'news'},
            'Push Square Reviews':  {'url': 'https://www.pushsquare.com/feeds/reviews', 'category': 'review'},
            'Push Square Features': {'url': 'https://www.pushsquare.com/feeds/features','category': 'analysis'},
            'Push Square Guides':   {'url': 'https://www.pushsquare.com/feeds/guides',  'category': 'guide'},
            'PlayStation Blog':     {'url': 'https://blog.playstation.com/feed/',        'category': 'news'},
        }
    },

    'Xbox': {
        'type': 'console',
        'sources': {
            'Pure Xbox':          {'url': 'https://www.purexbox.com/feeds/latest',  'category': 'news'},
            'Pure Xbox Reviews':  {'url': 'https://www.purexbox.com/feeds/reviews', 'category': 'review'},
            'Pure Xbox Features': {'url': 'https://www.purexbox.com/feeds/features','category': 'analysis'},
            'Pure Xbox Guides':   {'url': 'https://www.purexbox.com/feeds/guides',  'category': 'guide'},
            'Xbox Wire':          {'url': 'https://news.xbox.com/en-us/feed/',       'category': 'news'},
        }
    },

    'Nintendo': {
        'type': 'console',
        'sources': {
            'Nintendo Life':          {'url': 'https://www.nintendolife.com/feeds/latest',  'category': 'news'},
            'Nintendo Life Reviews':  {'url': 'https://www.nintendolife.com/feeds/reviews', 'category': 'review'},
            'Nintendo Life Features': {'url': 'https://www.nintendolife.com/feeds/features','category': 'analysis'},
            'Nintendo Life Guides':   {'url': 'https://www.nintendolife.com/feeds/guides',  'category': 'guide'},
        }
    },

    'PC': {
        'type': 'platform',
        'sources': {
            'PC Gamer':           {'url': 'https://www.pcgamer.com/rss/',          'category': 'news'},
            'PC Gamer Reviews':   {'url': 'https://www.pcgamer.com/rss/reviews/',  'category': 'review'},
            'PC Gamer Features':  {'url': 'https://www.pcgamer.com/rss/features/', 'category': 'analysis'},
            'Rock Paper Shotgun': {'url': 'https://www.rockpapershotgun.com/feed', 'category': 'news'},
            'PCGamesN':           {'url': 'https://www.pcgamesn.com/mainrss.xml',  'category': 'news'},
            'DSOGaming':          {'url': 'https://www.dsogaming.com/feed/',        'category': 'news'},
        }
    },

    'Mobile': {
        'type': 'platform',
        'sources': {
            'TouchArcade':         {'url': 'https://toucharcade.com/feed/',                  'category': 'news'},
            'TouchArcade Reviews': {'url': 'https://toucharcade.com/category/reviews/feed/', 'category': 'review'},
            'Pocket Gamer':        {'url': 'https://www.pocketgamer.com/rss/',               'category': 'news'},
        }
    },

    'General': {
        'type': 'general',
        'sources': {

            # ── IGN ──
            'IGN':         {'url': 'https://feeds.feedburner.com/ign/games-all',  'category': 'news'},
            'IGN Reviews': {'url': 'https://feeds.feedburner.com/ign/reviews',    'category': 'review'},

            # ── GameSpot ──
            'GameSpot':         {'url': 'https://www.gamespot.com/feeds/mashup/',  'category': 'news'},
            'GameSpot Reviews': {'url': 'https://www.gamespot.com/feeds/reviews/', 'category': 'review'},

            # ── Kotaku (فید اصلی — داخلش همه نوع محتواست، keyword detection تعیین میکنه) ──
            'Kotaku': {'url': 'https://kotaku.com/rss', 'category': ''},

            # ── Polygon ──
            'Polygon': {'url': 'https://www.polygon.com/rss/index.xml', 'category': ''},

            # ── Eurogamer ──
            'Eurogamer': {'url': 'https://www.eurogamer.net/?format=rss', 'category': ''},

            # ── GamesRadar ──
            'GamesRadar': {'url': 'https://www.gamesradar.com/feeds.xml', 'category': ''},

            # ── VG247 ──
            'VG247': {'url': 'https://www.vg247.com/feed', 'category': ''},

            # ── VGC ──
            'VGC': {'url': 'https://www.videogameschronicle.com/feed/', 'category': 'news'},

            # ── Game Rant ──
            'Game Rant': {'url': 'https://gamerant.com/feed/', 'category': ''},

            # ── TheGamer ──
            'TheGamer': {'url': 'https://www.thegamer.com/feed/', 'category': ''},

            # ── DualShockers ──
            'DualShockers': {'url': 'https://www.dualshockers.com/feed/', 'category': ''},

            # ── MP1st ──
            'MP1st': {'url': 'https://mp1st.com/feed', 'category': 'news'},

            # ── Wccftech ──
            'Wccftech': {'url': 'https://wccftech.com/feed/', 'category': ''},

            # ── Shacknews ──
            'Shacknews': {'url': 'https://www.shacknews.com/feed/rss', 'category': ''},

            # ── Gematsu ──
            'Gematsu': {'url': 'https://www.gematsu.com/feed', 'category': 'news'},

            # ── GamingBolt ──
            'GamingBolt News':    {'url': 'https://gamingbolt.com/feed',                  'category': 'news'},
            'GamingBolt Reviews': {'url': 'https://gamingbolt.com/category/reviews/feed', 'category': 'review'},

            # ── Game Developer ──
            'Game Developer': {'url': 'https://www.gamedeveloper.com/rss.xml', 'category': 'analysis'},

            # ── GamesIndustry.biz ──
            'GamesIndustry.biz': {'url': 'https://www.gamesindustry.biz/feed', 'category': 'analysis'},

            # ── تخفیف‌ها ──
            'GamingDeals Reddit': {'url': 'https://www.reddit.com/r/GameDeals/new/.rss?limit=20', 'category': 'deal'},
            'PS Deals Reddit':    {'url': 'https://www.reddit.com/r/ps4deals/new/.rss?limit=20',  'category': 'deal'},
            'Xbox Deals Reddit':  {'url': 'https://www.reddit.com/r/xboxdeals/new/.rss?limit=20', 'category': 'deal'},
        }
    }
}

# ──────── کلمات کلیدی پلتفرم ────────
PLATFORM_KEYWORDS = {
    'PlayStation': [
        'playstation', 'ps5', 'ps4', 'ps3', 'psvr', 'psvr2', 'ps plus',
        'dualsense', 'dualshock', 'sony', 'playstation 5', 'playstation 4',
        'playstation exclusive', 'state of play',
    ],
    'Xbox': [
        'xbox', 'xbox series x', 'xbox series s', 'xbox one', 'game pass',
        'xbox game pass', 'microsoft', 'gamepass', 'xbox exclusive',
        'xbox studio', 'phil spencer', 'xcloud',
    ],
    'Nintendo': [
        'nintendo', 'switch', 'switch 2', 'mario', 'zelda', 'metroid',
        'pokemon', 'kirby', 'nintendo direct', 'joy-con', 'amiibo',
        'wii', '3ds', 'game boy', 'donkey kong', 'splatoon',
    ],
    'PC': [
        'pc', 'steam', 'epic games', 'gog', 'windows', 'directx',
        'graphics card', 'gpu', 'nvidia', 'amd', 'intel', 'ray tracing',
        'early access', 'pc gaming', 'gaming pc', 'esports',
    ],
    'Mobile': [
        'mobile', 'ios', 'android', 'iphone', 'ipad', 'apple arcade',
        'google play', 'app store', 'gacha', 'free to play', 'f2p',
        'mobile game', 'netflix games',
    ],
}

# ──────── کلمات کلیدی نوع محتوا (برای فیدهایی که category ندارن) ────────
CONTENT_TYPE_KEYWORDS = {
    'review': [
        'review', 'verdict', 'scored', 'rating', 'we review',
        'our review', 'game review', 'reviewed', 'score', 'out of 10',
        'out of 5', 'stars', 'worth buying', 'should you buy',
    ],
    'preview': [
        'preview', 'hands-on', 'hands on', 'first look', 'we played',
        'early access impressions', 'demo impressions', 'played',
        'before release', 'upcoming', 'we went hands',
    ],
    'interview': [
        'interview', 'talks', 'speaks', 'explains', 'developer says',
        'director talks', 'exclusive interview', 'in conversation',
        'q&a', 'chat with',
    ],
    'analysis': [
        'analysis', 'analyzed', 'deep dive', 'breakdown', 'explained',
        'everything we know', 'theory', 'lore', 'retrospective',
        'history of', 'opinion', 'editorial', 'why', 'how',
        'what went wrong', 'what went right', 'future of',
        'state of', 'report', 'inside look',
    ],
    'guide': [
        'guide', 'how to', 'tips', 'tricks', 'walkthrough', 'tutorial',
        'best build', 'best settings', 'unlock', 'complete guide',
        'trophy guide', 'achievement guide', 'cheats', 'secrets',
        'easter egg', 'hidden', 'location',
    ],
    'deal': [
        'deal', 'sale', 'discount', 'cheap', 'free', 'offer',
        'price drop', 'bundle', 'limited time', 'percent off',
        'giveaway', 'humble bundle', 'epic free', 'ps plus free',
        'game pass new', 'xbox free', 'prime gaming',
    ],
    'list': [
        'best', 'worst', 'top 10', 'top 5', 'ranked', 'every',
        'all', 'list of', 'games like', 'alternatives', 'similar to',
        'must play', 'essential', 'recommended',
    ],
    'tech': [
        'performance', 'fps', 'frame rate', 'resolution', 'graphics',
        'benchmark', 'comparison', 'digital foundry', '4k', 'hdr',
        'ray tracing', 'loading time', 'patch notes', 'update notes',
    ],
}

# ──────── کلمات کلیدی تشخیص ویدیو ────────
VIDEO_KEYWORDS = [
    'trailer', 'reveal trailer', 'gameplay trailer', 'launch trailer',
    'story trailer', 'cinematic', 'teaser', 'video', 'watch',
    'footage', 'clip', 'cutscene', 'demo video',
]