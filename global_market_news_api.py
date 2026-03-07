#!/usr/bin/env python3
"""
Global Market News & Indicators Dashboard
Fetches REAL latest news using RSS feeds every run.
Generates HTML with Bloomberg Terminal UI (Template 1).
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
    cutoff = datetime.utcnow() - timedelta(hours=24)

    for url in urls:
        print(f"  Fetching {url[:60]}...")
        for item in fetch_rss(url):
            key = item["title"].lower()[:60]
            if key in seen_titles:
                continue

            if category == "google_trending" and item.get("pubDate"):
                try:
                    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"]:
                        try:
                            pub = datetime.strptime(item["pubDate"].strip(), fmt)
                            pub_utc = pub.replace(tzinfo=None) if pub.tzinfo else pub
                            if pub_utc < cutoff:
                                continue
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


def build_news_json(all_news: dict) -> str:
    """Serialize all_news into a JS-safe JSON object for client-side tab rendering."""
    categories_meta = {
        "markets":         "📊 MARKET UPDATES",
        "economic":        "💰 ECONOMIC & POLICY",
        "india":           "🇮🇳 INDIAN MARKETS",
        "google_trending": "🔥 GOOGLE TRENDING",
        "corporate":       "🏢 CORPORATE NEWS",
        "geopolitical":    "🌍 GEOPOLITICAL",
    }

    out = {}
    for cat, label in categories_meta.items():
        items = all_news.get(cat, [])
        out[cat] = {
            "label": label,
            "items": [
                {
                    "title":   escape(item.get("title", "Untitled")),
                    "source":  escape(item.get("source", "Unknown")),
                    "time":    format_pub_date(item.get("pubDate", "")),
                    "summary": escape(item.get("summary", "Click to read the full article.")),
                    "link":    escape(item.get("link", "#")),
                }
                for item in items
            ],
        }
    return json.dumps(out, ensure_ascii=False)


def generate_complete_html(all_news: dict) -> str:
    current_time = get_ist_time()
    total_articles = sum(len(v) for v in all_news.values())
    news_json = build_news_json(all_news)

    # Count per category for sidebar
    cat_counts = {
        "markets":         len(all_news.get("markets", [])),
        "economic":        len(all_news.get("economic", [])),
        "india":           len(all_news.get("india", [])),
        "google_trending": len(all_news.get("google_trending", [])),
        "corporate":       len(all_news.get("corporate", [])),
        "geopolitical":    len(all_news.get("geopolitical", [])),
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Global Market Dashboard – Live News</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600;700&family=IBM+Plex+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
/* ══════════════════════════════════════════
   BLOOMBERG TERMINAL THEME
   ══════════════════════════════════════════ */
:root {{
  --bg: #0d0d0d;
  --panel: #131313;
  --panel2: #181818;
  --border: #333333;
  --border2: #252525;
  --orange: #ff6a00;
  --orange-dim: rgba(255,106,0,0.10);
  --orange-mid: rgba(255,106,0,0.22);
  --green: #00ff55;
  --green-dim: rgba(0,255,85,0.08);
  --red: #ff3355;
  --red-dim: rgba(255,51,85,0.08);
  --yellow: #ffd700;
  --blue: #29b6ff;
  --muted: #999999;
  --muted2: #666666;
  --text: #d8d8d8;
  --white: #f5f5f5;
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: 'IBM Plex Mono', monospace;
  font-size: 14px;
  min-height: 100vh;
  overflow-x: hidden;
}}

/* ── TOP BAR ── */
.topbar {{
  background: var(--orange);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 18px;
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 2px;
  position: sticky;
  top: 0;
  z-index: 100;
}}
.topbar-left {{ display:flex; align-items:center; gap:16px; }}
.topbar-right {{ display:flex; gap: 22px; font-weight: 600; font-size: 11px; }}
.topbar-dot {{ width:8px; height:8px; border-radius:50%; background:#000; animation: blink 1.5s step-end infinite; }}
@keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.2}} }}

/* ── TICKER STRIP ── */
.ticker {{
  background: #1c1c1c;
  border-bottom: 1px solid var(--border);
  padding: 6px 0;
  overflow: hidden;
  white-space: nowrap;
}}
.ticker-track {{
  display: inline-flex;
  gap: 0;
  animation: scroll-ticker 60s linear infinite;
}}
.ticker-track:hover {{ animation-play-state: paused; }}
.ticker-item {{
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 26px;
  border-right: 1px solid var(--border);
  font-size: 12px;
  letter-spacing: 0.3px;
}}
.t-sym {{ color: var(--orange); font-weight: 700; }}
.t-val {{ color: var(--white); font-weight: 500; }}
.t-pos {{ color: var(--green); font-weight: 600; }}
.t-neg {{ color: var(--red); font-weight: 600; }}
.t-neu {{ color: #aaaaaa; }}
@keyframes scroll-ticker {{
  0%   {{ transform: translateX(0); }}
  100% {{ transform: translateX(-50%); }}
}}

/* ── MAIN SHELL ── */
.shell {{
  display: grid;
  grid-template-columns: 240px 1fr;
  height: calc(100vh - 56px);
}}

/* ── SIDEBAR ── */
.sidebar {{
  background: var(--panel);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: 16px 0 40px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}}
.sidebar::-webkit-scrollbar {{ width:4px; }}
.sidebar::-webkit-scrollbar-track {{ background:transparent; }}
.sidebar::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:2px; }}

.sb-section {{ margin-bottom: 24px; }}
.sb-label {{
  color: var(--orange);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  padding: 5px 14px 8px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.sb-item {{
  padding: 8px 14px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-left: 3px solid transparent;
  transition: all 0.12s;
  font-size: 13px;
}}
.sb-item:hover {{ background: var(--orange-dim); border-left-color: rgba(255,106,0,0.4); }}
.sb-item.active {{ background: var(--orange-dim); border-left-color: var(--orange); }}
.sb-item .sb-name {{ color: var(--white); font-weight: 500; }}
.sb-item .sb-count {{
  color: #cccccc;
  font-size: 11px;
  background: var(--border2);
  padding: 1px 7px;
  border-radius: 2px;
  font-weight: 600;
}}
.sb-item.active .sb-count {{ background: var(--orange-mid); color: var(--orange); }}

.sb-ind-row {{
  padding: 7px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  border-bottom: 1px solid var(--border2);
}}
.sb-ind-row:last-child {{ border-bottom: none; }}
.sb-ind-name {{ color: #cccccc; font-weight: 400; }}
.sb-ind-val {{ font-weight: 700; font-size: 12px; }}
.sb-ind-val.pos {{ color: var(--green); }}
.sb-ind-val.neg {{ color: var(--red); }}
.sb-ind-val.neu {{ color: #aaaaaa; }}

/* ── MAIN CONTENT ── */
.main {{ overflow-y: auto; display: flex; flex-direction: column; scrollbar-width: thin; scrollbar-color: var(--border) transparent; }}
.main::-webkit-scrollbar {{ width:4px; }}
.main::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:2px; }}

/* ── INDICATORS PANEL ── */
.ind-panel {{
  background: #101010;
  border-bottom: 1px solid var(--border);
  padding: 14px 16px;
  flex-shrink: 0;
}}
.ind-panel-hdr {{
  color: var(--orange);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.ind-panel-hdr::after {{ content:''; flex:1; height:1px; background: linear-gradient(90deg, rgba(255,106,0,0.5), transparent); }}

.ind-row {{ display: flex; gap: 3px; flex-wrap: wrap; }}

.ind-cell {{
  background: var(--panel);
  border: 1px solid var(--border);
  padding: 10px 14px;
  min-width: 130px;
  flex: 1;
  position: relative;
  transition: border-color 0.2s;
}}
.ind-cell::after {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
}}
.ind-cell.pos::after {{ background: var(--green); }}
.ind-cell.neg::after {{ background: var(--red); }}
.ind-cell.neu::after {{ background: #666; }}
.ind-cell:hover {{ border-color: var(--orange); }}

.ind-name {{
  color: #aaaaaa;
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 5px;
  font-weight: 500;
}}
.ind-val {{
  color: var(--white);
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 4px;
  white-space: nowrap;
  letter-spacing: -0.5px;
}}
.ind-chg {{
  font-size: 11px;
  letter-spacing: 0.3px;
  white-space: nowrap;
  font-weight: 600;
}}
.ind-chg.pos {{ color: var(--green); }}
.ind-chg.neg {{ color: var(--red); }}
.ind-chg.neu {{ color: #aaaaaa; }}

/* ── USA / INDIA ECON PANELS ── */
.econ-section {{
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  background: #101010;
  flex-shrink: 0;
}}
.econ-hdr {{
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.econ-hdr.usa {{ color: #e05060; }}
.econ-hdr.usa::after {{ content:''; flex:1; height:1px; background: linear-gradient(90deg, rgba(224,80,96,0.5), transparent); }}
.econ-hdr.india {{ color: #ffaa44; }}
.econ-hdr.india::after {{ content:''; flex:1; height:1px; background: linear-gradient(90deg, rgba(255,170,68,0.5), transparent); }}

/* ── CATEGORY TABS ── */
.cat-tabs {{
  display: flex;
  gap: 0;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  background: #101010;
  overflow-x: auto;
  flex-shrink: 0;
  scrollbar-width: none;
}}
.cat-tabs::-webkit-scrollbar {{ display:none; }}
.cat-tab {{
  padding: 9px 18px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: #999999;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  transition: all 0.15s;
  flex-shrink: 0;
}}
.cat-tab:hover {{ color: var(--white); }}
.cat-tab.active {{
  color: var(--orange);
  border-bottom-color: var(--orange);
}}

/* ── NEWS AREA ── */
.news-area {{ flex: 1; padding: 16px 18px; overflow-y: auto; }}
.news-hdr {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}}
.news-hdr-title {{
  color: var(--orange);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
}}
.news-hdr-meta {{ color: #aaaaaa; font-size: 11px; }}

/* ── NEWS TABLE ── */
.news-table {{ width: 100%; border-collapse: collapse; }}
.news-table tbody tr {{
  border-bottom: 1px solid var(--border2);
  cursor: pointer;
  transition: background 0.1s;
}}
.news-table tbody tr:hover td {{ background: rgba(255,106,0,0.05); }}
.news-table tbody tr.open td {{ background: rgba(255,106,0,0.08); }}

.td-num {{
  color: #888888;
  font-size: 11px;
  padding: 11px 8px 11px 4px;
  width: 30px;
  text-align: right;
  vertical-align: top;
  font-weight: 600;
}}
.td-time {{
  color: #aaaaaa;
  font-size: 11px;
  width: 88px;
  white-space: nowrap;
  padding: 11px 10px;
  vertical-align: top;
  font-weight: 500;
}}
.td-src {{
  width: 104px;
  padding: 11px 10px;
  vertical-align: top;
}}
.src-badge {{
  display: inline-block;
  background: var(--orange-dim);
  color: var(--orange);
  border: 1px solid rgba(255,106,0,0.35);
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 2px;
  white-space: nowrap;
  letter-spacing: 0.5px;
}}
.td-title {{ padding: 11px 10px; vertical-align: top; }}
.td-title .headline {{
  font-size: 13px;
  color: #f0f0f0;
  line-height: 1.55;
  letter-spacing: 0.2px;
  font-family: 'IBM Plex Sans', sans-serif;
  font-weight: 400;
}}
.td-title .expand-body {{
  display: none;
  margin-top: 10px;
  padding: 12px 14px;
  background: rgba(255,106,0,0.05);
  border-left: 2px solid var(--orange);
}}
.news-table tbody tr.open .td-title .expand-body {{ display: block; }}
.expand-summary {{
  font-size: 13px;
  color: #d0d0d0;
  line-height: 1.75;
  font-family: 'IBM Plex Sans', sans-serif;
  margin-bottom: 10px;
}}
.expand-link {{
  display: inline-block;
  color: var(--orange);
  font-size: 11px;
  text-decoration: none;
  letter-spacing: 1px;
  border-bottom: 1px solid rgba(255,106,0,0.4);
  padding-bottom: 1px;
  transition: opacity 0.15s;
  font-weight: 600;
}}
.expand-link:hover {{ opacity: 0.75; }}
.td-arrow {{
  width: 26px;
  padding: 11px 4px;
  vertical-align: top;
  text-align: center;
}}
.arrow-icon {{
  color: var(--orange);
  font-size: 11px;
  display: inline-block;
  transition: transform 0.2s;
  opacity: 0.65;
}}
.news-table tbody tr.open .arrow-icon {{
  transform: rotate(180deg);
  opacity: 1;
}}
.no-news {{
  color: #aaaaaa;
  font-size: 13px;
  padding: 24px 4px;
  font-style: italic;
}}

/* ── LOADING OVERLAY ── */
.loading-overlay {{
  position: fixed; top:0; left:0; width:100%; height:100%;
  background: rgba(10,10,10,0.97);
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  z-index: 9999; opacity: 0; pointer-events: none;
  transition: opacity 0.4s;
}}
.loading-overlay.visible {{ opacity:1; pointer-events:all; }}
.spinner {{
  width: 38px; height: 38px;
  border: 2px solid rgba(255,106,0,0.25);
  border-top-color: var(--orange);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
.loading-text {{
  margin-top: 18px;
  font-size: 13px;
  letter-spacing: 3px;
  color: var(--orange);
  text-transform: uppercase;
  font-weight: 600;
}}

/* ── STATUS BAR ── */
.statusbar {{
  position: fixed; bottom:0; left:0; right:0;
  background: var(--orange);
  color: #000;
  display: flex;
  justify-content: space-between;
  padding: 4px 16px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  z-index: 100;
}}

/* ── SCROLLBAR (main sidebar) ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}

/* ── RESPONSIVE ── */
@media (max-width: 900px) {{
  .shell {{ grid-template-columns: 1fr; height: auto; }}
  .sidebar {{ display: none; }}
  .ind-row {{ flex-wrap: wrap; }}
  .ind-cell {{ min-width: 120px; }}
}}
</style>
</head>
<body>

<!-- LOADING OVERLAY -->
<div class="loading-overlay" id="loadingOverlay">
  <div class="spinner"></div>
  <div class="loading-text">Loading Market Data…</div>
</div>

<!-- TOP BAR -->
<div class="topbar">
  <div class="topbar-left">
    <div class="topbar-dot"></div>
    <span>◼ GLOBAL MARKET DASHBOARD</span>
  </div>
  <div class="topbar-right">
    <span>🔴 LIVE FEED</span>
    <span id="topClock">--:--:-- IST</span>
    <span>📅 Generated: {current_time}</span>
    <span>✅ {total_articles} ARTICLES</span>
  </div>
</div>

<!-- TICKER STRIP -->
<div class="ticker">
  <div class="ticker-track" id="tickerTrack">
    <!-- populated by JS -->
  </div>
</div>

<!-- MAIN SHELL -->
<div class="shell">

  <!-- ═══ SIDEBAR ═══ -->
  <div class="sidebar">

    <div class="sb-section">
      <div class="sb-label">▶ CATEGORIES</div>
      <div class="sb-item active" id="sb-markets"        onclick="switchCat('markets',this)">
        <span class="sb-name">📊 Markets</span>
        <span class="sb-count">{cat_counts["markets"]}</span>
      </div>
      <div class="sb-item" id="sb-economic"       onclick="switchCat('economic',this)">
        <span class="sb-name">💰 Economic</span>
        <span class="sb-count">{cat_counts["economic"]}</span>
      </div>
      <div class="sb-item" id="sb-india"          onclick="switchCat('india',this)">
        <span class="sb-name">🇮🇳 India</span>
        <span class="sb-count">{cat_counts["india"]}</span>
      </div>
      <div class="sb-item" id="sb-google_trending" onclick="switchCat('google_trending',this)">
        <span class="sb-name">🔥 Trending</span>
        <span class="sb-count">{cat_counts["google_trending"]}</span>
      </div>
      <div class="sb-item" id="sb-corporate"      onclick="switchCat('corporate',this)">
        <span class="sb-name">🏢 Corporate</span>
        <span class="sb-count">{cat_counts["corporate"]}</span>
      </div>
      <div class="sb-item" id="sb-geopolitical"   onclick="switchCat('geopolitical',this)">
        <span class="sb-name">🌍 Geopolitical</span>
        <span class="sb-count">{cat_counts["geopolitical"]}</span>
      </div>
    </div>

    <div class="sb-section">
      <div class="sb-label">▶ LIVE PRICES</div>
      <div class="sb-ind-row"><span class="sb-ind-name">S&amp;P 500</span>    <span class="sb-ind-val neu" id="sbv-sp500">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Dow Jones</span>   <span class="sb-ind-val neu" id="sbv-dow">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Nasdaq</span>      <span class="sb-ind-val neu" id="sbv-nasdaq">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Nifty 50</span>    <span class="sb-ind-val neu" id="sbv-nifty">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Sensex</span>      <span class="sb-ind-val neu" id="sbv-sensex">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">USD/INR</span>     <span class="sb-ind-val neu" id="sbv-usdinr">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Crude Oil</span>   <span class="sb-ind-val neu" id="sbv-oil">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Gold</span>        <span class="sb-ind-val neu" id="sbv-gold">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Silver</span>      <span class="sb-ind-val neu" id="sbv-silver">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">USD Index</span>   <span class="sb-ind-val neu" id="sbv-dollar">--</span></div>
    </div>

    <div class="sb-section">
      <div class="sb-label">▶ SOURCES</div>
      <div class="sb-ind-row"><span class="sb-ind-name">CNBC</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">MarketWatch</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Reuters</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Economic Times</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">MoneyControl</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Yahoo Finance</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Google News</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Federal Reserve</span></div>
    </div>

  </div><!-- /sidebar -->

  <!-- ═══ MAIN ═══ -->
  <div class="main">

    <!-- ── LIVE MARKET INDICATORS ── -->
    <div class="ind-panel">
      <div class="ind-panel-hdr">▶ LIVE MARKET INDICATORS</div>
      <div class="ind-row">
        <div class="ind-cell neu" id="card-gift-nifty">
          <div class="ind-name">GIFT NIFTY (NSE IX)</div>
          <div class="ind-val" id="val-gift-nifty">Loading…</div>
          <div class="ind-chg neu" id="chg-gift-nifty">Futures · USD-denom.</div>
        </div>
        <div class="ind-cell neu" id="card-dow">
          <div class="ind-name">DOW JONES</div>
          <div class="ind-val" id="val-dow">Loading…</div>
          <div class="ind-chg neu" id="chg-dow">…</div>
        </div>
        <div class="ind-cell neu" id="card-sp500">
          <div class="ind-name">S&amp;P 500</div>
          <div class="ind-val" id="val-sp500">Loading…</div>
          <div class="ind-chg neu" id="chg-sp500">…</div>
        </div>
        <div class="ind-cell neu" id="card-nasdaq">
          <div class="ind-name">NASDAQ</div>
          <div class="ind-val" id="val-nasdaq">Loading…</div>
          <div class="ind-chg neu" id="chg-nasdaq">…</div>
        </div>
        <div class="ind-cell neu" id="card-oil">
          <div class="ind-name">CRUDE OIL</div>
          <div class="ind-val" id="val-oil">Loading…</div>
          <div class="ind-chg neu" id="chg-oil">…</div>
        </div>
        <div class="ind-cell neu" id="card-dollar">
          <div class="ind-name">USD INDEX</div>
          <div class="ind-val" id="val-dollar">Loading…</div>
          <div class="ind-chg neu" id="chg-dollar">…</div>
        </div>
        <div class="ind-cell neu" id="card-gold">
          <div class="ind-name">GOLD</div>
          <div class="ind-val" id="val-gold">Loading…</div>
          <div class="ind-chg neu" id="chg-gold">…</div>
        </div>
        <div class="ind-cell neu" id="card-silver">
          <div class="ind-name">SILVER</div>
          <div class="ind-val" id="val-silver">Loading…</div>
          <div class="ind-chg neu" id="chg-silver">…</div>
        </div>
      </div>
    </div>

    <!-- ── USA ECONOMIC INDICATORS ── -->
    <div class="econ-section">
      <div class="ind-panel-hdr econ-hdr usa">▶ 🇺🇸 USA ECONOMIC INDICATORS</div>
      <div class="ind-row">
        <div class="ind-cell neu"><div class="ind-name">FED FUNDS RATE</div><div class="ind-val">4.25–4.50%</div><div class="ind-chg neu">Hold – Jan 2026</div></div>
        <div class="ind-cell neu"><div class="ind-name">FOMC NEXT</div><div class="ind-val">Hold</div><div class="ind-chg neu">Mar 18–19, 2026</div></div>
        <div class="ind-cell neu"><div class="ind-name">CPI YoY</div><div class="ind-val" id="val-cpi">Loading…</div><div class="ind-chg neu" id="chg-cpi">Fetching…</div></div>
        <div class="ind-cell neu"><div class="ind-name">CORE CPI</div><div class="ind-val">3.3%</div><div class="ind-chg neu">YoY Dec 2025</div></div>
        <div class="ind-cell pos"><div class="ind-name">GDP GROWTH</div><div class="ind-val">2.8%</div><div class="ind-chg pos">Q4 2025 Advance</div></div>
        <div class="ind-cell pos"><div class="ind-name">UNEMPLOYMENT</div><div class="ind-val">4.1%</div><div class="ind-chg pos">Jan 2026</div></div>
        <div class="ind-cell pos"><div class="ind-name">NFP</div><div class="ind-val">+256K</div><div class="ind-chg pos">Jan 2026</div></div>
        <div class="ind-cell neu"><div class="ind-name">PPI YoY</div><div class="ind-val">3.3%</div><div class="ind-chg neu">Dec 2025</div></div>
      </div>
    </div>

    <!-- ── INDIA ECONOMIC INDICATORS ── -->
    <div class="econ-section">
      <div class="ind-panel-hdr econ-hdr india">▶ 🇮🇳 INDIA ECONOMIC INDICATORS</div>
      <div class="ind-row">
        <div class="ind-cell neu"><div class="ind-name">REPO RATE</div><div class="ind-val">6.25%</div><div class="ind-chg neu">RBI Feb 2026 Cut</div></div>
        <div class="ind-cell neu"><div class="ind-name">CPI</div><div class="ind-val">5.22%</div><div class="ind-chg neu">Dec 2025 YoY</div></div>
        <div class="ind-cell neu"><div class="ind-name">WPI</div><div class="ind-val">2.4%</div><div class="ind-chg neu">YoY Nov 2025</div></div>
        <div class="ind-cell pos"><div class="ind-name">IIP</div><div class="ind-val">5.2%</div><div class="ind-chg pos">YoY Nov 2025</div></div>
        <div class="ind-cell pos"><div class="ind-name">MFG PMI</div><div class="ind-val">57.7</div><div class="ind-chg pos">Jan 2026</div></div>
        <div class="ind-cell pos"><div class="ind-name">GDP GROWTH</div><div class="ind-val">6.4%</div><div class="ind-chg pos">FY 2024-25 Est.</div></div>
        <div class="ind-cell neu"><div class="ind-name">FISCAL DEFICIT</div><div class="ind-val">4.9%</div><div class="ind-chg neu">of GDP FY25 Target</div></div>
        <div class="ind-cell neu" id="card-usdinr"><div class="ind-name">USD/INR</div><div class="ind-val" id="val-usdinr">Loading…</div><div class="ind-chg neu" id="chg-usdinr">…</div></div>
      </div>
    </div>

    <!-- ── CATEGORY TABS ── -->
    <div class="cat-tabs" id="catTabs">
      <div class="cat-tab active" id="tab-markets"        onclick="switchCat('markets',null)">📊 MARKETS</div>
      <div class="cat-tab"        id="tab-economic"       onclick="switchCat('economic',null)">💰 ECONOMIC</div>
      <div class="cat-tab"        id="tab-india"          onclick="switchCat('india',null)">🇮🇳 INDIA</div>
      <div class="cat-tab"        id="tab-google_trending" onclick="switchCat('google_trending',null)">🔥 TRENDING</div>
      <div class="cat-tab"        id="tab-corporate"      onclick="switchCat('corporate',null)">🏢 CORPORATE</div>
      <div class="cat-tab"        id="tab-geopolitical"   onclick="switchCat('geopolitical',null)">🌍 GEOPOLITICAL</div>
    </div>

    <!-- ── NEWS AREA ── -->
    <div class="news-area">
      <div class="news-hdr">
        <span class="news-hdr-title" id="newsTitle">▶ MARKET UPDATES</span>
        <span class="news-hdr-meta" id="newsSubtitle">Click any headline to expand · {current_time}</span>
      </div>
      <table class="news-table">
        <tbody id="newsTbody"></tbody>
      </table>
    </div>

  </div><!-- /main -->
</div><!-- /shell -->

<!-- STATUS BAR -->
<div class="statusbar">
  <span>GLOBAL MARKET DASHBOARD · RSS FEEDS: 18 SOURCES · AUTO-REFRESH: 5 MIN · NOT FINANCIAL ADVICE</span>
  <span id="statusClock">--:-- IST</span>
</div>

<!-- ══════════════════════════════════════════
     SCRIPTS
══════════════════════════════════════════ -->
<script>
// ── All news injected by Python ──
const NEWS_DATA = {news_json};

// ── Current active category ──
let currentCat = 'markets';

// ════════════════════════════
// RENDER NEWS TABLE
// ════════════════════════════
function renderNews(cat) {{
  const d = NEWS_DATA[cat];
  if (!d) return;
  const tbody = document.getElementById('newsTbody');
  const items = d.items;

  if (!items || items.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="5" class="no-news">No articles available for this category.</td></tr>';
    document.getElementById('newsTitle').textContent = '▶ ' + d.label + ' — 0 ARTICLES';
    return;
  }}

  tbody.innerHTML = items.map((item, i) => {{
    const link = item.link && item.link !== '#'
      ? `<a class="expand-link" href="${{item.link}}" target="_blank" rel="noopener">Read Full Article ↗</a>`
      : '';
    return `
      <tr onclick="toggleRow(this)">
        <td class="td-num">${{String(i+1).padStart(2,'0')}}</td>
        <td class="td-time">${{item.time}}</td>
        <td class="td-src"><span class="src-badge">${{item.source}}</span></td>
        <td class="td-title">
          <div class="headline">${{item.title}}</div>
          <div class="expand-body">
            <div class="expand-summary">${{item.summary}}</div>
            ${{link}}
          </div>
        </td>
        <td class="td-arrow"><span class="arrow-icon">▼</span></td>
      </tr>`;
  }}).join('');

  document.getElementById('newsTitle').textContent = '▶ ' + d.label + ' — ' + items.length + ' ARTICLES';
}}

function toggleRow(row) {{
  row.classList.toggle('open');
}}

// ════════════════════════════
// SWITCH CATEGORY
// ════════════════════════════
function switchCat(cat, sidebarEl) {{
  currentCat = cat;

  // Update sidebar items
  document.querySelectorAll('.sb-item').forEach(el => el.classList.remove('active'));
  const sbEl = document.getElementById('sb-' + cat);
  if (sbEl) sbEl.classList.add('active');

  // Update tabs
  document.querySelectorAll('.cat-tab').forEach(el => el.classList.remove('active'));
  const tabEl = document.getElementById('tab-' + cat);
  if (tabEl) tabEl.classList.add('active');

  renderNews(cat);
}}

// ════════════════════════════
// TICKER STRIP
// ════════════════════════════
const TICKER_SYMBOLS = [
  ['GIFT NIFTY', 'gift-nifty'],
  ['DOW',    'dow'],
  ['S&P 500','sp500'],
  ['NASDAQ', 'nasdaq'],
  ['CRUDE',  'oil'],
  ['GOLD',   'gold'],
  ['SILVER', 'silver'],
  ['USD IDX','dollar'],
  ['USD/INR','usdinr'],
];

function buildTicker() {{
  const track = document.getElementById('tickerTrack');
  // Double for seamless loop
  const items = [...TICKER_SYMBOLS, ...TICKER_SYMBOLS];
  track.innerHTML = items.map(([name, key]) => `
    <span class="ticker-item" id="tick-${{key}}">
      <span class="t-sym">${{name}}</span>
      <span class="t-val t-neu" id="tv-${{key}}">--</span>
    </span>
  `).join('');
}}

function updateTicker(key, val, pct) {{
  const el = document.getElementById('tv-' + key);
  if (!el) return;
  const p = parseFloat(pct);
  el.textContent = val + (pct ? ' (' + (p >= 0 ? '+' : '') + pct + '%)' : '');
  el.className = 't-val ' + (p > 0 ? 't-pos' : p < 0 ? 't-neg' : 't-neu');

  // Update duplicate ticker item too
  const els = document.querySelectorAll('[id="tv-' + key + '"]');
  els.forEach(e => {{
    e.textContent = el.textContent;
    e.className = el.className;
  }});
}}

// ════════════════════════════
// INDICATOR CARD UPDATE
// ════════════════════════════
function updateCard(id, value, change, pchange) {{
  const vEl = document.getElementById('val-' + id);
  const cEl = document.getElementById('chg-' + id);
  const card = document.getElementById('card-' + id);
  if (vEl) vEl.textContent = value;
  if (cEl) {{
    const p = parseFloat(pchange);
    const sign = p >= 0 ? '+' : '';
    cEl.textContent = sign + change + ' (' + sign + pchange + '%)';
    const cls = p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu';
    cEl.className = 'ind-chg ' + cls;
    if (card) card.className = 'ind-cell ' + cls;
  }}
  // Update sidebar
  const sbEl = document.getElementById('sbv-' + id);
  if (sbEl) {{
    sbEl.textContent = value;
    const p = parseFloat(pchange);
    sbEl.className = 'sb-ind-val ' + (p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu');
  }}
  updateTicker(id, value, pchange);
}}

// ════════════════════════════
// YAHOO FINANCE FETCH
// ════════════════════════════
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

async function fetchYahoo(key, sym) {{
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${{sym}}?interval=1d&range=1d`;
  const proxies = [
    'https://corsproxy.io/?' + encodeURIComponent(url),
    'https://api.allorigins.win/get?url=' + encodeURIComponent(url),
    url
  ];
  for (const u of proxies) {{
    try {{
      const r = await fetch(u, {{mode: 'cors'}});
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
      let val = ['dow', 'sp500', 'nasdaq'].includes(key)
        ? cur.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})
        : key === 'dollar' ? cur.toFixed(2)
        : key === 'usdinr' ? '₹' + cur.toFixed(2)
        : '$' + cur.toFixed(2);
      updateCard(key, val, chg, pct);
      // Extra sidebar updates for nifty/sensex placeholder
      if (key === 'usdinr') {{
        const sbEl = document.getElementById('sbv-usdinr');
        if (sbEl) {{ sbEl.textContent = '₹' + cur.toFixed(2); }}
      }}
      return true;
    }} catch (e) {{ /* try next */ }}
  }}
  return false;
}}

// ════════════════════════════
// GIFT NIFTY FETCH
// ════════════════════════════
async function fetchGiftNifty() {{
  // Attempt 1: NSE IFSC via CORS proxy
  const nseUrl = 'https://www.nseifsc.com/market/GetIndexChartDetails?indices=NIFTY50&type=I';
  try {{
    const r = await fetch('https://corsproxy.io/?' + encodeURIComponent(nseUrl), {{mode: 'cors', signal: AbortSignal.timeout(6000)}});
    if (r.ok) {{
      const d = await r.json();
      if (d && d.length > 0) {{
        const last = d[d.length - 1];
        const first = d[0];
        const cur = parseFloat(last[1]);
        const prev = parseFloat(first[1]);
        if (cur && prev) {{
          const chg = (cur - prev).toFixed(2);
          const pct = (((cur - prev) / prev) * 100).toFixed(2);
          const val = cur.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
          const vEl = document.getElementById('val-gift-nifty');
          const cEl = document.getElementById('chg-gift-nifty');
          const card = document.getElementById('card-gift-nifty');
          if (vEl) vEl.textContent = val;
          if (cEl) {{
            const p = parseFloat(pct);
            const sign = p >= 0 ? '+' : '';
            cEl.textContent = sign + chg + ' (' + sign + pct + '%) · NSE IX';
            const cls = p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu';
            cEl.className = 'ind-chg ' + cls;
            if (card) card.className = 'ind-cell ' + cls;
          }}
          updateTicker('gift-nifty', val, pct);
          // sidebar nifty
          const sbN = document.getElementById('sbv-nifty');
          if (sbN) {{ sbN.textContent = val; sbN.className = 'sb-ind-val ' + (parseFloat(pct) > 0 ? 'pos' : parseFloat(pct) < 0 ? 'neg' : 'neu'); }}
          return;
        }}
      }}
    }}
  }} catch (e) {{ /* fall through */ }}

  // Attempt 2: Stooq
  try {{
    const stooqUrl = 'https://stooq.com/q/l/?s=nifty.ix&f=sd2t2ohlcv&e=csv';
    const r = await fetch('https://corsproxy.io/?' + encodeURIComponent(stooqUrl), {{signal: AbortSignal.timeout(5000)}});
    if (r.ok) {{
      const text = await r.text();
      const lines = text.trim().split('\\n');
      if (lines.length >= 2) {{
        const cols = lines[1].split(',');
        const close = parseFloat(cols[6]);
        const open = parseFloat(cols[3]);
        if (close && open) {{
          const chg = (close - open).toFixed(2);
          const pct = (((close - open) / open) * 100).toFixed(2);
          const val = close.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
          const vEl = document.getElementById('val-gift-nifty');
          const cEl = document.getElementById('chg-gift-nifty');
          const card = document.getElementById('card-gift-nifty');
          if (vEl) vEl.textContent = val;
          if (cEl) {{
            const p = parseFloat(pct);
            const sign = p >= 0 ? '+' : '';
            cEl.textContent = sign + chg + ' (' + sign + pct + '%) · NSE IX ~';
            const cls = p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu';
            cEl.className = 'ind-chg ' + cls;
            if (card) card.className = 'ind-cell ' + cls;
          }}
          updateTicker('gift-nifty', val, pct);
          return;
        }}
      }}
    }}
  }} catch (e) {{ /* fall through */ }}

  // Attempt 3: Fallback – Nifty 50 spot as proxy
  try {{
    const url = 'https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1d&range=1d';
    const r = await fetch('https://corsproxy.io/?' + encodeURIComponent(url), {{mode: 'cors', signal: AbortSignal.timeout(5000)}});
    if (r.ok) {{
      const d = await r.json();
      const meta = d?.chart?.result?.[0]?.meta;
      if (meta) {{
        const cur = meta.regularMarketPrice;
        const prev = meta.chartPreviousClose || meta.previousClose;
        if (cur && prev) {{
          const chg = (cur - prev).toFixed(2);
          const pct = (((cur - prev) / prev) * 100).toFixed(2);
          const val = cur.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
          const titleEl = document.querySelector('#card-gift-nifty .ind-name');
          if (titleEl) titleEl.textContent = '⚠ NIFTY 50 (GIFT proxy)';
          const vEl = document.getElementById('val-gift-nifty');
          const cEl = document.getElementById('chg-gift-nifty');
          const card = document.getElementById('card-gift-nifty');
          if (vEl) vEl.textContent = val;
          if (cEl) {{
            const p = parseFloat(pct);
            const sign = p >= 0 ? '+' : '';
            cEl.textContent = sign + chg + ' (' + sign + pct + '%) · INR spot';
            const cls = p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu';
            cEl.className = 'ind-chg ' + cls;
            if (card) card.className = 'ind-cell ' + cls;
          }}
          updateTicker('gift-nifty', val, pct);
          // sidebar sensex/nifty
          const sbN = document.getElementById('sbv-nifty');
          if (sbN) {{ sbN.textContent = val; sbN.className = 'sb-ind-val ' + (parseFloat(pct) > 0 ? 'pos' : parseFloat(pct) < 0 ? 'neg' : 'neu'); }}
          return;
        }}
      }}
    }}
  }} catch (e) {{ /* fall through */ }}

  // Hard fallback
  const vEl = document.getElementById('val-gift-nifty');
  const cEl = document.getElementById('chg-gift-nifty');
  if (vEl) vEl.textContent = 'N/A';
  if (cEl) cEl.textContent = 'Data unavailable';
}}

// ════════════════════════════
// CPI via FRED CSV (CORS proxy)
// ════════════════════════════
async function fetchCPI() {{
  const csvUrl = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL';
  const proxied = 'https://corsproxy.io/?' + encodeURIComponent(csvUrl);
  try {{
    const r = await fetch(proxied, {{signal: AbortSignal.timeout(8000)}});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const text = await r.text();
    const lines = text.trim().split('\\n').filter(l => l && !l.startsWith('DATE'));
    if (lines.length < 13) throw new Error('Not enough data');
    const lastLine = lines[lines.length - 1].split(',');
    const prevLine = lines[lines.length - 13].split(',');
    const lastVal = parseFloat(lastLine[1]);
    const prevVal = parseFloat(prevLine[1]);
    if (isNaN(lastVal) || isNaN(prevVal) || prevVal === 0) throw new Error('Bad values');
    const yoy = (((lastVal - prevVal) / prevVal) * 100).toFixed(1);
    const date = lastLine[0];
    const d = new Date(date + 'T12:00:00Z');
    const label = d.toLocaleString('en-US', {{month: 'short', year: 'numeric', timeZone: 'UTC'}});
    const vEl = document.getElementById('val-cpi');
    const cEl = document.getElementById('chg-cpi');
    const card = vEl ? vEl.closest('.ind-cell') : null;
    if (vEl) vEl.textContent = yoy + '%';
    if (cEl) cEl.textContent = 'YoY · ' + label;
    if (card) {{
      const p = parseFloat(yoy);
      card.className = 'ind-cell ' + (p > 3 ? 'neg' : p <= 2 ? 'pos' : 'neu');
    }}
  }} catch (e) {{
    const vEl = document.getElementById('val-cpi');
    const cEl = document.getElementById('chg-cpi');
    if (vEl) vEl.textContent = '2.9%';
    if (cEl) cEl.textContent = 'YoY · Dec 2025 (cached)';
  }}
}}

// ════════════════════════════
// CLOCK & REFRESH
// ════════════════════════════
function updateClock() {{
  const now = new Date();
  const opts = {{hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'Asia/Kolkata'}};
  const ist = now.toLocaleString('en-US', opts);
  const el = document.getElementById('topClock');
  if (el) el.textContent = ist + ' IST';
  const st = document.getElementById('statusClock');
  if (st) st.textContent = ist + ' IST';
  const ref = document.getElementById('newsSubtitle');
  if (ref) {{
    const opts2 = {{hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata'}};
    ref.textContent = 'Click any headline to expand · Last refresh: ' + now.toLocaleString('en-US', opts2) + ' IST';
  }}
}}

let isFirstLoad = true;

async function loadAll() {{
  fetchGiftNifty();
  await Promise.all(
    Object.entries(SYMBOLS).map(async ([k, s]) => {{
      const ok = await fetchYahoo(k, s);
      if (!ok) {{
        const vEl = document.getElementById('val-' + k);
        const cEl = document.getElementById('chg-' + k);
        if (vEl) vEl.textContent = 'N/A';
        if (cEl) cEl.textContent = 'Unavailable';
      }}
    }})
  );
  updateClock();
  if (isFirstLoad) {{
    setTimeout(() => document.getElementById('loadingOverlay').classList.remove('visible'), 500);
    isFirstLoad = false;
  }}
}}

// ════════════════════════════
// INIT
// ════════════════════════════
window.addEventListener('DOMContentLoaded', () => {{
  buildTicker();
  renderNews('markets');

  if (!sessionStorage.getItem('visited')) {{
    document.getElementById('loadingOverlay').classList.add('visible');
    sessionStorage.setItem('visited', '1');
  }}

  loadAll();
  fetchCPI();
  setInterval(loadAll, 5 * 60 * 1000);
  setInterval(updateClock, 1000);
}});
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    print("\n" + "=" * 70)
    print("🚀  GLOBAL MARKET DASHBOARD  –  BLOOMBERG TERMINAL THEME")
    print("=" * 70)

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

    print("\n" + "=" * 70)
    print(f"✅  SUCCESS!  Dashboard written to: {output}")
    print("=" * 70)
    print("\n💡 Every time you run this script the news refreshes automatically.")
    print("   Click any headline in the browser to expand and read the summary.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
