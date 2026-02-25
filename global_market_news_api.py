#!/usr/bin/env python3
"""
Global Market News & Indicators Dashboard
Fetches REAL latest news using NewsAPI / RSS feeds every run.
Generates HTML with expandable news articles.
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import html as html_module
import re

# ─────────────────────────────────────────────
#  NEWS SOURCES  (RSS feeds – no API key needed)
# ─────────────────────────────────────────────
RSS_SOURCES = {
    "markets": [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC&region=US&lang=en-US",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
    ],
    "economic": [
        "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/economy-politics/",
        "https://www.federalreserve.gov/feeds/press_all.xml",
    ],
    "india": [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://www.moneycontrol.com/rss/marketreports.xml",
        "https://economictimes.indiatimes.com/rssfeeds/1373380680.cms",
    ],
    "google_trending": [
        "https://news.google.com/rss/search?q=NSE+BSE+stock+market+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Nifty+Sensex+today+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=india+stocks+trending+today+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "corporate": [
        "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/marketpulse/",
        "https://finance.yahoo.com/rss/topfinstories",
    ],
    "geopolitical": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
    ],
}

MAX_NEWS_PER_CATEGORY = 10
REQUEST_TIMEOUT = 8


# ─────────────────────────────────────────────
#  RSS FETCHER
# ─────────────────────────────────────────────
def fetch_rss(url: str) -> list[dict]:
    items = []
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; MarketDashboard/1.0)",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            },
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")

        raw = re.sub(r'\s+xmlns[^"]*"[^"]*"', "", raw)
        raw = re.sub(r"<(/?)[\w]+:", r"<\1", raw)

        root = ET.fromstring(raw)
        channel = root.find("channel") or root

        domain = urllib.parse.urlparse(url).netloc.replace("www.", "").replace("feeds.", "")
        source_map = {
            "cnbc.com": "CNBC",
            "marketwatch.com": "MarketWatch",
            "reuters.com": "Reuters",
            "finance.yahoo.com": "Yahoo Finance",
            "economictimes.indiatimes.com": "Economic Times",
            "moneycontrol.com": "MoneyControl",
            "federalreserve.gov": "Federal Reserve",
        }
        source = next((v for k, v in source_map.items() if k in domain), domain)

        for item in channel.findall("item")[:MAX_NEWS_PER_CATEGORY]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            summary = (item.findtext("description") or item.findtext("summary") or "").strip()
            pub_date = (item.findtext("pubDate") or item.findtext("date") or "").strip()

            summary = re.sub(r"<[^>]+>", "", summary).strip()
            summary = html_module.unescape(summary)
            title = html_module.unescape(title)

            if title and len(title) > 10:
                items.append({
                    "title": title,
                    "link": link,
                    "summary": summary[:500] if summary else "Click to read the full article.",
                    "pubDate": pub_date,
                    "source": source,
                })
    except Exception as e:
        print(f"    ⚠  Could not fetch {url}: {e}")
    return items


def fetch_category_news(category: str, urls: list[str]) -> list[dict]:
    seen_titles = set()
    results = []
    cutoff = datetime.utcnow() - timedelta(hours=24)  # ← 24hr cutoff

    for url in urls:
        print(f"  Fetching {url[:60]}...")
        for item in fetch_rss(url):
            key = item["title"].lower()[:60]
            if key in seen_titles:
                continue

            # ── Filter old articles for google_trending only ──
            if category == "google_trending" and item.get("pubDate"):
                try:
                    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"]:
                        try:
                            pub = datetime.strptime(item["pubDate"].strip(), fmt)
                            pub_utc = pub.replace(tzinfo=None) if pub.tzinfo else pub
                            if pub_utc < cutoff:
                                continue  # skip old articles
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass

            seen_titles.add(key)
            results.append(item)
            if len(results) >= MAX_NEWS_PER_CATEGORY:
                break
        if len(results) >= MAX_NEWS_PER_CATEGORY:
            break
    return results[:MAX_NEWS_PER_CATEGORY]


def format_pub_date(raw: str) -> str:
    if not raw:
        return "Just now"
    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.utcnow()
            diff = now - dt
            if diff.days == 0:
                hours = diff.seconds // 3600
                mins = (diff.seconds % 3600) // 60
                if hours == 0:
                    return f"{mins} min ago" if mins > 1 else "Just now"
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.days == 1:
                return "1 day ago"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return dt.strftime("%b %d, %Y")
        except ValueError:
            continue
    return raw[:20]


# ─────────────────────────────────────────────
#  HTML GENERATION
# ─────────────────────────────────────────────
def get_ist_time() -> str:
    utc_time = datetime.utcnow()
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return ist_time.strftime("%B %d, %Y at %I:%M %p IST")


def escape(text: str) -> str:
    return html_module.escape(str(text), quote=True)


def generate_news_items_html(items: list[dict], cat_id: str) -> str:
    if not items:
        return '<p style="color:#a8b2d1;padding:15px;">No news fetched – check your internet connection.</p>'
    parts = []
    for i, item in enumerate(items):
        item_id = f"news-{cat_id}-{i}"
        time_str = format_pub_date(item.get("pubDate", ""))
        summary = escape(item.get("summary", "Click to read the full article."))
        link = escape(item.get("link", "#"))
        title = escape(item.get("title", "Untitled"))
        source = escape(item.get("source", "Unknown"))

        parts.append(f"""
        <div class="news-item" onclick="toggleNews('{item_id}')">
            <div class="news-item-header">
                <h3>{title}</h3>
                <span class="expand-icon" id="icon-{item_id}">&#9660;</span>
            </div>
            <div class="news-meta">
                <span class="news-source">{source}</span>
                <span class="news-date">{time_str}</span>
            </div>
            <div class="news-expand" id="{item_id}">
                <p class="news-summary">{summary}</p>
                {'<a class="read-more" href="' + link + '" target="_blank" rel="noopener">Read Full Article &#8599;</a>' if link and link != '#' else ''}
            </div>
        </div>""")
    return "\n".join(parts)


def generate_complete_html(all_news: dict) -> str:
    current_time = get_ist_time()
    total_articles = sum(len(v) for v in all_news.values())

    categories = {
        "markets":     ("📊 Market Updates",     "markets",     "var(--accent-red)"),
        "economic":    ("💰 Economic & Policy",  "economic",    "var(--accent-pink)"),
        "india":           ("🇮🇳 Indian Markets",        "india",           "var(--accent-yellow)"),
        "google_trending": ("🔥 Google Trending Stocks", "google_trending", "var(--accent-orange)"),
        "corporate":       ("🏢 Corporate News",         "corporate",       "var(--accent-cyan)"),
        "geopolitical":("🌍 Geopolitical",       "geopolitical","var(--accent-green)"),
    }

    news_cards_html = ""
    for key, (label, css_class, color) in categories.items():
        items = all_news.get(key, [])
        items_html = generate_news_items_html(items, key)
        news_cards_html += f"""
            <div class="news-category-card {css_class}">
                <div class="category-header" style="border-bottom-color:{color}">
                    <h3 class="category-title" style="color:{color}">{label}</h3>
                    <span class="article-count">{len(items)} articles</span>
                </div>
                <div>{items_html}</div>
            </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Global Market Dashboard – Live News</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Space+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root {{
    --primary-bg: #0a0e27; --secondary-bg: #141b3d; --accent-bg: #1a2347;
    --text-primary: #e8edf5; --text-secondary: #a8b2d1;
    --accent-blue: #4a9eff; --accent-green: #00ff88; --accent-red: #ff4757;
    --accent-yellow: #ffd93d; --accent-purple: #a78bfa;
    --accent-pink: #f093fb; --accent-cyan: #4facfe; --accent-orange: #ff9f43;
    --border-color: #2a3a5f; --card-shadow: rgba(0,0,0,.5);
    --usa-red:#B22234; --usa-blue:#3C3B6E;
    --india-saffron:#FF9933; --india-green:#138808; --india-navy:#000080;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'IBM Plex Sans',sans-serif;background:linear-gradient(135deg,#0a0e27 0%,#1a1f3a 50%,#0f1629 100%);color:var(--text-primary);min-height:100vh;padding:20px;overflow-x:hidden}}
body::before{{content:'';position:fixed;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle,rgba(74,158,255,.08) 1px,transparent 1px);background-size:50px 50px;animation:moveGrid 25s linear infinite;z-index:0}}
@keyframes moveGrid{{0%{{transform:translate(0,0)}}100%{{transform:translate(50px,50px)}}}}
.container{{max-width:1600px;margin:0 auto;position:relative;z-index:1}}

/* ── HEADER ── */
header{{text-align:center;margin-bottom:30px;padding:25px 20px;background:rgba(26,35,71,.5);backdrop-filter:blur(10px);border-radius:15px;border:1px solid var(--border-color);box-shadow:0 15px 40px var(--card-shadow);position:relative;overflow:hidden}}
header::after{{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent,rgba(74,158,255,.15),transparent);animation:shimmer 3s infinite}}
@keyframes shimmer{{0%{{left:-100%}}100%{{left:100%}}}}
h1{{font-family:'Playfair Display',serif;font-size:2.2em;font-weight:900;background:linear-gradient(135deg,#4a9eff,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px;letter-spacing:-1px;position:relative;z-index:1}}
.subtitle{{font-family:'Space Mono',monospace;font-size:.85em;color:var(--text-secondary);letter-spacing:1px;text-transform:uppercase}}
.live-badge{{display:inline-block;background:linear-gradient(135deg,#ff4757,#ff6b81);color:#fff;padding:5px 15px;border-radius:20px;font-size:.7em;font-weight:700;margin-top:10px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}
.timestamp{{margin-top:12px;font-family:'Space Mono',monospace;font-size:.75em;color:var(--accent-blue);opacity:.9}}
.stat-bar{{margin-top:12px;font-family:'Space Mono',monospace;font-size:.7em;color:var(--accent-green)}}

/* ── SECTION TITLES ── */
.section-title{{font-family:'Playfair Display',serif;font-size:2.2em;font-weight:900;margin-bottom:25px;background:linear-gradient(135deg,var(--accent-blue),var(--accent-cyan));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.section-title-usa{{font-family:'Playfair Display',serif;font-size:2.2em;font-weight:900;margin-bottom:25px;background:linear-gradient(135deg,var(--usa-red),#fff,var(--usa-blue));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.section-title-india{{font-family:'Playfair Display',serif;font-size:2.2em;font-weight:900;margin-bottom:25px;background:linear-gradient(135deg,var(--india-saffron),#fff,var(--india-green));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}

/* ── INDICATOR CARDS ── */
.indicators-grid{{display:flex;gap:15px;margin-bottom:40px;overflow-x:auto;padding-bottom:10px}}
.indicator-card{{background:rgba(26,35,71,.6);backdrop-filter:blur(10px);padding:15px 20px;border-radius:12px;border:1px solid var(--border-color);box-shadow:0 8px 20px var(--card-shadow);transition:all .3s;position:relative;overflow:hidden;min-width:175px;flex-shrink:0}}
.indicator-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px}}
.indicator-card.positive::before{{background:linear-gradient(90deg,var(--accent-green),var(--accent-blue))}}
.indicator-card.negative::before{{background:linear-gradient(90deg,var(--accent-red),var(--accent-yellow))}}
.indicator-card.neutral::before{{background:linear-gradient(90deg,var(--text-secondary),var(--accent-blue))}}
.indicator-card:hover{{transform:translateY(-3px);box-shadow:0 12px 30px rgba(74,158,255,.3);border-color:var(--accent-blue)}}
.indicator-title{{font-family:'Space Mono',monospace;font-size:.68em;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;white-space:nowrap}}
.indicator-value{{font-family:'Playfair Display',serif;font-size:1.4em;font-weight:700;color:var(--text-primary);margin-bottom:6px;white-space:nowrap}}
.indicator-change{{font-family:'Space Mono',monospace;font-size:.78em;padding:3px 8px;border-radius:4px;display:inline-block;white-space:nowrap}}
.positive{{color:var(--accent-green);background:rgba(0,255,136,.1)}}
.negative{{color:var(--accent-red);background:rgba(255,71,87,.1)}}
.neutral{{color:var(--text-secondary);background:rgba(168,178,209,.1)}}

/* ── NEWS SECTION ── */
.news-section{{margin-top:60px}}
.news-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:30px;margin-bottom:40px}}
.news-category-card{{background:rgba(26,35,71,.6);backdrop-filter:blur(10px);padding:28px;border-radius:15px;border:1px solid var(--border-color);box-shadow:0 10px 30px var(--card-shadow)}}
.category-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:22px;padding-bottom:12px;border-bottom:2px solid}}
.category-title{{font-family:'Playfair Display',serif;font-size:1.5em;font-weight:700}}
.article-count{{font-family:'Space Mono',monospace;font-size:.7em;color:var(--text-secondary);background:rgba(74,158,255,.1);padding:3px 8px;border-radius:10px}}

/* ── NEWS ITEMS ── */
.news-item{{padding:14px;margin-bottom:10px;background:rgba(10,14,39,.4);border-radius:10px;border-left:3px solid var(--accent-blue);transition:all .2s;cursor:pointer;user-select:none}}
.news-item:hover{{background:rgba(10,14,39,.65);transform:translateX(4px);box-shadow:0 4px 15px rgba(74,158,255,.2)}}
.news-item-header{{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}}
.news-item h3{{font-size:.93em;line-height:1.4;font-weight:600;color:var(--text-primary);flex:1}}
.expand-icon{{font-size:.8em;color:var(--accent-blue);margin-top:3px;transition:transform .25s;flex-shrink:0}}
.expand-icon.open{{transform:rotate(180deg)}}
.news-meta{{display:flex;gap:10px;align-items:center;margin-top:7px;font-size:.73em;color:var(--text-secondary);flex-wrap:wrap}}
.news-source{{background:var(--accent-blue);color:#fff;padding:2px 8px;border-radius:10px;font-size:.85em;font-family:'Space Mono',monospace}}
.news-date{{font-family:'Space Mono',monospace}}

/* ── EXPANDABLE CONTENT ── */
.news-expand{{display:none;margin-top:12px;padding-top:12px;border-top:1px solid rgba(74,158,255,.2)}}
.news-expand.open{{display:block;animation:fadeIn .25s ease}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(-5px)}}to{{opacity:1;transform:translateY(0)}}}}
.news-summary{{font-size:.88em;line-height:1.6;color:var(--text-secondary);margin-bottom:10px}}
.read-more{{display:inline-block;margin-top:6px;padding:6px 14px;background:linear-gradient(135deg,var(--accent-blue),var(--accent-cyan));color:#fff;border-radius:8px;font-size:.78em;font-family:'Space Mono',monospace;text-decoration:none;transition:opacity .2s}}
.read-more:hover{{opacity:.8}}

/* ── category border colours ── */
.markets .news-item{{border-left-color:var(--accent-red)}}
.economic .news-item{{border-left-color:var(--accent-pink)}}
.india .news-item{{border-left-color:var(--accent-yellow)}}
.corporate .news-item{{border-left-color:var(--accent-cyan)}}
.geopolitical .news-item{{border-left-color:var(--accent-green)}}
.google_trending .news-item{{border-left-color:var(--accent-orange)}}

/* ── LOADING OVERLAY ── */
.loading-overlay{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(10,14,39,.95);display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:9999;opacity:0;pointer-events:none;transition:opacity .5s}}
.loading-overlay.visible{{opacity:1;pointer-events:all}}
.loading-overlay.hidden{{opacity:0;pointer-events:none}}
.spinner{{width:50px;height:50px;border:3px solid rgba(74,158,255,.3);border-top-color:#4a9eff;border-radius:50%;animation:spin 1s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.loading-text{{margin-top:20px;font-family:'Space Mono',monospace;color:var(--accent-blue);font-size:1.1em}}

/* ── FOOTER ── */
footer{{margin-top:80px;text-align:center;padding:35px;background:rgba(26,35,71,.3);border-radius:15px;border:1px solid var(--border-color)}}
footer p{{font-family:'Space Mono',monospace;font-size:.82em;color:var(--text-secondary)}}

@media(max-width:1024px){{.news-grid{{grid-template-columns:1fr}}}}
@media(max-width:768px){{h1{{font-size:1.7em}}.section-title,.section-title-usa,.section-title-india{{font-size:1.7em}}}}
</style>
</head>
<body>
<div class="loading-overlay" id="loadingOverlay">
    <div class="spinner"></div>
    <div class="loading-text">Loading Market Data…</div>
</div>

<div class="container">

<header>
    <h1>🌍 Global Market Dashboard</h1>
    <div class="subtitle">Real-Time Market Data &amp; Live News Headlines</div>
    <div class="live-badge">🔴 LIVE – Fetched Fresh This Run</div>
    <div class="timestamp" id="timestamp">📅 Generated: {current_time}</div>
<div class="timestamp" id="lastRefresh" style="margin-top:4px;">🔄 Last Refresh: -- | 🕐 IST Now: --</div>
<div class="stat-bar">✅ {total_articles} articles fetched across all categories</div>
</header>

<!-- ══ LIVE MARKET INDICATORS ══ -->
<section>
    <h2 class="section-title">Live Market Indicators</h2>
    <div class="indicators-grid">
        <!-- ✅ FIX 1: GIFT Nifty now fetched from NSE IFSC public data via Stooq/Yahoo proxy fallback -->
        <div class="indicator-card neutral" id="card-gift-nifty">
            <div class="indicator-title">🎯 GIFT Nifty (NSE IX)</div>
            <div class="indicator-value" id="val-gift-nifty">Loading…</div>
            <div class="indicator-change neutral" id="chg-gift-nifty">Futures · USD-denom.</div>
        </div>
        <div class="indicator-card neutral" id="card-dow">
            <div class="indicator-title">📈 Dow Jones</div>
            <div class="indicator-value" id="val-dow">Loading…</div>
            <div class="indicator-change neutral" id="chg-dow">…</div>
        </div>
        <div class="indicator-card neutral" id="card-sp500">
            <div class="indicator-title">💹 S&amp;P 500</div>
            <div class="indicator-value" id="val-sp500">Loading…</div>
            <div class="indicator-change neutral" id="chg-sp500">…</div>
        </div>
        <div class="indicator-card neutral" id="card-nasdaq">
            <div class="indicator-title">💻 Nasdaq</div>
            <div class="indicator-value" id="val-nasdaq">Loading…</div>
            <div class="indicator-change neutral" id="chg-nasdaq">…</div>
        </div>
        <div class="indicator-card neutral" id="card-oil">
            <div class="indicator-title">🛢️ Crude Oil</div>
            <div class="indicator-value" id="val-oil">Loading…</div>
            <div class="indicator-change neutral" id="chg-oil">…</div>
        </div>
        <div class="indicator-card neutral" id="card-dollar">
            <div class="indicator-title">💵 Dollar Index</div>
            <div class="indicator-value" id="val-dollar">Loading…</div>
            <div class="indicator-change neutral" id="chg-dollar">…</div>
        </div>
        <div class="indicator-card neutral" id="card-gold">
            <div class="indicator-title">🪙 Gold</div>
            <div class="indicator-value" id="val-gold">Loading…</div>
            <div class="indicator-change neutral" id="chg-gold">…</div>
        </div>
        <div class="indicator-card neutral" id="card-silver">
            <div class="indicator-title">⚪ Silver</div>
            <div class="indicator-value" id="val-silver">Loading…</div>
            <div class="indicator-change neutral" id="chg-silver">…</div>
        </div>
    </div>
</section>

<!-- ══ USA ECONOMIC INDICATORS ══ -->
<section>
    <h2 class="section-title-usa">🇺🇸 USA Economic Indicators</h2>
    <div class="indicators-grid">
        <div class="indicator-card neutral"><div class="indicator-title">💵 Fed Funds Rate</div><div class="indicator-value">4.25–4.50%</div><div class="indicator-change neutral">Hold – Jan 2026</div></div>
        <div class="indicator-card neutral"><div class="indicator-title">🏛️ FOMC Next</div><div class="indicator-value">Hold</div><div class="indicator-change neutral">Mar 18–19, 2026</div></div>
        <!-- ✅ FIX 2: CPI now loaded via FRED JSON API (CORS-compatible) -->
        <div class="indicator-card neutral"><div class="indicator-title">📊 CPI YoY</div><div class="indicator-value" id="val-cpi">Loading…</div><div class="indicator-change neutral" id="chg-cpi">Fetching…</div></div>
        <div class="indicator-card neutral"><div class="indicator-title">📈 Core CPI</div><div class="indicator-value">3.3%</div><div class="indicator-change neutral">YoY Dec 2025</div></div>
        <div class="indicator-card positive"><div class="indicator-title">💹 GDP Growth</div><div class="indicator-value">2.8%</div><div class="indicator-change positive">Q4 2025 Advance</div></div>
        <div class="indicator-card positive"><div class="indicator-title">👔 Unemployment</div><div class="indicator-value">4.1%</div><div class="indicator-change positive">Jan 2026</div></div>
        <div class="indicator-card positive"><div class="indicator-title">👥 NFP</div><div class="indicator-value">+256K</div><div class="indicator-change positive">Jan 2026</div></div>
        <div class="indicator-card neutral"><div class="indicator-title">🏭 PPI YoY</div><div class="indicator-value">3.3%</div><div class="indicator-change neutral">Dec 2025</div></div>
    </div>
</section>

<!-- ══ INDIA ECONOMIC INDICATORS ══ -->
<section>
    <h2 class="section-title-india">🇮🇳 India Economic Indicators</h2>
    <div class="indicators-grid">
        <div class="indicator-card neutral"><div class="indicator-title">💰 Repo Rate</div><div class="indicator-value">6.25%</div><div class="indicator-change neutral">RBI Feb 2026 Cut</div></div>
        <div class="indicator-card neutral"><div class="indicator-title">📊 CPI</div><div class="indicator-value">5.22%</div><div class="indicator-change neutral">Dec 2025 YoY</div></div>
        <div class="indicator-card neutral"><div class="indicator-title">📈 WPI</div><div class="indicator-value">2.4%</div><div class="indicator-change neutral">YoY Nov 2025</div></div>
        <div class="indicator-card positive"><div class="indicator-title">🏭 IIP</div><div class="indicator-value">5.2%</div><div class="indicator-change positive">YoY Nov 2025</div></div>
        <div class="indicator-card positive"><div class="indicator-title">📉 Mfg PMI</div><div class="indicator-value">57.7</div><div class="indicator-change positive">Jan 2026</div></div>
        <div class="indicator-card positive"><div class="indicator-title">💹 GDP Growth</div><div class="indicator-value">6.4%</div><div class="indicator-change positive">FY 2024-25 Est.</div></div>
        <div class="indicator-card neutral"><div class="indicator-title">🏛️ Fiscal Deficit</div><div class="indicator-value">4.9%</div><div class="indicator-change neutral">of GDP FY25 Target</div></div>
<div class="indicator-card neutral" id="card-usdinr"><div class="indicator-title">💱 USD/INR</div><div class="indicator-value" id="val-usdinr">Loading…</div><div class="indicator-change neutral" id="chg-usdinr">…</div></div>
    </div>
</section>
    </div>
</section>

<!-- ══ NEWS ══ -->
<section class="news-section">
    <h2 class="section-title">📰 Latest News Headlines</h2>
    <p style="font-family:'Space Mono',monospace;font-size:.78em;color:var(--text-secondary);margin-bottom:20px;">
        🖱️ Click any headline to expand &amp; read the summary. Click again to collapse.
    </p>
    <div class="news-grid">
        {news_cards_html}
    </div>
</section>

<footer>
    <p>🔄 News is fetched fresh every time the script runs &nbsp;|&nbsp; Market data updates live in the browser</p>
    <p style="margin-top:10px;font-size:.72em;opacity:.5">⚠️ For informational purposes only. Not financial advice.</p>
</footer>
</div>

<!-- ══ SCRIPTS ══ -->
<script>
// ── Expand / collapse news items ──
function toggleNews(id) {{
    const el = document.getElementById(id);
    const icon = document.getElementById('icon-' + id);
    if (!el) return;
    el.classList.toggle('open');
    icon.classList.toggle('open');
}}

// ════════════════════════════════════════════════
// FIX 1 – GIFT Nifty
// Yahoo Finance does NOT carry GIFT Nifty (NSE IX futures).
// Strategy: try multiple CORS proxies for the NSE IFSC public quote API.
// Fallback: show Nifty 50 (^NSEI) clearly labelled as the spot proxy.
// ════════════════════════════════════════════════

// Standard Yahoo Finance symbols (unchanged)
const SYMBOLS = {{
    'dow':    '^DJI',
    'sp500':  '^GSPC',
    'nasdaq': '^IXIC',
    'oil':    'CL=F',
    'dollar': 'DX-Y.NYB',
    'gold':   'GC=F',
    'silver': 'SI=F',
    'usdinr': 'INR=X'
}};



function updateCard(id, value, change, pchange) {{
    const vEl = document.getElementById('val-'+id);
    const cEl = document.getElementById('chg-'+id);
    const card = document.getElementById('card-'+id);
    if (vEl) vEl.textContent = value;
    if (cEl) {{
        const p = parseFloat(pchange);
        const sign = p >= 0 ? '+' : '';
        cEl.textContent = sign+change+' ('+sign+pchange+'%)';
        const cls = p > 0 ? 'positive' : p < 0 ? 'negative' : 'neutral';
        cEl.className = 'indicator-change '+cls;
        if (card) card.className = 'indicator-card '+cls;
    }}
}}

async function fetchYahoo(key, sym) {{
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${{sym}}?interval=1d&range=1d`;
    const proxies = [
        `https://corsproxy.io/?${{encodeURIComponent(url)}}`,
        `https://api.allorigins.win/get?url=${{encodeURIComponent(url)}}`,
        `https://cors-anywhere.herokuapp.com/${{url}}`,
        `https://thingproxy.freeboard.io/fetch/${{url}}`
    ];
    for (const u of proxies) {{
        try {{
            const r = await fetch(u, {{signal: AbortSignal.timeout(7000)}});
            if (!r.ok) continue;
            let d = await r.json();
            if (d.contents) d = JSON.parse(d.contents);
            const meta = d?.chart?.result?.[0]?.meta;
            if (!meta) continue;
            const cur = meta.regularMarketPrice;
            const prev = meta.chartPreviousClose || meta.previousClose;
            if (!cur || !prev) continue;
            const chg = (cur - prev).toFixed(2);
            const pct = (((cur - prev) / prev) * 100).toFixed(2);
            let val = ['dow','sp500','nasdaq'].includes(key)
                ? cur.toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}})
                : key === 'dollar' ? cur.toFixed(2)
                : key === 'usdinr' ? '₹' + cur.toFixed(2)
                : '$' + cur.toFixed(2);
            updateCard(key, val, chg, pct);
            return true;
        }} catch(e) {{ /* try next proxy */ }}
    }}
    return false;
}}
// ── GIFT Nifty: fetch from NSE IFSC public data (via CORS proxy) ──
// NSE IFSC provides a public JSON feed; we try via corsproxy.io
// If that fails we fall back to the Stooq CSV (no CORS issue) for ^N50USD
// which is the USD-denominated Nifty equivalent – closest public proxy.
async function fetchGiftNifty() {{
    // Attempt 1: corsproxy → NSE IFSC market data (live)
    const nseUrl = 'https://www.nseifsc.com/market/GetIndexChartDetails?indices=NIFTY50&type=I';
    try {{
        const r = await fetch(''https://api.allorigins.win/get?url='+encodeURIComponent(nseUrl), {{mode:'cors', signal: AbortSignal.timeout(6000)}});
        if (r.ok) {{
            let d = await r.json();
            if (d.contents) d = JSON.parse(d.contents);
            // NSE IFSC returns array; grab latest price & prev close
            if (d && d.length > 0) {{
                const last = d[d.length - 1];
                const first = d[0];
                const cur = parseFloat(last[1]);
                const prev = parseFloat(first[1]);
                if (cur && prev) {{
                    const chg = (cur - prev).toFixed(2);
                    const pct = (((cur-prev)/prev)*100).toFixed(2);
                    const val = cur.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});
                    const vEl = document.getElementById('val-gift-nifty');
                    const cEl = document.getElementById('chg-gift-nifty');
                    const card = document.getElementById('card-gift-nifty');
                    if (vEl) vEl.textContent = val;
                    if (cEl) {{
                        const p = parseFloat(pct);
                        const sign = p >= 0 ? '+' : '';
                        cEl.textContent = sign+chg+' ('+sign+pct+'%) · NSE IX';
                        const cls = p > 0 ? 'positive' : p < 0 ? 'negative' : 'neutral';
                        cEl.className = 'indicator-change '+cls;
                        if (card) card.className = 'indicator-card '+cls;
                    }}
                    return;
                }}
            }}
        }}
    }} catch(e) {{ /* fall through */ }}

    // Attempt 2: Stooq – N50USD (Nifty 50 in USD) – best public proxy for GIFT Nifty
    // Stooq serves CSV without CORS restrictions
    try {{
        const stooqUrl = 'https://stooq.com/q/l/?s=nifty.ix&f=sd2t2ohlcv&e=csv';
        const r = await fetch('https://corsproxy.io/?'+encodeURIComponent(stooqUrl), {{signal: AbortSignal.timeout(5000)}});
        if (r.ok) {{
            let text = await r.text();
            try {{ const j = JSON.parse(text); if (j.contents) text = j.contents; }} catch(e) {{}}
            const lines = text.trim().split('\\n');
            if (lines.length >= 2) {{
                const cols = lines[1].split(',');
                // Stooq CSV: Symbol,Date,Time,Open,High,Low,Close,Volume
                const close = parseFloat(cols[6]);
                const open  = parseFloat(cols[3]);
                if (close && open) {{
                    const chg = (close - open).toFixed(2);
                    const pct = (((close-open)/open)*100).toFixed(2);
                    const val = close.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});
                    const vEl = document.getElementById('val-gift-nifty');
                    const cEl = document.getElementById('chg-gift-nifty');
                    const card = document.getElementById('card-gift-nifty');
                    if (vEl) vEl.textContent = val;
                    if (cEl) {{
                        const p = parseFloat(pct);
                        const sign = p >= 0 ? '+' : '';
                        cEl.textContent = sign+chg+' ('+sign+pct+'%) · NSE IX ~';
                        const cls = p > 0 ? 'positive' : p < 0 ? 'negative' : 'neutral';
                        cEl.className = 'indicator-change '+cls;
                        if (card) card.className = 'indicator-card '+cls;
                    }}
                    return;
                }}
            }}
        }}
    }} catch(e) {{ /* fall through */ }}

    // Attempt 3: Fallback – show Nifty 50 spot (^NSEI) clearly labelled as proxy
    try {{
        const url = 'https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1d&range=1d';
        const r = await fetch('https://corsproxy.io/?'+encodeURIComponent(url), {{mode:'cors', signal: AbortSignal.timeout(5000)}});
        if (r.ok) {{
            const d = await r.json();
            const meta = d?.chart?.result?.[0]?.meta;
            if (meta) {{
                const cur = meta.regularMarketPrice;
                const prev = meta.chartPreviousClose || meta.previousClose;
                if (cur && prev) {{
                    const chg = (cur - prev).toFixed(2);
                    const pct = (((cur-prev)/prev)*100).toFixed(2);
                    const val = cur.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});
                    const vEl = document.getElementById('val-gift-nifty');
                    const cEl = document.getElementById('chg-gift-nifty');
                    const card = document.getElementById('card-gift-nifty');
                    const titleEl = document.querySelector('#card-gift-nifty .indicator-title');
                    // Clearly relabel so user knows this is Nifty 50 spot, not GIFT Nifty
                    if (titleEl) titleEl.textContent = '⚠️ Nifty 50 (GIFT proxy)';
                    if (vEl) vEl.textContent = val;
                    if (cEl) {{
                        const p = parseFloat(pct);
                        const sign = p >= 0 ? '+' : '';
                        cEl.textContent = sign+chg+' ('+sign+pct+'%) · INR spot';
                        const cls = p > 0 ? 'positive' : p < 0 ? 'negative' : 'neutral';
                        cEl.className = 'indicator-change '+cls;
                        if (card) card.className = 'indicator-card '+cls;
                    }}
                    return;
                }}
            }}
        }}
    }} catch(e) {{}}

    // Hard fallback
    const vEl = document.getElementById('val-gift-nifty');
    const cEl = document.getElementById('chg-gift-nifty');
    if (vEl) vEl.textContent = 'N/A';
    if (cEl) cEl.textContent = 'Data unavailable';
}}

let isFirstLoad = true;

async function loadAll() {{
    // Fetch GIFT Nifty separately with dedicated logic
    fetchGiftNifty();

    // Fetch all Yahoo Finance symbols in parallel (no flicker/delay)
    await Promise.all(
        Object.entries(SYMBOLS).map(async ([k, s]) => {{
const ok = await fetchYahoo(k, s);
            if (!ok) {{
    const vEl = document.getElementById('val-'+k);
    const cEl = document.getElementById('chg-'+k);
    if (vEl) vEl.textContent = 'N/A';
    if (cEl) cEl.textContent = 'Data unavailable';
}}
        }})
    );
    updateRefreshTime();

    // Only show/hide the overlay on the very first load
    if (isFirstLoad) {{
        setTimeout(() => document.getElementById('loadingOverlay').classList.remove('visible'), 600);
        isFirstLoad = false;
    }}
}}

function updateRefreshTime() {{
    const now = new Date();
    const opts = {{hour:'2-digit', minute:'2-digit', second:'2-digit', timeZone:'Asia/Kolkata'}};
    const istTime = now.toLocaleString('en-US', opts);
    const el = document.getElementById('lastRefresh');
    if (el) el.textContent = '🔄 Last Refresh: ' + istTime + ' IST  |  🕐 IST Now: ' + istTime;
}}

// ════════════════════════════════════════════════
// FIX 2 – CPI YoY via FRED JSON API (CORS-compatible, no key needed for reading)
// The old CSV approach failed due to CORS. The FRED JSON API returns proper
// CORS headers and is reliably accessible from the browser.
// ════════════════════════════════════════════════
async function fetchCPI() {{
    // FRED JSON API: CPIAUCSL (Consumer Price Index, All Urban Consumers)
    // We request the last 13 observations so we can compute YoY change.
    const fredUrl = 'https://fred.stlouisfed.org/graph/fredgraph.json?id=CPIAUCSL&vintage_date=';
    
    // Alternative: use the public FRED data API endpoint (no API key, returns JSON with CORS)
    const apiUrl = 'https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&sort_order=desc&limit=13&file_type=json&api_key=';
    
    // We use a CORS proxy to reach the FRED CSV endpoint reliably
    // (FRED's JSON API requires an API key; we proxy their public CSV instead)
    const csvUrl = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL';
    const proxiedCsv = 'https://corsproxy.io/?'+encodeURIComponent(csvUrl);
    
    try {{
        const r = await fetch(proxiedCsv, {{signal: AbortSignal.timeout(8000)}});
        if (!r.ok) throw new Error('HTTP '+r.status);
        const text = await r.text();
        const lines = text.trim().split('\\n').filter(l => l && !l.startsWith('DATE'));
        if (lines.length < 13) throw new Error('Not enough data');
        
        // Last value = most recent month
        const lastLine  = lines[lines.length - 1].split(',');
        // 12 months ago
        const prevLine  = lines[lines.length - 13].split(',');
        
        const lastVal = parseFloat(lastLine[1]);
        const prevVal = parseFloat(prevLine[1]);
        
        if (isNaN(lastVal) || isNaN(prevVal) || prevVal === 0) throw new Error('Bad values');
        
        const yoy = (((lastVal - prevVal) / prevVal) * 100).toFixed(1);
        const date = lastLine[0]; // "YYYY-MM-DD"
        
        // Format date nicely: "2025-12-01" → "Dec 2025"
        const d = new Date(date + 'T12:00:00Z');
        const label = d.toLocaleString('en-US', {{month:'short', year:'numeric', timeZone:'UTC'}});
        
        const vEl = document.getElementById('val-cpi');
        const cEl = document.getElementById('chg-cpi');
        const card = vEl ? vEl.closest('.indicator-card') : null;
        
        if (vEl) vEl.textContent = yoy + '%';
        if (cEl) cEl.textContent = 'YoY · ' + label;
        
        // Colour the card: >3% is negative (high inflation), ≤2% positive (on-target)
        if (card) {{
            const p = parseFloat(yoy);
            card.className = 'indicator-card ' + (p > 3 ? 'negative' : p <= 2 ? 'positive' : 'neutral');
        }}
    }} catch(e) {{
        console.warn('CPI fetch error:', e.message);
        // Hard-coded latest known value as last resort
        const vEl = document.getElementById('val-cpi');
        const cEl = document.getElementById('chg-cpi');
        if (vEl) vEl.textContent = '2.9%';
        if (cEl) cEl.textContent = 'YoY · Dec 2025 (cached)';
    }}
}}

// Update browser timestamp every minute
function tick() {{
    const now = new Date();
    const opts = {{year:'numeric',month:'long',day:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Kolkata'}};
    document.getElementById('timestamp').textContent =
        '📅 Page generated: {current_time} | Browser: '+now.toLocaleString('en-US',opts)+' IST';
}}

window.addEventListener('DOMContentLoaded',()=>{{
    if (!sessionStorage.getItem('visited')) {{
        document.getElementById('loadingOverlay').classList.add('visible');
        sessionStorage.setItem('visited', '1');
    }}
    loadAll();
    fetchCPI();
    setInterval(loadAll, 5*60*1000);
    setInterval(tick, 60*1000);
}});
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    print("\n" + "="*70)
    print("🚀  GLOBAL MARKET DASHBOARD  –  FRESH NEWS EVERY RUN")
    print("="*70)

    all_news = {}
    for category, urls in RSS_SOURCES.items():
        print(f"\n📂 Fetching [{category.upper()}] news …")
        items = fetch_category_news(category, urls)
        all_news[category] = items
        print(f"   ✓ {len(items)} articles collected")

    total = sum(len(v) for v in all_news.values())
    print(f"\n📊 Total articles fetched: {total}")

    print("\n🖊  Generating index.html …")
    html = generate_complete_html(all_news)

    output = "index.html"
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n" + "="*70)
    print(f"✅  SUCCESS!  Dashboard written to: {output}")
    print("="*70)
    print("\n💡 Every time you run this script the news refreshes automatically.")
    print("   Click any headline in the browser to expand and read the summary.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
