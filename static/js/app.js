// ══════════════════════════════════════════════
// GamePulse — Frontend (فاز ۳)
// ══════════════════════════════════════════════

// ──────── State ────────
let currentPlatform = 'all';
let currentTime = '24h';
let currentType = 'all';
let currentUrgency = 'all';
let currentSearch = '';
let currentPage = 1;
let currentSection = 'dashboard';
let tagArticleId = null;
let lastKnownUpdate = null;
let editingSourceId = null;

// والپیپر
let wallpapers = [];
let currentWallpaperIndex = 0;
let wallpaperInterval = null;
let wallpaperSpeed = 5000;
let wallpaperTransition = 'fade';
let wallpaperBlur = 5;
let wallpaperDarkness = 60;
let activeSlide = 0;

// ──────── Init ────────
document.addEventListener('DOMContentLoaded', () => {
    setCurrentDate();
    loadStats();
    loadNews();
    loadUrgentNews();
    loadTrendingGames();
    setupEventListeners();
    startLiveTracking();
    loadWallpaperSettings();
    loadWallpapers();
});

// ──────── تاریخ ────────
function setCurrentDate() {
    const now = new Date();
    const el = document.getElementById('currentDate');
    if (el) el.textContent = now.toLocaleDateString('fa-IR', {
        weekday: 'long', year: 'numeric',
        month: 'long', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

// ══════════════════════════════════════════════
// ⚡ سیستم لایو ترک
// ══════════════════════════════════════════════

function startLiveTracking() {
    checkLiveStatus();
    setInterval(checkLiveStatus, 15000);
}

function checkLiveStatus() {
    fetch('/api/live-status')
        .then(r => r.json())
        .then(data => {
            updateLiveTimer(data);
            checkForNewArticles(data);
            checkForUrgentAlerts(data);
        })
        .catch(err => console.error('Live error:', err));
}

function updateLiveTimer(data) {
    const timerEl = document.getElementById('liveTimer');
    if (!timerEl) return;

    if (!data.last_update) {
        timerEl.textContent = 'در حال اتصال...';
        return;
    }

    const secondsAgo = Math.floor((new Date() - new Date(data.last_update)) / 1000);
    const nextIn = Math.max(0, 120 - secondsAgo);

    if (nextIn > 0) {
        const m = Math.floor(nextIn / 60);
        const s = nextIn % 60;
        timerEl.textContent = m > 0
            ? `آپدیت: ${m}:${s.toString().padStart(2,'0')}`
            : `آپدیت: ${s}ث`;
    } else {
        timerEl.textContent = 'در حال آپدیت...';
    }
}

function checkForNewArticles(data) {
    if (!lastKnownUpdate) {
        lastKnownUpdate = data.last_update;
        return;
    }

    if (data.last_update !== lastKnownUpdate && data.new_count > 0) {
        lastKnownUpdate = data.last_update;

        loadStats();
        loadTrendingGames();
        loadUrgentNews();

        // ✅ اگر کاربر داخل داشبورد یا رادار خبری است، خودکار رفرش کن
        if (currentSection === 'dashboard' || currentSection === 'news') {
            currentPage = 1;
            loadNews(false);
            showNotification(`⚡ ${data.new_count} خبر جدید بارگذاری شد!`);
        } else {
            // در بقیه بخش‌ها فقط نوار بنفش نمایش داده شود
            const bar = document.getElementById('newArticlesBar');
            const text = document.getElementById('newArticlesText');
            if (bar && text) {
                text.textContent = `${data.new_count} خبر جدید اضافه شد!`;
                bar.style.display = 'flex';
            }
        }
    }
}

function checkForUrgentAlerts(data) {
    if (!data.urgent_alerts || data.urgent_alerts.length === 0) return;
    if (!lastKnownUpdate || data.last_update === lastKnownUpdate) return;

    const popup = document.getElementById('urgentPopup');
    const body = document.getElementById('urgentPopupBody');
    if (!popup || !body) return;

    body.innerHTML = data.urgent_alerts.slice(0, 3).map(a => `
        <a href="${a.link}" target="_blank" class="urgent-popup-item">
            <span class="urgent-popup-source">${a.source}</span>
            <span class="urgent-popup-title">${a.title}</span>
        </a>
    `).join('');

    popup.style.display = 'block';
    setTimeout(() => closeUrgentPopup(), 15000);
}

function refreshAndDismiss() {
    dismissNewBar();
    currentPage = 1;
    loadNews();
    showNotification('✅ اخبار جدید بارگذاری شد!');
}

function dismissNewBar() {
    const bar = document.getElementById('newArticlesBar');
    if (bar) bar.style.display = 'none';
}

function closeUrgentPopup() {
    const popup = document.getElementById('urgentPopup');
    if (popup) popup.style.display = 'none';
}

// ══════════════════════════════════════════════
// 🖼️ سیستم والپیپر متحرک
// ══════════════════════════════════════════════

function loadWallpaperSettings() {
    const saved = localStorage.getItem('wallpaperSettings');
    if (saved) {
        const settings = JSON.parse(saved);
        wallpaperSpeed = settings.speed || 5000;
        wallpaperTransition = settings.transition || 'fade';
        wallpaperBlur = settings.blur || 5;
        wallpaperDarkness = settings.darkness || 60;

        const speedEl = document.getElementById('wallpaperSpeed');
        const transEl = document.getElementById('wallpaperTransition');
        const blurEl = document.getElementById('wallpaperBlur');
        const darkEl = document.getElementById('wallpaperDarkness');

        if (speedEl) speedEl.value = wallpaperSpeed;
        if (transEl) transEl.value = wallpaperTransition;
        if (blurEl) { blurEl.value = wallpaperBlur; document.getElementById('blurValue').textContent = wallpaperBlur + 'px'; }
        if (darkEl) { darkEl.value = wallpaperDarkness; document.getElementById('darknessValue').textContent = wallpaperDarkness + '%'; }
    }

    applyWallpaperOverlay();

    // رنج اینپوت‌ها
    const blurRange = document.getElementById('wallpaperBlur');
    const darkRange = document.getElementById('wallpaperDarkness');

    if (blurRange) {
        blurRange.addEventListener('input', (e) => {
            wallpaperBlur = parseInt(e.target.value);
            document.getElementById('blurValue').textContent = wallpaperBlur + 'px';
            applyWallpaperBlur();
        });
    }

    if (darkRange) {
        darkRange.addEventListener('input', (e) => {
            wallpaperDarkness = parseInt(e.target.value);
            document.getElementById('darknessValue').textContent = wallpaperDarkness + '%';
            applyWallpaperOverlay();
        });
    }
}

function applyWallpaperOverlay() {
    const overlay = document.querySelector('.wallpaper-overlay');
    if (overlay) {
        overlay.style.background = `rgba(10, 10, 15, ${wallpaperDarkness / 100})`;
    }
}

function applyWallpaperBlur() {
    const slides = document.querySelectorAll('.wallpaper-slide');
    slides.forEach(slide => {
        slide.style.filter = wallpaperBlur > 0 ? `blur(${wallpaperBlur}px)` : 'none';
    });
}

function saveWallpaperSettings() {
    const speed = parseInt(document.getElementById('wallpaperSpeed').value);
    const transition = document.getElementById('wallpaperTransition').value;
    const blur = parseInt(document.getElementById('wallpaperBlur').value);
    const darkness = parseInt(document.getElementById('wallpaperDarkness').value);

    wallpaperSpeed = speed;
    wallpaperTransition = transition;
    wallpaperBlur = blur;
    wallpaperDarkness = darkness;

    localStorage.setItem('wallpaperSettings', JSON.stringify({
        speed, transition, blur, darkness
    }));

    applyWallpaperOverlay();
    applyWallpaperBlur();

    if (wallpapers.length > 0) {
        startWallpaperShow();
    }

    showNotification('✅ تنظیمات والپیپر ذخیره شد!');
}

function loadWallpapers() {
    fetch('/api/wallpapers')
        .then(r => r.json())
        .then(data => {
            wallpapers = data;
            renderWallpaperList();
            if (wallpapers.length > 0) {
                loadWallpaperImages();
            }
        });
}

function loadWallpaperImages() {
    if (wallpapers.length === 0) return;

    // لود اولین والپیپر
    fetch(`/api/wallpapers/${wallpapers[0].id}`)
        .then(r => r.json())
        .then(data => {
            const slide0 = document.getElementById('wallSlide0');
            if (slide0 && data.data) {
                slide0.style.backgroundImage = `url(${data.data})`;
                slide0.style.filter = wallpaperBlur > 0 ? `blur(${wallpaperBlur}px)` : 'none';
                slide0.classList.add('active');
            }
        });

    if (wallpapers.length > 1) {
        startWallpaperShow();
    }
}

function startWallpaperShow() {
    if (wallpaperInterval) clearInterval(wallpaperInterval);
    if (wallpapers.length < 2) return;

    currentWallpaperIndex = 0;
    activeSlide = 0;

    wallpaperInterval = setInterval(() => {
        const nextIndex = (currentWallpaperIndex + 1) % wallpapers.length;
        const nextSlideId = activeSlide === 0 ? 1 : 0;

        fetch(`/api/wallpapers/${wallpapers[nextIndex].id}`)
            .then(r => r.json())
            .then(data => {
                if (!data.data) return;

                const currentSlideEl = document.getElementById(`wallSlide${activeSlide}`);
                const nextSlideEl = document.getElementById(`wallSlide${nextSlideId}`);

                if (!nextSlideEl || !currentSlideEl) return;

                nextSlideEl.style.backgroundImage = `url(${data.data})`;
                nextSlideEl.style.filter = wallpaperBlur > 0 ? `blur(${wallpaperBlur}px)` : 'none';

                if (wallpaperTransition === 'zoom') {
                    nextSlideEl.classList.add('zoom-effect');
                } else {
                    nextSlideEl.classList.remove('zoom-effect');
                }

                if (wallpaperTransition === 'slide') {
                    nextSlideEl.style.transform = 'translateX(-100%)';
                    nextSlideEl.style.transition = 'none';
                    nextSlideEl.classList.add('active');
                    setTimeout(() => {
                        nextSlideEl.style.transition = 'transform 1.5s ease';
                        nextSlideEl.style.transform = 'translateX(0)';
                        currentSlideEl.style.transition = 'transform 1.5s ease';
                        currentSlideEl.style.transform = 'translateX(100%)';
                        setTimeout(() => {
                            currentSlideEl.classList.remove('active');
                            currentSlideEl.style.transform = '';
                            currentSlideEl.style.transition = '';
                        }, 1500);
                    }, 50);
                } else {
                    // fade & zoom
                    nextSlideEl.classList.add('active');
                    setTimeout(() => {
                        currentSlideEl.classList.remove('active');
                    }, 1500);
                }

                activeSlide = nextSlideId;
                currentWallpaperIndex = nextIndex;
            });
    }, wallpaperSpeed);
}

function renderWallpaperList() {
    const list = document.getElementById('wallpaperList');
    if (!list) return;

    if (wallpapers.length === 0) {
        list.innerHTML = '<p style="font-size:12px;color:var(--text-muted);text-align:center;padding:10px">هنوز والپیپری اضافه نشده</p>';
        return;
    }

    list.innerHTML = wallpapers.map((wp, index) => `
        <div class="wallpaper-thumb ${index === currentWallpaperIndex ? 'active' : ''}" id="wpThumb${wp.id}">
            <img src="" data-id="${wp.id}" alt="${wp.filename}" onload="this.style.opacity=1" style="opacity:0;transition:opacity 0.3s">
            <button class="wallpaper-thumb-delete" onclick="deleteWallpaper(${wp.id})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');

    // لود تصاویر thumbnail
    wallpapers.forEach(wp => {
        fetch(`/api/wallpapers/${wp.id}`)
            .then(r => r.json())
            .then(data => {
                const img = list.querySelector(`img[data-id="${wp.id}"]`);
                if (img && data.data) img.src = data.data;
            });
    });
}

function handleWallpaperUpload(files) {
    Array.from(files).forEach(file => {
        if (!file.type.startsWith('image/')) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const data = e.target.result;

            fetch('/api/wallpapers/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: file.name, data: data })
            })
            .then(r => r.json())
            .then(result => {
                if (result.success) {
                    showNotification(`✅ ${file.name} آپلود شد!`);
                    loadWallpapers();
                }
            });
        };
        reader.readAsDataURL(file);
    });
}

function deleteWallpaper(id) {
    fetch('/api/wallpapers/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showNotification('🗑️ والپیپر حذف شد!');
            loadWallpapers();

            if (wallpapers.length <= 1) {
                if (wallpaperInterval) clearInterval(wallpaperInterval);
                document.querySelectorAll('.wallpaper-slide').forEach(s => {
                    s.style.backgroundImage = '';
                    s.classList.remove('active');
                });
            }
        }
    });
}

// ══════════════════════════════════════════════
// Event Listeners
// ══════════════════════════════════════════════

function setupEventListeners() {

    document.querySelectorAll('.platform-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.platform-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentPlatform = btn.dataset.platform;
            currentPage = 1;
            loadNews();
        });
    });

    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTime = btn.dataset.time;
            currentPage = 1;
            loadNews();
        });
    });

    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentType = btn.dataset.type;
            currentPage = 1;
            loadNews();
        });
    });

    document.querySelectorAll('.urgency-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.urgency-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentUrgency = btn.dataset.urgency;
            currentPage = 1;
            loadNews();
        });
    });

    let searchTimeout;
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentSearch = e.target.value;
                currentPage = 1;
                loadNews();
            }, 500);
        });
    }

    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshBtn.classList.add('spinning');
            fetch('/api/refresh', { method: 'POST' })
                .then(() => {
                    showNotification('📡 در حال بروزرسانی...');
                    setTimeout(() => {
                        refreshBtn.classList.remove('spinning');
                        loadStats();
                        loadNews();
                        loadUrgentNews();
                        loadTrendingGames();
                        showNotification('✅ بروزرسانی کامل شد!');
                    }, 12000);
                });
        });
    }

    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            currentPage++;
            loadNews(true);
        });
    }

    document.getElementById('closeTagModal')?.addEventListener('click', () => {
        document.getElementById('tagModal').classList.remove('active');
    });

    document.querySelectorAll('.tag-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (tagArticleId) {
                setTag(tagArticleId, btn.dataset.tag);
                document.getElementById('tagModal').classList.remove('active');
            }
        });
    });

    document.getElementById('closeSourceModal')?.addEventListener('click', () => {
        document.getElementById('sourceModal').classList.remove('active');
    });

    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            currentSection = item.dataset.section;
            currentPage = 1;
            handleSection();
        });
    });

    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.remove('active');
        });
    });

    // والپیپر آپلود
    const wallpaperInput = document.getElementById('wallpaperInput');
    if (wallpaperInput) {
        wallpaperInput.addEventListener('change', (e) => {
            handleWallpaperUpload(e.target.files);
        });
    }

    // Drag & Drop
    const uploadArea = document.getElementById('wallpaperUploadArea');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            handleWallpaperUpload(e.dataTransfer.files);
        });
    }

    // فیلتر منابع
    document.querySelectorAll('.source-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.source-filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterSources(btn.dataset.filter);
        });
    });
}

// ──────── Section Handler ────────
function handleSection() {
    const newsGrid = document.getElementById('newsGrid');
    const loadMoreWrapper = document.getElementById('loadMoreWrapper');
    const sourcesSection = document.getElementById('sourcesSection');
    const trendsSection = document.getElementById('trendsSection');
    const settingsSection = document.getElementById('settingsSection');
    const filtersBar = document.getElementById('filtersBar');
    const trendingSection = document.getElementById('trendingSection');
    const urgentBar = document.getElementById('urgentBar');

    // پنهان کردن همه
    [newsGrid, loadMoreWrapper, sourcesSection, trendsSection, settingsSection].forEach(el => {
        if (el) el.style.display = 'none';
    });

    switch (currentSection) {
        case 'dashboard':
        case 'news':
            if (newsGrid) newsGrid.style.display = 'grid';
            if (filtersBar) filtersBar.style.display = 'flex';
            if (trendingSection && wallpapers.length > 0) trendingSection.style.display = 'block';
            loadNews();
            break;

        case 'trends':
            if (trendsSection) trendsSection.style.display = 'block';
            if (filtersBar) filtersBar.style.display = 'none';
            if (trendingSection) trendingSection.style.display = 'none';
            loadTrendsSection();
            break;

        case 'bookmarks':
            if (newsGrid) newsGrid.style.display = 'grid';
            if (filtersBar) filtersBar.style.display = 'none';
            if (trendingSection) trendingSection.style.display = 'none';
            loadBookmarks();
            break;

        case 'trailers':
            if (newsGrid) newsGrid.style.display = 'grid';
            if (filtersBar) filtersBar.style.display = 'none';
            if (trendingSection) trendingSection.style.display = 'none';
            loadTrailers();
            break;

        case 'sources':
            if (sourcesSection) sourcesSection.style.display = 'block';
            if (filtersBar) filtersBar.style.display = 'none';
            if (trendingSection) trendingSection.style.display = 'none';
            loadSources();
            break;

        case 'settings':
            if (settingsSection) settingsSection.style.display = 'block';
            if (filtersBar) filtersBar.style.display = 'none';
            if (trendingSection) trendingSection.style.display = 'none';
            renderWallpaperList();
            break;
    }
}

// ──────── Load Stats ────────
function loadStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            animateNumber('statToday', data.today);
            animateNumber('statTotal', data.total);
            animateNumber('statSources', data.sources);
            animateNumber('statBookmarked', data.bookmarked);
            animateNumber('statVideos', data.video_count);
            animateNumber('statUrgent', data.urgent_count);
        });
}

function animateNumber(elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const start = parseInt(el.textContent) || 0;
    const diff = target - start;
    const steps = 20;
    let step = 0;
    const interval = setInterval(() => {
        step++;
        el.textContent = Math.round(start + (diff * step / steps)).toLocaleString('fa-IR');
        if (step >= steps) clearInterval(interval);
    }, 30);
}

// ──────── اخبار فوری ────────
function loadUrgentNews() {
    fetch('/api/urgent')
        .then(r => r.json())
        .then(data => {
            const bar = document.getElementById('urgentBar');
            const list = document.getElementById('urgentList');
            if (!bar || !list) return;

            if (data.length === 0) { bar.style.display = 'none'; return; }

            bar.style.display = 'flex';
            list.innerHTML = data.slice(0, 5).map(a => `
                <a href="${a.link}" target="_blank" class="urgent-item">🔴 ${a.title}</a>
            `).join('');
        });
}

// ──────── ترندینگ ────────
function loadTrendingGames() {
    fetch('/api/trending-games')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('trendingGames');
            const section = document.getElementById('trendingSection');
            if (!container || !section) return;

            if (data.length === 0) { section.style.display = 'none'; return; }

            section.style.display = 'block';
            const maxCount = data[0]?.count || 1;
            container.innerHTML = data.map((game, i) => `
                <button class="game-tag" onclick="searchGame('${game.name}')">
                    <span class="game-rank">${i + 1}</span>
                    ${game.name}
                    <span class="game-count">${game.count}</span>
                    <div class="game-bar" style="width:${(game.count/maxCount)*100}%"></div>
                </button>
            `).join('');

            const el = document.getElementById('lastUpdateText');
            if (el) el.textContent = `— ${new Date().toLocaleTimeString('fa-IR')}`;
        });
}

// ══════════════════════════════════════════════
// 📈 بخش ترندز
// ══════════════════════════════════════════════

function loadTrendsSection() {
    loadInternalTrends();
    loadGoogleTrends();
}

function loadInternalTrends() {
    const el = document.getElementById('internalTrends');
    if (!el) return;
    el.innerHTML = '<div class="loading-small">در حال تحلیل...</div>';

    fetch('/api/trends/internal')
        .then(r => r.json())
        .then(data => {
            if (!data.top_words || data.top_words.length === 0) {
                el.innerHTML = '<p class="loading-small">داده‌ای یافت نشد</p>';
                return;
            }

            const maxCount = data.top_words[0]?.count || 1;

            el.innerHTML = `
                <div class="trend-word-list">
                    ${data.top_words.slice(0, 10).map((word, i) => `
                        <div class="trend-word-item">
                            <span class="trend-word-rank">${i + 1}</span>
                            <span class="trend-word-text">${word.word}</span>
                            <div class="trend-word-bar-wrap">
                                <div class="trend-word-bar" style="width:${(word.count/maxCount)*100}%"></div>
                            </div>
                            <span class="trend-word-count">${word.count}</span>
                        </div>
                    `).join('')}
                </div>
                <p style="font-size:10px;color:var(--text-muted);margin-top:10px;text-align:center">
                    بر اساس ${data.total_articles} خبر ۲۴ ساعت گذشته
                </p>
            `;

            // ترند پلتفرم
            const platformEl = document.getElementById('platformTrends');
            if (platformEl && data.platform_trends) {
                platformEl.innerHTML = `
                    <div class="platform-trends-grid">
                        ${Object.entries(data.platform_trends)
                            .filter(([p, words]) => words.length > 0)
                            .map(([platform, words]) => `
                                <div class="platform-trend-col">
                                    <div class="platform-trend-title">
                                        ${getPlatformIcon(platform)} ${platform}
                                    </div>
                                    ${words.map(w => `
                                        <div class="platform-trend-word">
                                            <span>${w.word}</span>
                                            <span>${w.count}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            `).join('')}
                    </div>
                `;
            }
        });
}

function loadGoogleTrends() {
    const googleEl = document.getElementById('googleTrends');
    const iranEl = document.getElementById('iranTrends');
    const relatedEl = document.getElementById('relatedQueries');

    fetch('/api/trends')
        .then(r => r.json())
        .then(data => {
            // Google Trends جهانی
            if (googleEl) {
                if (!data.global || Object.keys(data.global).length === 0) {
                    googleEl.innerHTML = '<p class="loading-small">در حال دریافت از Google Trends...</p>';
                } else {
                    const maxVal = Math.max(...Object.values(data.global)) || 1;
                    googleEl.innerHTML = `
                        <div class="google-trend-list">
                            ${Object.entries(data.global).map(([name, value]) => `
                                <div class="google-trend-item">
                                    <span class="google-trend-name">${name}</span>
                                    <div class="google-trend-bar-wrap">
                                        <div class="google-trend-bar" style="width:${(value/maxVal)*100}%"></div>
                                    </div>
                                    <span class="google-trend-value">${value}</span>
                                </div>
                            `).join('')}
                        </div>
                        ${data.updated_at ? `<p style="font-size:10px;color:var(--text-muted);margin-top:8px;text-align:center">آپدیت: ${timeAgo(data.updated_at)}</p>` : ''}
                    `;
                }
            }

            // ترند ایران
            if (iranEl) {
                if (!data.iran || Object.keys(data.iran).length === 0) {
                    iranEl.innerHTML = '<p class="loading-small">در حال دریافت ترند ایران...</p>';
                } else {
                    iranEl.innerHTML = `
                        <div class="iran-trend-list">
                            ${Object.entries(data.iran).map(([name, value]) => `
                                <span class="iran-trend-tag">
                                    🇮🇷 ${name}
                                    <strong>${value}</strong>
                                </span>
                            `).join('')}
                        </div>
                    `;
                }
            }

            // سرچ‌های مرتبط
            if (relatedEl) {
                if (!data.related || data.related.length === 0) {
                    relatedEl.innerHTML = '<p class="loading-small">در حال دریافت...</p>';
                } else {
                    relatedEl.innerHTML = `
                        <div class="related-list">
                            ${data.related.map(q => `
                                <span class="related-tag">${q.query || q}</span>
                            `).join('')}
                        </div>
                    `;
                }
            }
        });
}

function doCompare() {
    const kw1 = document.getElementById('compareKw1').value.trim();
    const kw2 = document.getElementById('compareKw2').value.trim();
    const resultEl = document.getElementById('compareResult');

    if (!kw1 || !kw2) {
        showNotification('⚠️ دو کلمه وارد کن!');
        return;
    }

    if (resultEl) resultEl.innerHTML = '<div class="loading-small">در حال مقایسه...</div>';

    fetch(`/api/trends/compare?kw1=${encodeURIComponent(kw1)}&kw2=${encodeURIComponent(kw2)}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                resultEl.innerHTML = `<p class="loading-small" style="color:var(--danger)">${data.error}</p>`;
                return;
            }

            const max = Math.max(data[kw1] || 0, data[kw2] || 0) || 1;

            resultEl.innerHTML = `
                <div class="compare-bars">
                    <div class="compare-bar-item">
                        <span class="compare-bar-label">${kw1}</span>
                        <div class="compare-bar-wrap">
                            <div class="compare-bar-fill kw1" style="width:${((data[kw1]||0)/max)*100}%">
                                ${data[kw1] || 0}
                            </div>
                        </div>
                    </div>
                    <div class="compare-bar-item">
                        <span class="compare-bar-label">${kw2}</span>
                        <div class="compare-bar-wrap">
                            <div class="compare-bar-fill kw2" style="width:${((data[kw2]||0)/max)*100}%">
                                ${data[kw2] || 0}
                            </div>
                        </div>
                    </div>
                </div>
                <p style="font-size:10px;color:var(--text-muted);margin-top:8px;text-align:center">
                    میانگین ۷ روز گذشته
                </p>
            `;
        });
}

// ══════════════════════════════════════════════
// مدیریت منابع
// ══════════════════════════════════════════════

function loadSources() {
    const grid = document.getElementById('sourcesGrid');
    const summary = document.getElementById('sourcesSummary');
    if (!grid) return;

    grid.innerHTML = '<div style="padding:20px;color:var(--text-secondary);font-size:12px">در حال بارگذاری...</div>';

    fetch('/api/sources')
        .then(r => r.json())
        .then(data => {
            // خلاصه وضعیت
            const activeWithArticles = data.filter(s => s.is_active && s.article_count > 0).length;
            const activeEmpty = data.filter(s => s.is_active && (!s.article_count || s.article_count === 0)).length;
            const inactive = data.filter(s => !s.is_active).length;
            const total = data.length;

            if (summary) {
                summary.innerHTML = `
                    <div class="summary-card">
                        <div class="summary-card-number">${total}</div>
                        <div class="summary-card-label">کل منابع</div>
                    </div>
                    <div class="summary-card active">
                        <div class="summary-card-number">${activeWithArticles}</div>
                        <div class="summary-card-label">✅ پرخبر</div>
                    </div>
                    <div class="summary-card empty">
                        <div class="summary-card-number">${activeEmpty}</div>
                        <div class="summary-card-label">⚠️ بدون خبر</div>
                    </div>
                    <div class="summary-card inactive">
                        <div class="summary-card-number">${inactive}</div>
                        <div class="summary-card-label">❌ غیرفعال</div>
                    </div>
                `;
            }

            // ذخیره داده برای فیلتر
            grid.dataset.allSources = JSON.stringify(data);
            renderSourceCards(data);
        });
}

function filterSources(filter) {
    const grid = document.getElementById('sourcesGrid');
    if (!grid || !grid.dataset.allSources) return;

    const allSources = JSON.parse(grid.dataset.allSources);
    let filtered = allSources;

    if (filter === 'active') {
        filtered = allSources.filter(s => s.is_active && s.article_count > 0);
    } else if (filter === 'empty') {
        filtered = allSources.filter(s => s.is_active && (!s.article_count || s.article_count === 0));
    } else if (filter === 'inactive') {
        filtered = allSources.filter(s => !s.is_active);
    }

    renderSourceCards(filtered);
}

function renderSourceCards(sources) {
    const grid = document.getElementById('sourcesGrid');
    if (!grid) return;

    if (sources.length === 0) {
        grid.innerHTML = '<div style="padding:20px;color:var(--text-secondary);font-size:12px">منبعی یافت نشد</div>';
        return;
    }

    grid.innerHTML = sources.map(source => {
        const hasArticles = source.article_count > 0;
        const isActive = source.is_active;
        const statusClass = !isActive ? 'inactive' : hasArticles ? 'active' : 'empty';
        const cardClass = !isActive ? 'inactive' : !hasArticles ? 'no-articles' : '';

        return `
            <div class="source-card ${cardClass}">
                <div class="source-status-dot ${statusClass}"></div>
                <div class="source-info">
                    <h4>${source.name}</h4>
                    <div class="source-info-details">
                        <span class="source-article-count ${hasArticles ? '' : 'zero'}">
                            ${source.article_count || 0} خبر
                        </span>
                        <span class="source-last-update">
                            ${source.last_fetch ? timeAgo(source.last_fetch) : 'هنوز چک نشده'}
                        </span>
                    </div>
                </div>
                <span class="source-platform-badge">${getPlatformIcon(source.platform)} ${source.platform}</span>
                <div class="source-actions">
                    <button class="source-btn toggle-off" onclick="toggleSource(${source.id})" title="${isActive ? 'غیرفعال' : 'فعال'}">
                        <i class="fas fa-${isActive ? 'pause' : 'play'}"></i>
                    </button>
                    <button class="source-btn" onclick="openEditSourceModal(${source.id}, '${source.name.replace(/'/g,"\\'")}', '${source.url}', '${source.platform}')" title="ویرایش">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="source-btn delete" onclick="deleteSource(${source.id}, '${source.name.replace(/'/g,"\\'")}')'" title="حذف">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function openAddSourceModal() {
    editingSourceId = null;
    document.getElementById('sourceModalTitle').textContent = '➕ منبع جدید';
    document.getElementById('sourceId').value = '';
    document.getElementById('sourceName').value = '';
    document.getElementById('sourceUrl').value = '';
    document.getElementById('sourcePlatform').value = 'General';
    document.getElementById('sourceModal').classList.add('active');
}

function openEditSourceModal(id, name, url, platform) {
    editingSourceId = id;
    document.getElementById('sourceModalTitle').textContent = '✏️ ویرایش منبع';
    document.getElementById('sourceId').value = id;
    document.getElementById('sourceName').value = name;
    document.getElementById('sourceUrl').value = url;
    document.getElementById('sourcePlatform').value = platform;
    document.getElementById('sourceModal').classList.add('active');
}

function saveSource() {
    const id = document.getElementById('sourceId').value;
    const name = document.getElementById('sourceName').value.trim();
    const url = document.getElementById('sourceUrl').value.trim();
    const platform = document.getElementById('sourcePlatform').value;

    if (!name || !url) { showNotification('⚠️ نام و آدرس RSS الزامیست!'); return; }

    const endpoint = id ? '/api/sources/edit' : '/api/sources/add';
    const body = id ? { id, name, url, platform } : { name, url, platform };

    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            document.getElementById('sourceModal').classList.remove('active');
            showNotification(id ? '✅ منبع ویرایش شد!' : '✅ منبع جدید اضافه شد!');
            loadSources();
        } else {
            showNotification(`⚠️ ${data.error || 'خطا!'}`);
        }
    });
}

function deleteSource(id, name) {
    if (!confirm(`آیا مطمئنی که می‌خوای "${name}" رو حذف کنی؟`)) return;

    fetch('/api/sources/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) { showNotification('🗑️ منبع حذف شد!'); loadSources(); }
    });
}

function toggleSource(id) {
    fetch('/api/sources/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) { showNotification('✅ وضعیت منبع تغییر کرد!'); loadSources(); }
    });
}

// ──────── Load News ────────
function loadNews(append = false) {
    const grid = document.getElementById('newsGrid');
    const loadMoreWrapper = document.getElementById('loadMoreWrapper');
    if (!grid) return;

    if (!append) {
        grid.innerHTML = '';
        grid.appendChild(createLoadingState());
    }

    const params = new URLSearchParams({
        platform: currentPlatform,
        type: currentType,
        time: currentTime,
        urgency: currentUrgency,
        search: currentSearch,
        bookmarked: currentSection === 'bookmarks' ? 'true' : 'false',
        page: currentPage
    });

    fetch(`/api/news?${params}`)
        .then(r => r.json())
        .then(data => {
            if (!append) grid.innerHTML = '';

            if (data.articles.length === 0 && !append) {
                grid.innerHTML = createEmptyState();
                if (loadMoreWrapper) loadMoreWrapper.style.display = 'none';
                return;
            }

            data.articles.forEach(article => grid.appendChild(createNewsCard(article)));

            if (loadMoreWrapper) {
                loadMoreWrapper.style.display = data.has_more ? 'block' : 'none';
            }
        })
        .catch(() => {
            if (!append) grid.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>خطا در دریافت اخبار...</p></div>`;
        });
}

function loadBookmarks() { currentSearch = ''; currentPage = 1; loadNews(); }

function loadTrailers() {
    const grid = document.getElementById('newsGrid');
    if (!grid) return;
    grid.innerHTML = '';
    grid.appendChild(createLoadingState());

    fetch(`/api/news?platform=all&type=all&time=all&search=trailer&page=1`)
        .then(r => r.json())
        .then(data => {
            grid.innerHTML = '';
            const trailers = data.articles.filter(a => a.has_video);
            if (trailers.length === 0) { grid.innerHTML = createEmptyState('تریلری یافت نشد'); return; }
            trailers.forEach(a => grid.appendChild(createNewsCard(a)));
        });
}

function searchGame(gameName) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) { searchInput.value = gameName; currentSearch = gameName; }
    currentPage = 1;
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    document.querySelector('[data-section="news"]')?.classList.add('active');
    currentSection = 'news';
    handleSection();
}

// ──────── Create News Card ────────
function createNewsCard(article) {
    const card = document.createElement('div');
    card.className = `news-card urgency-${article.urgency || 'normal'}`;
    card.id = `article-${article.id}`;

    const platforms = article.detected_platforms ? article.detected_platforms.split(',') : ['General'];
    const platformBadges = platforms.map(p =>
        `<span class="platform-badge ${p.trim()}">${getPlatformIcon(p.trim())} ${p.trim()}</span>`
    ).join('');

    const typeLabels = {
        'news': '📰 خبر', 'review': '⭐ بررسی', 'preview': '👁️ پیش‌نمایش',
        'interview': '🎤 مصاحبه', 'analysis': '📊 تحلیل', 'guide': '📖 راهنما',
        'list': '📋 لیست', 'deal': '💰 تخفیف', 'tech': '⚙️ تکنولوژی'
    };

    const urgencyBadge = article.urgency === 'high'
        ? '<span class="urgency-badge high">🔴 فوری</span>'
        : article.urgency === 'medium'
        ? '<span class="urgency-badge medium">🟡 مهم</span>'
        : '';

    const imageHtml = article.image_url
        ? `<img class="news-card-image" src="${article.image_url}" alt="" loading="lazy" onerror="this.style.display='none'">`
        : '';

    const videoBadge = article.has_video ? '<span class="video-badge">🎬 ویدیو</span>' : '';
    const tagBadge = article.custom_tag ? `<span class="custom-tag-badge">🏷️ ${article.custom_tag}</span>` : '';

    const gameTags = article.game_tags
        ? article.game_tags.split(',').filter(g => g.trim()).slice(0, 3)
            .map(g => `<span class="game-mini-tag" onclick="searchGame('${g.trim()}')">${g.trim()}</span>`).join('')
        : '';

    const summaryHtml = article.summary_fa
        ? `<p class="news-card-summary fa">${article.summary_fa}</p>`
        : article.summary
        ? `<p class="news-card-summary">${article.summary}</p>`
        : '';

    const sourcePlatformColors = {
        'PlayStation': 'var(--ps-color)', 'Xbox': 'var(--xbox-color)',
        'Nintendo': 'var(--nintendo-color)', 'PC': 'var(--pc-color)',
        'Mobile': 'var(--mobile-color)', 'General': 'var(--accent)'
    };
    const sourceColor = sourcePlatformColors[article.source_platform] || 'var(--accent)';

    card.innerHTML = `
        ${imageHtml}
        <div class="news-card-body">
            <div class="news-card-meta">
                ${urgencyBadge}
                <span class="source-badge" style="background:${sourceColor}">${article.source}</span>
                ${platformBadges}
                <span class="type-badge">${typeLabels[article.content_type] || '📰 خبر'}</span>
                ${videoBadge}
                ${tagBadge}
            </div>
            <h3 class="news-card-title">
                <a href="${article.link}" target="_blank" rel="noopener">${article.title}</a>
            </h3>
            ${summaryHtml}
            ${gameTags ? `<div class="game-tags-row">${gameTags}</div>` : ''}
            <div class="news-card-footer">
                <span class="news-time">${timeAgo(article.fetched_at)}</span>
                <div class="news-actions">
                    <button class="action-btn ${article.is_bookmarked ? 'bookmarked' : ''}"
                            onclick="toggleBookmark(${article.id})" title="ذخیره">
                        <i class="fas fa-bookmark"></i>
                    </button>
                    <button class="action-btn" onclick="openTagModal(${article.id})" title="برچسب">
                        <i class="fas fa-tag"></i>
                    </button>
                    <button class="action-btn" onclick="window.open('${article.link}', '_blank')" title="مشاهده">
                        <i class="fas fa-external-link-alt"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    return card;
}

// ──────── Helpers ────────
function getPlatformIcon(platform) {
    const icons = { 'PlayStation': '🎮', 'Xbox': '🟩', 'Nintendo': '🔴', 'PC': '🖥️', 'Mobile': '📱', 'General': '🌐' };
    return icons[platform] || '🌐';
}

function timeAgo(dateString) {
    if (!dateString) return '';
    const diff = Math.floor((new Date() - new Date(dateString)) / 1000);
    if (diff < 60) return 'همین الان';
    if (diff < 3600) return `${Math.floor(diff / 60)} دقیقه پیش`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} ساعت پیش`;
    return `${Math.floor(diff / 86400)} روز پیش`;
}

function createLoadingState() {
    const div = document.createElement('div');
    div.className = 'loading-state';
    div.innerHTML = `<div class="spinner"></div><p>در حال دریافت اخبار...</p>`;
    return div;
}

function createEmptyState(message = 'خبری یافت نشد') {
    return `<div class="empty-state"><i class="fas fa-inbox"></i><p>${message}</p></div>`;
}

// ──────── Actions ────────
function toggleBookmark(id) {
    fetch('/api/bookmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    })
    .then(r => r.json())
    .then(data => {
        const card = document.getElementById(`article-${id}`);
        if (!card) return;
        const btn = card.querySelector('.action-btn');
        if (data.bookmarked) { btn.classList.add('bookmarked'); showNotification('✅ ذخیره شد!'); }
        else { btn.classList.remove('bookmarked'); showNotification('❌ از ذخیره‌شده‌ها حذف شد'); }
        loadStats();
    });
}

function openTagModal(id) {
    tagArticleId = id;
    document.getElementById('tagModal').classList.add('active');
}

function setTag(id, tag) {
    fetch('/api/tag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, tag })
    })
    .then(r => r.json())
    .then(() => {
        showNotification(tag ? `🏷️ برچسب "${tag}" اضافه شد` : '🏷️ برچسب حذف شد');
        loadNews();
    });
}

function showNotification(text) {
    const notif = document.getElementById('notification');
    const notifText = document.getElementById('notifText');
    if (!notif || !notifText) return;
    notifText.textContent = text;
    notif.classList.add('show');
    setTimeout(() => notif.classList.remove('show'), 3000);
}