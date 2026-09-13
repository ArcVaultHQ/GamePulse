# ──────────────────────────────────────────────
# GamePulse — Feed Configuration
# لیست فیدهای RSS سایت‌های گیمینگ دنیا
# ──────────────────────────────────────────────

GAMING_FEEDS = {

    # ──────────── رسانه‌های اختصاصی پلی‌استیشن ────────────
    "PlayStation": {
        "type": "exclusive",
        "color": "#006FCD",
        "icon": "🎮",
        "sources": {
            "Push Square": {
                "url": "https://www.pushsquare.com/feeds/latest",
                "logo": "pushsquare"
            },
            "PlayStation Blog": {
                "url": "https://blog.playstation.com/feed/",
                "logo": "playstationblog"
            },
        }
    },

    # ──────────── رسانه‌های اختصاصی ایکس‌باکس ────────────
    "Xbox": {
        "type": "exclusive",
        "color": "#107C10",
        "icon": "🟩",
        "sources": {
            "Pure Xbox": {
                "url": "https://www.purexbox.com/feeds/latest",
                "logo": "purexbox"
            },
            "Xbox Wire": {
                "url": "https://news.xbox.com/en-us/feed/",
                "logo": "xboxwire"
            },
        }
    },

    # ──────────── رسانه‌های اختصاصی نینتندو ────────────
    "Nintendo": {
        "type": "exclusive",
        "color": "#E60012",
        "icon": "🔴",
        "sources": {
            "Nintendo Life": {
                "url": "https://www.nintendolife.com/feeds/latest",
                "logo": "nintendolife"
            },
        }
    },

    # ──────────── رسانه‌های اختصاصی PC ────────────
    "PC": {
        "type": "exclusive",
        "color": "#FF6B00",
        "icon": "🖥️",
        "sources": {
            "PC Gamer": {
                "url": "https://www.pcgamer.com/rss/",
                "logo": "pcgamer"
            },
            "Rock Paper Shotgun": {
                "url": "https://www.rockpapershotgun.com/feed",
                "logo": "rps"
            },
            "PCGamesN": {
                "url": "https://www.pcgamesn.com/mainrss.xml",
                "logo": "pcgamesn"
            },
            "DSOGaming": {
                "url": "https://www.dsogaming.com/feed/",
                "logo": "dsogaming"
            },
        }
    },

    # ──────────── رسانه‌های اختصاصی موبایل ────────────
    "Mobile": {
        "type": "exclusive",
        "color": "#A855F7",
        "icon": "📱",
        "sources": {
            "TouchArcade": {
                "url": "https://toucharcade.com/feed/",
                "logo": "toucharcade"
            },
        }
    },

    # ──────────── رسانه‌های عمومی (مولتی‌پلتفرم) ────────────
    "General": {
        "type": "general",
        "color": "#FFD700",
        "icon": "🌐",
        "sources": {
            "IGN": {
                "url": "https://feeds.feedburner.com/ign/all",
                "logo": "ign"
            },
            "GameSpot": {
                "url": "https://www.gamespot.com/feeds/mashup/",
                "logo": "gamespot"
            },
            "Kotaku": {
                "url": "https://kotaku.com/rss",
                "logo": "kotaku"
            },
            "Polygon": {
                "url": "https://www.polygon.com/rss/index.xml",
                "logo": "polygon"
            },
            "Eurogamer": {
                "url": "https://www.eurogamer.net/feed",
                "logo": "eurogamer"
            },
            "GamesRadar": {
                "url": "https://www.gamesradar.com/rss/",
                "logo": "gamesradar"
            },
            "VG247": {
                "url": "https://www.vg247.com/feed",
                "logo": "vg247"
            },
            "Destructoid": {
                "url": "https://www.destructoid.com/feed/",
                "logo": "destructoid"
            },
            "VGC": {
                "url": "https://www.videogameschronicle.com/feed",
                "logo": "vgc"
            },
            "Game Rant": {
                "url": "https://gamerant.com/feed/",
                "logo": "gamerant"
            },
            "TheGamer": {
                "url": "https://www.thegamer.com/feed/",
                "logo": "thegamer"
            },
            "DualShockers": {
                "url": "https://www.dualshockers.com/feed/",
                "logo": "dualshockers"
            },
            "Twinfinite": {
                "url": "https://twinfinite.net/feed/",
                "logo": "twinfinite"
            },
            "MP1st": {
                "url": "https://mp1st.com/feed",
                "logo": "mp1st"
            },
            "Wccftech": {
                "url": "https://wccftech.com/feed/",
                "logo": "wccftech"
            },
            "Shacknews": {
                "url": "https://www.shacknews.com/feed/rss",
                "logo": "shacknews"
            },
            "Siliconera": {
                "url": "https://www.siliconera.com/feed/",
                "logo": "siliconera"
            },
            "Gematsu": {
                "url": "https://www.gematsu.com/feed",
                "logo": "gematsu"
            },
        }
    },
}


# لیست کلمات کلیدی برای تشخیص خودکار پلتفرم از عنوان خبر
PLATFORM_KEYWORDS = {
    "PlayStation": ["ps5", "ps4", "playstation", "dualsense", "psn", "ps plus",
                    "psvr", "psvr2", "ps vr2", "dualshock", "sony interactive",
                    "naughty dog", "insomniac", "guerrilla", "sucker punch",
                    "santa monica", "bluepoint", "housemarque", "firesprite",
                    "haven studios", "bungie"],
    "Xbox": ["xbox", "series x", "series s", "game pass", "gamepass",
             "halo", "forza", "microsoft gaming", "bethesda", "activision",
             "blizzard", "obsidian", "ninja theory", "rare", "playground games",
             "turn 10", "id software", "machinegames", "arkane", "compulsion",
             "double fine", "inexile"],
    "Nintendo": ["nintendo", "switch", "switch 2", "zelda", "mario", "pokemon",
                 "pokémon", "smash bros", "metroid", "splatoon", "kirby",
                 "animal crossing", "fire emblem", "xenoblade", "pikmin",
                 "joy-con", "amiibo", "game freak", "hal laboratory",
                 "monolith soft", "retro studios"],
    "PC": ["steam", "epic games store", "gog", "pc gaming", "nvidia",
           "amd", "rtx", "geforce", "radeon", "directx", "vulkan",
           "pc port", "pc version", "mod", "modding", "early access",
           "valve", "steam deck"],
    "Mobile": ["ios", "android", "mobile game", "apple arcade", "google play",
               "iphone", "ipad", "mobile gaming", "touch screen", "gacha",
               "free to play mobile", "netease", "mihoyo", "hoyoverse",
               "supercell", "king"],
}

# کلمات کلیدی تشخیص ویدیو/تریلر
VIDEO_KEYWORDS = ["trailer", "gameplay", "teaser", "cinematic", "reveal",
                  "footage", "video", "watch", "showcase", "demo",
                  "walkthrough", "preview trailer", "launch trailer",
                  "announcement trailer", "story trailer"]

# کلمات کلیدی دسته‌بندی نوع محتوا
CONTENT_TYPE_KEYWORDS = {
    "review": ["review", "rated", "score", "verdict", "/10", "critique"],
    "news": ["announced", "confirms", "revealed", "launches", "releases",
             "update", "patch", "dlc", "expansion", "report", "rumor"],
    "preview": ["preview", "hands-on", "first look", "impressions",
                "hands on", "early access preview"],
    "interview": ["interview", "talks about", "discusses", "speaks to",
                  "q&a", "conversation with"],
    "analysis": ["analysis", "deep dive", "explained", "breakdown",
                 "opinion", "editorial", "why", "how"],
    "guide": ["guide", "how to", "tips", "walkthrough", "best",
              "tier list", "build guide"],
    "list": ["best", "top", "ranking", "list", "every", "all"],
    "deal": ["deal", "sale", "discount", "free", "offer", "price drop",
             "cheap", "bundle"],
    "tech": ["performance", "fps", "resolution", "ray tracing",
             "digital foundry", "specs", "benchmark", "comparison"],
}