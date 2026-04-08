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
from datetime import datetime, timedelta, timezone
import html as html_module
import re
import calendar
import logging

# ─────────────────────────────────────────────
#  LOGGING SETUP
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)

# ─────────────────────────────────────────────
#  NEWS SOURCES  (RSS feeds – no API key needed)
# ─────────────────────────────────────────────
RSS_SOURCES = {
    # 1 ── Markets + Earnings + IPO & Deals
    "markets": [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC&region=US&lang=en-US",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://news.google.com/rss/search?q=earnings+results+IPO+stock+market+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 2 ── Macro & Policy + Trade & Tariffs
    "macro_policy": [
        "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/economy-politics/",
        "https://www.federalreserve.gov/feeds/press_all.xml",
        "https://news.google.com/rss/search?q=trade+tariffs+WTO+supply+chain+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 3 ── Banking & FX + Forex
    "banking_fx": [
        "https://news.google.com/rss/search?q=central+bank+interest+rates+Fed+ECB+RBI+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://www.cnbc.com/id/10000108/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/financialservices/",
        "https://news.google.com/rss/search?q=forex+USD+EUR+JPY+GBP+currency+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 4 ── Commodities & Energy + OPEC
    "commodities_energy": [
        "https://news.google.com/rss/search?q=commodities+copper+wheat+natural+gas+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://feeds.marketwatch.com/marketwatch/commodities/",
        "https://www.cnbc.com/id/10000113/device/rss/rss.html",
        "https://news.google.com/rss/search?q=OPEC+oil+energy+renewables+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 5 ── India Markets (includes trending)
    "india": [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://www.moneycontrol.com/rss/marketreports.xml",
        "https://economictimes.indiatimes.com/rssfeeds/1373380680.cms",
        "https://news.google.com/rss/search?q=NSE+BSE+Nifty+Sensex+stock+market+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=india+stocks+trending+today+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    # 6 ── Bonds & Rates (NEW)
    "bonds_rates": [
        "https://news.google.com/rss/search?q=treasury+yields+10+year+bond+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=yield+curve+sovereign+debt+credit+spread+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://feeds.marketwatch.com/marketwatch/bonds/",
    ],
    # 7 ── Corporate News
    "corporate": [
        "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/marketpulse/",
        "https://finance.yahoo.com/rss/topfinstories",
    ],
    # 8 ── Geopolitical
    "geopolitical": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
    ],
    # 9 ── Crypto & Web3
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://news.google.com/rss/search?q=bitcoin+ethereum+crypto+DeFi+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 10 ── Tech & AI
    "tech_ai": [
        "https://news.google.com/rss/search?q=artificial+intelligence+AI+tech+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=OpenAI+Google+AI+Microsoft+AI+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=AI+chips+semiconductor+LLM+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 11 ── Asia & China (China + Japan/Nikkei/BOJ)
    "asia_china": [
        "https://news.google.com/rss/search?q=china+stock+market+Hang+Seng+Shanghai+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=PBOC+yuan+China+economy+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://feeds.reuters.com/reuters/CNtopNews",
        "https://news.google.com/rss/search?q=Nikkei+Japan+BOJ+yen+Asia+markets+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 12 ── Europe & UK (NEW)
    "europe_uk": [
        "https://news.google.com/rss/search?q=DAX+FTSE+Euro+Stoxx+European+markets+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=ECB+Bank+of+England+interest+rates+Europe+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://feeds.reuters.com/reuters/UKTopNews",
        "https://news.google.com/rss/search?q=FTSE+100+UK+economy+pound+sterling+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 13 ── ESG & Climate (NEW)
    "esg_climate": [
        "https://news.google.com/rss/search?q=ESG+green+bonds+sustainable+investing+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=carbon+market+climate+change+COP+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=renewable+energy+solar+wind+EV+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 14 ── Latin America (NEW)
    "latam": [
        "https://news.google.com/rss/search?q=Bovespa+Brazil+stock+market+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=Mexico+IPC+Argentina+peso+LATAM+economy+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=Latin+America+emerging+markets+commodities+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
}

MAX_NEWS_PER_CATEGORY = 10
REQUEST_TIMEOUT = 8

# ─────────────────────────────────────────────
#  KEY EVENT CALENDAR — FULLY DYNAMIC
#  Primary:  Trading Economics API (guest access, no key needed)
#  Fallback: Computed approximate schedule
# ─────────────────────────────────────────────
EVENT_RSS_FEEDS = [
    "https://news.google.com/rss/search?q=RBI+MPC+repo+rate+decision+upcoming&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=FOMC+Fed+interest+rate+decision+upcoming&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=US+nonfarm+payrolls+CPI+data+release&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=India+GDP+CPI+inflation+data+release&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=ECB+BOJ+interest+rate+decision+meeting&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=OPEC+meeting+oil+output+decision&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=India+F%26O+expiry+quarterly+results+earnings&hl=en-IN&gl=IN&ceid=IN:en",
]

# ── COUNTRY/REGION MAPPING ──
_REGION_MAP = {
    "United States": "USA", "India": "India", "Euro Area": "Europe",
    "Germany": "Europe", "France": "Europe", "Italy": "Europe",
    "United Kingdom": "Europe", "Japan": "Asia", "China": "Asia",
    "South Korea": "Asia", "Australia": "Asia", "Canada": "USA",
    "Brazil": "Global", "Mexico": "Global", "Russia": "Global",
    "Switzerland": "Europe", "New Zealand": "Asia", "Indonesia": "Asia",
    "Singapore": "Asia", "Hong Kong": "Asia", "Taiwan": "Asia",
}

# ── IMPACT MAPPING (Trading Economics uses 1/2/3) ──
_IMPACT_MAP = {3: "🔴 HIGH", 2: "🟡 MEDIUM", 1: "🟢 LOW"}

# ── CATEGORY KEYWORDS → CATEGORY ──
_CATEGORY_KEYWORDS = {
    "Interest Rate": "Central Bank", "Rate Decision": "Central Bank",
    "Repo Rate": "Central Bank", "FOMC": "Central Bank",
    "Fed ": "Central Bank", "MPC": "Central Bank",
    "Monetary Policy": "Central Bank", "Cash Rate": "Central Bank",
    "Refinancing Rate": "Central Bank",
    "Non Farm": "Jobs Data", "Nonfarm": "Jobs Data",
    "Employment": "Jobs Data", "Unemployment": "Jobs Data",
    "Payrolls": "Jobs Data", "Jobless": "Jobs Data",
    "CPI": "Inflation", "Inflation": "Inflation",
    "PPI": "Inflation", "WPI": "Inflation",
    "Consumer Price": "Inflation", "Core PCE": "Inflation",
    "GDP": "GDP", "Gross Domestic": "GDP",
    "PMI": "PMI", "Manufacturing": "PMI",
    "Trade Balance": "Trade", "Exports": "Trade",
    "Imports": "Trade", "Current Account": "Trade",
    "Crude Oil": "Energy", "OPEC": "Energy",
    "Budget": "Fiscal Policy", "Fiscal": "Fiscal Policy",
    "Retail Sales": "Consumer", "Consumer Confidence": "Consumer",
    "Industrial Production": "Industrial", "Factory Orders": "Industrial",
    "Housing": "Real Estate", "Building Permits": "Real Estate",
    "Bond": "Bonds & Rates", "Treasury": "Bonds & Rates",
    "Auction": "Bonds & Rates",
}


def _classify_event(event_name: str) -> str:
    for keyword, category in _CATEGORY_KEYWORDS.items():
        if keyword.lower() in event_name.lower():
            return category
    return "Other"


def _compute_status(date_obj):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    days_away = (date_obj - now).days
    if days_away < -2:
        status = "PASSED"
    elif days_away < 0:
        status = "JUST PASSED"
    elif days_away == 0:
        status = "TODAY"
    elif days_away <= 7:
        status = "THIS WEEK"
    elif days_away <= 30:
        status = "UPCOMING"
    else:
        status = "SCHEDULED"
    return status, days_away  # keep negative for "days ago" display


def fetch_live_economic_calendar() -> list[dict]:
    """
    Fetch REAL upcoming economic events from Trading Economics free API.
    Returns structured list of events sorted by date.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start = now.strftime("%Y-%m-%d")
    end = (now + timedelta(days=90)).strftime("%Y-%m-%d")

    # Countries that affect Indian stock market + major global
    countries = "united%20states,india,euro%20area,japan,united%20kingdom,china"

    # Trading Economics guest API returns HTTP 403 — skip directly to fallback
    raw_events = []
    logging.info("  Trading Economics API unavailable — using computed fallback dates")
    return _compute_fallback_events()

    # Parse into our event format
    events = []
    seen = set()
    for ev in raw_events:
        event_name = ev.get("Event", "").strip()
        country = ev.get("Country", "").strip()
        date_str = ev.get("Date", "")
        importance = ev.get("Importance", 1)

        if not event_name or not date_str:
            continue

        # Deduplicate
        key = f"{date_str[:10]}_{event_name}"
        if key in seen:
            continue
        seen.add(key)

        # Parse date
        try:
            date_obj = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            try:
                date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
            except ValueError:
                continue

        # Skip past events (older than 2 days)
        if date_obj < now - timedelta(days=2):
            continue

        region = _REGION_MAP.get(country, "Global")
        impact = _IMPACT_MAP.get(importance, "🟢 LOW")
        category = _classify_event(event_name)
        status, days_away = _compute_status(date_obj)

        # Add flag emoji based on region
        flag = {"USA": "🇺🇸", "India": "🇮🇳", "Europe": "🇪🇺",
                "Asia": "🌏", "Global": "🌍"}.get(region, "🌍")

        events.append({
            "date": date_obj.strftime("%Y-%m-%d"),
            "date_display": date_obj.strftime("%b %d, %Y (%a)"),
            "title": f"{flag} {event_name}",
            "category": category,
            "impact": impact,
            "region": region,
            "country": country,
            "days_away": days_away,
            "status": status,
            "actual": ev.get("Actual", ""),
            "forecast": ev.get("Forecast", ""),
            "previous": ev.get("Previous", ""),
        })

    events.sort(key=lambda e: e["date"])
    return events


def _nth_weekday(year, month, weekday, n):
    """Return the nth occurrence of a weekday in a month (1-indexed). weekday: 0=Mon..6=Sun."""
    c = calendar.monthcalendar(year, month)
    days = [week[weekday] for week in c if week[weekday] != 0]
    if n <= len(days):
        return datetime(year, month, days[n - 1])
    return None


def _compute_fallback_events() -> list[dict]:
    """
    FALLBACK: Return approximate scheduled financial events when API is unavailable.
    These are computed dynamically relative to the current date.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    year = now.year
    events = []

    def add(date_obj, title, category, impact, region):
        if date_obj and date_obj >= now - timedelta(days=2):
            status, days_away = _compute_status(date_obj)
            events.append({
                "date": date_obj.strftime("%Y-%m-%d"),
                "date_display": date_obj.strftime("%b %d, %Y (%a)"),
                "title": title,
                "category": category,
                "impact": impact,
                "region": region,
                "country": "",
                "days_away": days_away,
                "status": status,
                "actual": "",
                "forecast": "",
                "previous": "",
            })

    # ── FOMC MEETINGS ──
    fomc_months_2025 = [(1,28,29),(3,18,19),(5,6,7),(6,17,18),(7,29,30),(9,16,17),(10,28,29),(12,9,10)]
    fomc_months_2026 = [(1,27,28),(3,17,18),(4,28,29),(6,16,17),(7,28,29),(9,15,16),(10,27,28),(12,8,9)]
    for m, d1, d2 in (fomc_months_2025 if year == 2025 else fomc_months_2026):
        add(datetime(year, m, d2), f"🇺🇸 FOMC Rate Decision ({calendar.month_abbr[m]} {d1}-{d2})",
            "Central Bank", "🔴 HIGH", "USA")

    # ── RBI MPC MEETINGS ──
    rbi_2025 = [(2,7),(4,9),(6,6),(8,8),(10,8),(12,5)]
    rbi_2026 = [(2,6),(4,8),(6,5),(8,7),(10,7),(12,4)]
    for m, d in (rbi_2025 if year == 2025 else rbi_2026):
        try:
            add(datetime(year, m, d), f"🇮🇳 RBI MPC Repo Rate Decision ({calendar.month_abbr[m]})",
                "Central Bank", "🔴 HIGH", "India")
        except ValueError:
            pass

    # ── US Non-Farm Payrolls (1st Friday of each month) ──
    for m in range(1, 13):
        nfp = _nth_weekday(year, m, 4, 1)
        if nfp:
            add(nfp, f"🇺🇸 US Non-Farm Payrolls ({calendar.month_abbr[m]})",
                "Jobs Data", "🔴 HIGH", "USA")

    # ── US CPI (~12th-14th of each month) ──
    for m in range(1, 13):
        d = 13 if m % 2 == 0 else 12
        try:
            add(datetime(year, m, d), f"🇺🇸 US CPI Inflation Data ({calendar.month_abbr[m]})",
                "Inflation", "🔴 HIGH", "USA")
        except ValueError:
            pass

    # ── India CPI (~12th of each month) ──
    for m in range(1, 13):
        try:
            add(datetime(year, m, 12), f"🇮🇳 India CPI Data ({calendar.month_abbr[m]})",
                "Inflation", "🟡 MEDIUM", "India")
        except ValueError:
            pass

    # ── ECB Rate Decisions ──
    ecb_2025 = [(1,30),(3,6),(4,17),(6,5),(7,24),(9,11),(10,30),(12,18)]
    ecb_2026 = [(1,22),(3,5),(4,16),(6,4),(7,16),(9,10),(10,29),(12,17)]
    for m, d in (ecb_2025 if year == 2025 else ecb_2026):
        try:
            add(datetime(year, m, d), f"🇪🇺 ECB Rate Decision ({calendar.month_abbr[m]} {d})",
                "Central Bank", "🟡 MEDIUM", "Europe")
        except ValueError:
            pass

    # ── BOJ Meetings ──
    boj_2025 = [(1,24),(3,14),(4,30),(6,13),(7,31),(9,19),(10,31),(12,19)]
    boj_2026 = [(1,23),(3,13),(4,29),(6,12),(7,17),(9,18),(10,30),(12,18)]
    for m, d in (boj_2025 if year == 2025 else boj_2026):
        try:
            add(datetime(year, m, d), f"🇯🇵 BOJ Rate Decision ({calendar.month_abbr[m]} {d})",
                "Central Bank", "🟡 MEDIUM", "Asia")
        except ValueError:
            pass

    # ── India GDP (quarterly) ──
    for m, d in [(2,28),(5,30),(8,29),(11,28)]:
        try:
            add(datetime(year, m, d), f"🇮🇳 India GDP Data ({calendar.month_abbr[m]})",
                "GDP", "🟡 MEDIUM", "India")
        except ValueError:
            pass

    # ── US GDP (advance estimates) ──
    for m, d in [(1,30),(4,30),(7,30),(10,30)]:
        try:
            add(datetime(year, m, d), f"🇺🇸 US GDP Advance Estimate",
                "GDP", "🟡 MEDIUM", "USA")
        except ValueError:
            pass

    # ── India Union Budget ──
    add(datetime(year, 2, 1), "🇮🇳 India Union Budget", "Fiscal Policy", "🔴 HIGH", "India")

    # ── OPEC+ Meetings ──
    for m, d in [(3,1),(6,1),(9,1),(12,1)]:
        add(datetime(year, m, d), f"🛢️ OPEC+ Meeting ({calendar.month_abbr[m]})",
            "Energy", "🟡 MEDIUM", "Global")

    # ── India F&O Expiry (last Thursday of each month) ──
    for m in range(1, 13):
        c = calendar.monthcalendar(year, m)
        thursdays = [week[3] for week in c if week[3] != 0]
        if thursdays:
            add(datetime(year, m, thursdays[-1]), f"🇮🇳 F&O Monthly Expiry ({calendar.month_abbr[m]})",
                "Derivatives", "🟡 MEDIUM", "India")

    events.sort(key=lambda e: e["date"])
    return events


def fetch_event_news() -> list[dict]:
    """Fetch latest news about upcoming economic events from RSS."""
    seen = set()
    results = []
    for url in EVENT_RSS_FEEDS:
        for item in fetch_rss(url):
            key = item["title"].lower()[:60]
            if key in seen:
                continue
            seen.add(key)
            results.append(item)
            if len(results) >= 20:
                break
        if len(results) >= 20:
            break
    return results[:20]


def build_event_calendar_json(events: list[dict]) -> str:
    return json.dumps(events, ensure_ascii=False)


def build_event_news_json(news_items: list[dict]) -> str:
    out = []
    for item in news_items:
        out.append({
            "title": escape(item.get("title", "")),
            "source": escape(item.get("source", "")),
            "time": format_pub_date(item.get("pubDate", "")),
            "summary": escape(item.get("summary", "")),
            "link": escape(item.get("link", "#")),
        })
    return json.dumps(out, ensure_ascii=False)


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
            "cointelegraph.com": "CoinTelegraph",
            "coindesk.com": "CoinDesk",
            "feedburner.com": "TechCrunch",
            "techcrunch.com": "TechCrunch",
            "news.google.com": "Google News",
            "ft.com": "Financial Times",
            "bbc.co.uk": "BBC",
            "theguardian.com": "The Guardian",
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
        logging.warning(f"Could not fetch {url}: {e}")
    return items


def fetch_category_news(category: str, urls: list[str]) -> list[dict]:
    seen_titles = set()
    results = []

    DATE_FMTS = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]

    def is_within_window(pub_date_str: str, cutoff: datetime) -> bool:
        if not pub_date_str:
            return False
        for fmt in DATE_FMTS:
            try:
                pub = datetime.strptime(pub_date_str.strip(), fmt)
                # Always normalize to naive UTC before comparing with cutoff
                if pub.tzinfo is not None:
                    pub = datetime(*pub.utctimetuple()[:6])
                # cutoff is already datetime.now(timezone.utc).replace(tzinfo=None) based — comparison is safe
                return pub >= cutoff
            except ValueError:
                continue
        return False

    def _collect(cutoff: datetime) -> None:
        for url in urls:
            logging.info(f"  Fetching {url[:60]}")
            for item in fetch_rss(url):
                key = item["title"].lower()[:60]
                if key in seen_titles:
                    continue
                if not is_within_window(item.get("pubDate", ""), cutoff):
                    continue
                seen_titles.add(key)
                results.append(item)
                if len(results) >= MAX_NEWS_PER_CATEGORY:
                    return
            if len(results) >= MAX_NEWS_PER_CATEGORY:
                return

    # Pass 1: last 24 hours
    _collect(datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24))

    # Pass 2 fallback: extend to 2 days if fewer than 5 articles
    if len(results) < 5:
        logging.warning(f"Only {len(results)} articles in 24h for [{category}] — extending to 2-day window")
        _collect(datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=2))

    return results[:MAX_NEWS_PER_CATEGORY]


def format_pub_date(raw: str) -> str:
    if not raw:
        return "Just now"
    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            # Always normalize to naive UTC so diff is always accurate
            if dt.tzinfo is not None:
                dt_utc = dt.utctimetuple()
                dt = datetime(*dt_utc[:6])
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            diff = now - dt
            total_seconds = diff.total_seconds()
            if total_seconds < 0:
                return "Just now"
            if total_seconds < 3600:
                mins = int(total_seconds // 60)
                return f"{mins} min ago" if mins > 1 else "Just now"
            if total_seconds < 86400:
                hours = int(total_seconds // 3600)
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            if diff.days == 1:
                return "1 day ago"
            # For anything 2+ days old, show the actual date — never lie
            return dt.strftime("%b %d, %Y")
        except ValueError:
            continue
    return raw[:20]


# ─────────────────────────────────────────────
#  HTML GENERATION
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
#  SERVER-SIDE ECONOMIC DATA FETCHER
#  Fetches all indicators from Python directly
#  (no CORS proxy needed — always fresh)
# ─────────────────────────────────────────────
ECON_FETCH_TIMEOUT = 30


def _fetch_json(url: str):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; MarketDashboard/2.0)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=ECON_FETCH_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; MarketDashboard/2.0)",
    })
    with urllib.request.urlopen(req, timeout=ECON_FETCH_TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


FRED_API_KEY = "945a102ffb72e3b04414990e35bd8aa7"


def _fred_series(series_id: str, n: int = 14) -> list[list[str]]:
    """
    Fetch FRED series via authenticated JSON API.
    Returns last n observations as [date, value] pairs.
    Falls back to public CSV if the API call fails.
    """
    try:
        url = (
            "https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
            f"&sort_order=desc&limit={n}"
        )
        data = _fetch_json(url)
        obs = [o for o in data.get("observations", []) if o.get("value") not in (".", "")]
        return [[o["date"], o["value"]] for o in reversed(obs)]
    except Exception as e:
        logging.warning(f"FRED API fallback to CSV for {series_id}: {e}")
        text = _fetch_text(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}")
        lines = [l for l in text.strip().split("\n") if l and not l.startswith("DATE")]
        return [l.split(",") for l in lines[-n:]]


def _fred_csv_last_rows(series_id: str, n: int = 14) -> list[list[str]]:
    """Alias kept for backward compatibility."""
    return _fred_series(series_id, n)


def _fred_yoy(series_id: str) -> tuple[str, str, str]:
    """Compute YoY % from FRED monthly series. Returns (yoy_str, date_label, raw_date)."""
    rows = _fred_series(series_id, 14)
    if len(rows) < 13:
        raise ValueError("Not enough data")
    last_val = float(rows[-1][1])
    prev_val = float(rows[-13][1])
    if prev_val == 0:
        raise ValueError("Zero denominator")
    yoy = ((last_val - prev_val) / prev_val) * 100
    d = datetime.strptime(rows[-1][0], "%Y-%m-%d")
    label = d.strftime("%b %Y")
    return f"{yoy:.1f}", label, rows[-1][0]


def _world_bank(indicator: str, country: str = "IN", mrv: int = 2):
    """Fetch latest value from World Bank API."""
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&mrv={mrv}"
    data = _fetch_json(url)
    rows = [r for r in (data[1] or []) if r.get("value") is not None]
    if not rows:
        raise ValueError("No data")
    return rows


def fetch_all_economic_data() -> dict:
    """
    Fetch all economic indicators server-side.
    USA  : FRED (Federal Reserve) — free, no key, reliable CSV/JSON API
    India: World Bank API (annual) + Google News RSS for repo rate
    No Trading Economics dependency — guest access returns HTTP 403.
    """
    result = {}

    def safe(key, fn):
        try:
            result[key] = fn()
            logging.info(f"    ✓ {key}")
        except Exception as e:
            logging.warning(f"    ✗ {key}: {e}")
            result[key] = None

    # ════════════════════════════════════════════
    #  USA — FRED (api.stlouisfed.org, free, no key)
    # ════════════════════════════════════════════

    def fetch_us_fedfunds():
        lower_rows = _fred_series("DFEDTARL", 2)
        upper_rows = _fred_series("DFEDTARU", 2)
        lower = float(lower_rows[-1][1])
        upper = float(upper_rows[-1][1])
        return {"value": f"{lower:.2f}–{upper:.2f}%", "note": "Fed target range", "css": "neu"}
    safe("us_fedfunds", fetch_us_fedfunds)

    def fetch_us_cpi():
        yoy, label, _ = _fred_yoy("CPIAUCSL")
        v = float(yoy)
        return {"value": f"{yoy}%", "note": f"YoY · {label}",
                "css": "neg" if v > 3 else ("pos" if v <= 2 else "neu")}
    safe("us_cpi", fetch_us_cpi)

    def fetch_us_core_cpi():
        yoy, label, _ = _fred_yoy("CPILFESL")
        v = float(yoy)
        return {"value": f"{yoy}%", "note": f"Core YoY · {label}",
                "css": "neg" if v > 3 else ("pos" if v <= 2 else "neu")}
    safe("us_core_cpi", fetch_us_core_cpi)

    def fetch_us_gdp():
        rows = _fred_series("A191RL1Q225SBEA", 4)
        val = float(rows[-1][1])
        d = datetime.strptime(rows[-1][0], "%Y-%m-%d")
        qtr = (d.month - 1) // 3 + 1
        return {"value": f"{val:.1f}%", "note": f"Q{qtr} {d.year} annualised",
                "css": "pos" if val > 0 else "neg"}
    safe("us_gdp", fetch_us_gdp)

    def fetch_us_unemployment():
        rows = _fred_series("UNRATE", 2)
        val = float(rows[-1][1])
        d = datetime.strptime(rows[-1][0], "%Y-%m-%d")
        return {"value": f"{val:.1f}%", "note": d.strftime("%b %Y"),
                "css": "pos" if val < 4 else ("neg" if val > 5 else "neu")}
    safe("us_unemployment", fetch_us_unemployment)

    def fetch_us_nfp():
        rows = _fred_series("PAYEMS", 3)
        change = round(float(rows[-1][1]) - float(rows[-2][1]))
        sign = "+" if change >= 0 else ""
        d = datetime.strptime(rows[-1][0], "%Y-%m-%d")
        return {"value": f"{sign}{change}K", "note": d.strftime("%b %Y"),
                "css": "pos" if change > 0 else "neg"}
    safe("us_nfp", fetch_us_nfp)

    def fetch_us_ppi():
        yoy, label, _ = _fred_yoy("PPIFIS")
        v = float(yoy)
        return {"value": f"{yoy}%", "note": f"YoY · {label}",
                "css": "neg" if v > 3 else ("pos" if v <= 2 else "neu")}
    safe("us_ppi", fetch_us_ppi)

    # ════════════════════════════════════════════
    #  INDIA — World Bank API + Google News RSS
    #  World Bank: api.worldbank.org, free, CORS-open, JSON
    # ════════════════════════════════════════════

    def fetch_india_repo():
        # Source 1: RBI official policy rates page — multi-pattern scrape
        rbi_urls = [
            "https://rbi.org.in/Scripts/bs_viewcontent.aspx?Id=2118",
            "https://rbi.org.in/en/web/rbi/monetary-policy",
        ]
        patterns = [
            r'Policy Repo Rate\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*%',
            r'Repo Rate\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*%',
            r'repo rate[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*(?:per cent|percent|%)',
            r'([0-9]+\.[0-9]+)\s*%.*?[Rr]epo',
            r'[Rr]epo[^0-9]*([0-9]+\.[0-9]+)',
        ]
        for rbi_url in rbi_urls:
            try:
                html_text = _fetch_text(rbi_url)
                for pat in patterns:
                    m = re.search(pat, html_text, re.IGNORECASE)
                    if m:
                        val = float(m.group(1))
                        if 1.0 <= val <= 20.0:
                            return {"value": f"{val:.2f}%", "note": "RBI", "css": "neu"}
            except Exception:
                continue

        # Source 2: Google News RSS — parse rate from headlines
        rss_url = ("https://news.google.com/rss/search?"
                   "q=RBI+repo+rate+percent&hl=en-IN&gl=IN&ceid=IN:en")
        text = _fetch_text(rss_url)
        for pat in [r'repo rate[^0-9%]{0,30}(\d+(?:\.\d+)?)\s*%',
                    r'(\d+(?:\.\d+)?)\s*%\s*repo rate',
                    r'repo rate[^0-9]{0,20}(\d+\.\d+)']:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = float(m.group(1))
                if 1.0 <= val <= 20.0:
                    return {"value": f"{val:.2f}%", "note": "RBI · news", "css": "neu"}

        raise ValueError("All sources failed for India Repo Rate")
    safe("india_repo", fetch_india_repo)

    def fetch_india_cpi():
        # World Bank annual CPI inflation (most recent available)
        rows = _world_bank("FP.CPI.TOTL.ZG", "IN", 2)
        val = float(rows[0]["value"])
        yr = str(rows[0]["date"])
        return {"value": f"{val:.1f}%", "note": f"FY{yr[2:]} (WB annual)",
                "css": "neg" if val > 6 else ("pos" if val < 4 else "neu")}
    safe("india_cpi", fetch_india_cpi)

    def fetch_india_gdp():
        rows = _world_bank("NY.GDP.MKTP.KD.ZG", "IN", 2)
        val = float(rows[0]["value"])
        yr = str(rows[0]["date"])
        return {"value": f"{val:.1f}%", "note": f"FY{yr[2:]} (WB annual)",
                "css": "pos" if val > 5 else ("neg" if val < 0 else "neu")}
    safe("india_gdp", fetch_india_gdp)

    def fetch_india_unemp():
        rows = _world_bank("SL.UEM.TOTL.ZS", "IN", 2)
        val = float(rows[0]["value"])
        yr = str(rows[0]["date"])
        return {"value": f"{val:.1f}%", "note": f"FY{yr[2:]} (WB annual)",
                "css": "pos" if val < 5 else "neg"}
    safe("india_unemp", fetch_india_unemp)

    def fetch_india_wpi():
        rows = _world_bank("FP.WPI.TOTL", "IN", 3)
        if len(rows) >= 2:
            cur, prev = float(rows[0]["value"]), float(rows[1]["value"])
            yoy = ((cur - prev) / prev) * 100
            yr = str(rows[0]["date"])
            return {"value": f"{yoy:.1f}%", "note": f"FY{yr[2:]} (WB annual)", "css": "neu"}
        raise ValueError("Not enough WPI rows")
    safe("india_wpi", fetch_india_wpi)

    def fetch_india_pmi():
        # No free real-time PMI API; use World Bank manufacturing growth as proxy
        rows = _world_bank("NV.IND.MANF.KD.ZG", "IN", 2)
        val = float(rows[0]["value"])
        yr = str(rows[0]["date"])
        return {"value": f"{val:.1f}%", "note": f"Mfg growth · FY{yr[2:]} (WB)",
                "css": "pos" if val > 0 else "neg"}
    safe("india_pmi", fetch_india_pmi)

    def fetch_india_fiscal():
        rows = _world_bank("GC.BAL.CASH.GD.ZS", "IN", 2)
        val = abs(float(rows[0]["value"]))
        yr = str(rows[0]["date"])
        return {"value": f"{val:.1f}%", "note": f"of GDP · FY{yr[2:]} (WB annual)", "css": "neu"}
    safe("india_fiscal", fetch_india_fiscal)

    return result

def build_econ_data_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


# ─────────────────────────────────────────────
#  TIME UTILS
# ─────────────────────────────────────────────
def get_ist_time() -> str:
    utc_time = datetime.now(timezone.utc).replace(tzinfo=None)
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return ist_time.strftime("%B %d, %Y at %I:%M %p IST")


def escape(text: str) -> str:
    return html_module.escape(str(text), quote=True)


def build_news_json(all_news: dict) -> str:
    """Serialize all_news into a JS-safe JSON object for client-side tab rendering."""
    categories_meta = {
        "markets":            "📊 MARKETS & EARNINGS",
        "macro_policy":       "💰 MACRO & POLICY",
        "banking_fx":         "🏦 BANKING & FX",
        "bonds_rates":        "📈 BONDS & RATES",
        "commodities_energy": "📦 COMMODITIES & ENERGY",
        "india":              "🇮🇳 INDIA MARKETS",
        "corporate":          "🏢 CORPORATE NEWS",
        "geopolitical":       "🌍 GEOPOLITICAL",
        "crypto":             "📉 CRYPTO & WEB3",
        "tech_ai":            "🤖 TECH & AI",
        "asia_china":         "🌏 ASIA & CHINA",
        "europe_uk":          "🇪🇺 EUROPE & UK",
        "esg_climate":        "🌱 ESG & CLIMATE",
        "latam":              "🌎 LATAM",
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


def generate_complete_html(all_news: dict, event_calendar=None, event_news=None, econ_data=None) -> str:
    current_time = get_ist_time()
    total_articles = sum(len(v) for v in all_news.values())
    news_json = build_news_json(all_news)
    event_calendar = event_calendar or []
    event_news = event_news or []
    econ_data = econ_data or {}
    event_cal_json = build_event_calendar_json(event_calendar)
    event_news_json = build_event_news_json(event_news)
    econ_json = build_econ_data_json(econ_data)

    # Count per category for sidebar
    cat_counts = {
        "markets":            len(all_news.get("markets", [])),
        "macro_policy":       len(all_news.get("macro_policy", [])),
        "banking_fx":         len(all_news.get("banking_fx", [])),
        "bonds_rates":        len(all_news.get("bonds_rates", [])),
        "commodities_energy": len(all_news.get("commodities_energy", [])),
        "india":              len(all_news.get("india", [])),
        "corporate":          len(all_news.get("corporate", [])),
        "geopolitical":       len(all_news.get("geopolitical", [])),
        "crypto":             len(all_news.get("crypto", [])),
        "tech_ai":            len(all_news.get("tech_ai", [])),
        "asia_china":         len(all_news.get("asia_china", [])),
        "europe_uk":          len(all_news.get("europe_uk", [])),
        "esg_climate":        len(all_news.get("esg_climate", [])),
        "latam":              len(all_news.get("latam", [])),
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NexusFeed – Global Market Intelligence v2</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600;700&family=IBM+Plex+Sans:wght@300;400;600&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
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
  font-size: 16px;
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
  font-size: 14px;
  letter-spacing: 2px;
  position: sticky;
  top: 0;
  z-index: 100;
}}
.topbar-left {{ display:flex; align-items:center; gap:16px; }}
.topbar-right {{ display:flex; gap: 22px; font-weight: 600; font-size: 13px; }}
.topbar-dot {{ width:8px; height:8px; border-radius:50%; background:#000; animation: blink 1.5s step-end infinite; }}
@keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.2}} }}

/* ── CLOCK BAR ── */
.clockbar {{
  background: #161616;
  border-bottom: 1px solid #2e2e2e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'IBM Plex Mono', monospace;
  padding: 8px 18px;
  position: sticky;
  top: 34px;
  z-index: 99;
}}
.clockbar-clocks {{
  display: flex;
  align-items: center;
  gap: 0;
}}
.clockbar-tz {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 32px;
  border-right: 1px solid #2e2e2e;
}}
.clockbar-tz:last-of-type {{ border-right: none; }}
.clockbar-tag {{
  color: var(--orange);
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 3px;
}}
.clockbar-val {{
  color: #f0f0f0;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
}}
.clockbar-dot {{
  color: var(--orange);
  font-size: 9px;
  animation: blink 1.5s step-end infinite;
}}
.clockbar-date {{
  position: absolute;
  right: 18px;
  color: #666;
  font-size: 11px;
  letter-spacing: 0.5px;
}}

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
  will-change: transform;
}}
.ticker-track:hover {{ animation-play-state: paused; }}
.ticker-item {{
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 26px;
  border-right: 1px solid var(--border);
  font-size: 14px;
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
  grid-template-columns: 280px 1fr;
  height: calc(100vh - 90px);
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
  font-size: 13px;
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
  font-size: 15px;
}}
.sb-item:hover {{ background: var(--orange-dim); border-left-color: rgba(255,106,0,0.4); }}
.sb-item.active {{ background: var(--orange-dim); border-left-color: var(--orange); }}
.sb-item .sb-name {{ color: var(--white); font-weight: 500; }}
.sb-item .sb-count {{
  color: #cccccc;
  font-size: 13px;
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
  font-size: 14px;
  border-bottom: 1px solid var(--border2);
}}
.sb-ind-row:last-child {{ border-bottom: none; }}
.sb-ind-name {{ color: #cccccc; font-weight: 400; }}
.sb-ind-val {{ font-weight: 700; font-size: 14px; }}
.sb-ind-val.pos {{ color: var(--green); }}
.sb-ind-val.neg {{ color: var(--red); }}
.sb-ind-val.neu {{ color: #aaaaaa; }}

/* ── COLLAPSIBLE ECON SECTIONS IN SIDEBAR ── */
.sb-econ-hdr {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 14px 8px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  user-select: none;
  transition: background 0.12s;
}}
.sb-econ-hdr:hover {{ background: rgba(255,106,0,0.06); }}
.sb-econ-title {{
  font-size: 13px; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; display: flex; align-items: center; gap: 6px;
}}
.sb-econ-title.usa  {{ color: #e05060; }}
.sb-econ-title.india {{ color: #ffaa44; }}
.sb-econ-arrow {{
  color: var(--orange); font-size: 11px;
  transition: transform 0.2s; flex-shrink: 0;
}}
.sb-econ-arrow.collapsed {{ transform: rotate(-90deg); }}

.sb-econ-body {{ overflow: hidden; transition: max-height 0.25s ease; }}
.sb-econ-body.collapsed {{ max-height: 0 !important; }}

.sb-econ-row {{
  padding: 6px 14px;
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  column-gap: 8px;
  row-gap: 1px;
  border-bottom: 1px solid var(--border2);
  align-items: center;
}}
.sb-econ-row:last-child {{ border-bottom: none; padding-bottom: 10px; }}

/* Label — top-left */
.sb-econ-key {{
  grid-column: 1; grid-row: 1;
  color: #c8d4e8;
  font-size: 11.5px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  font-weight: 700;
  white-space: normal;
  line-height: 1.3;
}}

/* Value — top-right, bold & coloured */
.sb-econ-val {{
  grid-column: 2; grid-row: 1;
  font-weight: 700;
  font-size: 14.5px;
  white-space: nowrap;
  text-align: right;
  font-family: 'IBM Plex Mono', monospace;
  letter-spacing: 0.3px;
}}
.sb-econ-val.pos {{ color: #00e868; }}
.sb-econ-val.neg {{ color: #ff4466; }}
.sb-econ-val.neu {{ color: #d0d0d0; }}

/* Note — bottom-right, light yellow */
.sb-econ-note {{
  grid-column: 2; grid-row: 2;
  color: #f0e070;
  font-size: 10.5px;
  white-space: normal;
  text-align: right;
  line-height: 1.3;
  font-style: italic;
  font-weight: 500;
}}

/* ── MAIN CONTENT ── */
.main {{ overflow-y: auto; display: flex; flex-direction: column; scrollbar-width: thin; scrollbar-color: var(--border) transparent; }}
.main::-webkit-scrollbar {{ width:4px; }}
.main::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:2px; }}

/* ── INDICATORS / ECON PANELS ── */
.ind-panel-hdr {{
  color: var(--orange);
  font-size: 13px;
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
  font-size: 13px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 5px;
  font-weight: 500;
}}
.ind-val {{
  color: var(--white);
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
  white-space: nowrap;
  letter-spacing: -0.5px;
}}
.ind-chg {{
  font-size: 13px;
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
  font-size: 13px;
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
  font-size: 13px;
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
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
}}
.news-hdr-meta {{ color: #aaaaaa; font-size: 13px; }}

/* ── NEWSPAPER COLUMN — COMPACT STYLE ── */
.news-col {{ border: 1px solid var(--border); border-radius: 3px; overflow: hidden; }}

.nc-item {{
  border-bottom: 1px solid #1e1e1e;
  cursor: pointer;
  transition: background 0.12s;
  user-select: none;
}}
.nc-item:last-of-type {{ border-bottom: none; }}
.nc-item:hover {{ background: rgba(255,106,0,0.04); }}
.nc-item.open {{ background: rgba(255,106,0,0.06); border-left: 2px solid var(--orange); }}

.nc-row {{
  display: grid;
  grid-template-columns: 36px 1fr 24px;
  align-items: center;
  padding: 13px 12px 13px 0;
  gap: 4px;
}}
.nc-num {{
  font-size: 14px; font-weight: 700;
  color: var(--orange); opacity: 0.55;
  font-family: 'IBM Plex Mono', monospace;
  text-align: right; padding-right: 4px;
}}
.nc-headline {{
  font-family: 'DM Sans', sans-serif;
  font-size: 20px; font-weight: 500;
  color: #e8e8e8; line-height: 1.55;
  letter-spacing: 0.1px;
}}
.nc-arrow {{
  color: #555; font-size: 12px;
  text-align: center; transition: transform 0.2s, color 0.15s;
}}
.nc-item:hover .nc-arrow {{ color: var(--orange); }}
.nc-item.open .nc-arrow {{ transform: rotate(180deg); color: var(--orange); }}

.nc-expand-body {{
  display: none;
  padding: 0 14px 12px 36px;
  border-top: 1px dashed #2a2a2a;
}}
.nc-expand-body.open {{ display: block; animation: fadeIn 0.18s ease; }}
@keyframes fadeIn {{ from {{ opacity:0; transform:translateY(-3px); }} to {{ opacity:1; transform:translateY(0); }} }}

.nc-meta {{
  display: flex; align-items: center; gap: 6px;
  padding: 8px 0 6px;
}}
.nc-src {{
  font-family: 'DM Sans', sans-serif;
  font-size: 14px; font-weight: 600; letter-spacing: 0.5px;
  padding: 2px 7px; border-radius: 3px;
  background: rgba(255,106,0,0.14); color: var(--orange);
  text-transform: uppercase;
}}
.nc-sep {{ color: #444; font-size: 14px; }}
.nc-time {{ font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: #666; }}
.nc-summary {{
  font-family: 'DM Sans', sans-serif;
  font-size: 17px; color: #aaaaaa;
  line-height: 1.7; margin-bottom: 8px;
}}
.nc-link {{
  display: inline-block;
  font-family: 'DM Sans', sans-serif;
  color: var(--orange); font-size: 15px; font-weight: 600;
  text-decoration: none; letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255,106,0,0.3);
  padding-bottom: 1px; transition: opacity 0.15s;
}}
.nc-link:hover {{ opacity: 0.7; }}

.no-news {{
  color: #777; font-size: 14px;
  padding: 20px 14px; font-family: 'DM Sans', sans-serif;
}}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}

/* ── LOADING OVERLAY ── */
.loading-overlay {{
  position: fixed; inset: 0;
  background: rgba(13,13,13,0.97);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  z-index: 500;
  opacity: 0; pointer-events: none;
  transition: opacity 0.3s;
}}
.loading-overlay.visible {{ opacity: 1; pointer-events: all; }}
.spinner {{
  width: 36px; height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--orange);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 14px;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
.loading-text {{
  color: var(--orange); font-size: 13px;
  letter-spacing: 2px; text-transform: uppercase;
  font-weight: 600;
}}

/* ── STATUS BAR ── */
.statusbar {{
  background: #161616;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 18px;
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.5px;
  position: sticky;
  bottom: 0;
  z-index: 98;
}}

/* ── HAMBURGER BUTTON ── */
.hamburger {{
  display: none;
  flex-direction: column; justify-content: center; gap: 4px;
  width: 32px; height: 32px; cursor: pointer;
  padding: 4px; border-radius: 3px;
  transition: background 0.15s; flex-shrink: 0;
}}
.hamburger:hover {{ background: rgba(0,0,0,0.2); }}
.hamburger span {{ display: block; width: 20px; height: 2px; background: #000; border-radius: 2px; }}

/* ── SIDEBAR OVERLAY (mobile) ── */
.sidebar-overlay {{
  display: none;
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7); z-index: 200;
}}
.sidebar-overlay.open {{ display: block; }}

/* ── RESPONSIVE — Tablet ── */
@media (max-width: 900px) {{
  .shell {{ grid-template-columns: 1fr; height: auto; }}
  .sidebar {{
    position: fixed; top: 0; left: -265px; bottom: 0;
    width: 265px; z-index: 300;
    transition: left 0.25s ease; padding-top: 50px;
  }}
  .sidebar.open {{ left: 0; }}
  .hamburger {{ display: flex; }}
  .topbar-right span:nth-child(3) {{ display: none; }}
  .ind-row {{ flex-wrap: wrap; }}
  .ind-cell {{ min-width: 110px; }}
  .news-area {{ padding: 12px 10px; }}
  .statusbar span:first-child {{ font-size: 9px; letter-spacing: 0; }}
}}

/* ── RESPONSIVE — Mobile ── */
@media (max-width: 600px) {{
  body {{ font-size: 13px; }}
  .topbar {{ padding: 5px 10px; }}
  .topbar-right {{ gap: 10px; font-size: 10px; }}
  .topbar-right span:nth-child(3), .topbar-right span:nth-child(4) {{ display: none; }}
  .ticker-item {{ padding: 0 14px; font-size: 11px; }}
  .cat-tabs {{ padding: 0 6px; }}
  .cat-tab {{ padding: 8px 10px; font-size: 12px; letter-spacing: 0.5px; }}
  .news-area {{ padding: 10px 8px; }}
  .news-hdr {{ margin-bottom: 10px; padding-bottom: 8px; }}
  .news-hdr-title {{ font-size: 10px; }}
  .news-hdr-meta {{ display: none; }}
  .nc-row {{ padding: 8px 8px 8px 0; }}
  .nc-headline {{ font-size: 15px; }}
  .nc-expand-body {{ padding: 0 8px 10px 30px; }}
  .statusbar {{ padding: 3px 8px; font-size: 9px; }}
  .statusbar span:first-child {{ display: none; }}
  .ind-cell {{ min-width: 90px; padding: 8px 10px; }}
  .ind-val {{ font-size: 17px; }}
}}

/* ── LIGHT MODE ── */
body.light {{
  --bg: #f0f1f4;
  --panel: #ffffff;
  --panel2: #f7f7f8;
  --border: #d0d4db;
  --border2: #e2e5ea;
  --muted: #666666;
  --muted2: #999999;
  --text: #1a1a1a;
  --white: #111111;
}}
body.light .topbar {{ background: #ff7a1a; }}
body.light .clockbar {{ background: #e8eaef; border-color: #d0d4db; }}
body.light .ticker {{ background: #e2e5ea; }}
body.light .statusbar {{ background: #e2e5ea; color: #444; }}
body.light .nc-headline {{ color: #111; }}
body.light .nc-summary {{ color: #555; }}
body.light .nc-expand-body {{ border-color: #d0d4db; }}
body.light .sb-econ-key {{ color: #555; }}
body.light .sb-ind-name {{ color: #555; }}
body.light .clockbar-val {{ color: #111; }}
body.light .cat-tab {{ color: #666; }}
body.light .cat-tab.active {{ color: var(--orange); }}
body.light .cat-tabs {{ background: #f0f1f4; }}
body.light .econ-section {{ background: #f5f5f7; }}
body.light .loading-overlay {{ background: rgba(240,241,244,0.97); }}
body.light .loading-text {{ color: #333; }}

/* ── THEME TOGGLE ── */
.theme-toggle {{
  cursor: pointer; font-size: 16px; padding: 2px 6px;
  border-radius: 4px; transition: background 0.15s;
  user-select: none;
}}
.theme-toggle:hover {{ background: rgba(0,0,0,0.15); }}

/* ── SEARCH BOX ── */
.news-search {{
  padding: 0 18px 10px;
  flex-shrink: 0;
}}
.news-search input {{
  width: 100%;
  background: var(--panel);
  border: 1px solid var(--border);
  color: var(--white);
  font-family: 'IBM Plex Mono', monospace;
  font-size: 13px;
  padding: 9px 14px 9px 36px;
  border-radius: 4px;
  outline: none;
  transition: border-color 0.15s;
}}
.news-search input::placeholder {{ color: var(--muted2); }}
.news-search input:focus {{ border-color: var(--orange); }}
.news-search-wrap {{
  position: relative;
}}
.news-search-icon {{
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  color: var(--muted2); font-size: 14px; pointer-events: none;
}}

/* ── SCROLL-TO-TOP BUTTON ── */
.scroll-top {{
  position: fixed; bottom: 40px; right: 20px;
  width: 40px; height: 40px;
  background: var(--orange);
  color: #000; font-weight: 700; font-size: 18px;
  border: none; border-radius: 50%;
  cursor: pointer; z-index: 90;
  display: none; align-items: center; justify-content: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.4);
  transition: opacity 0.2s, transform 0.2s;
}}
.scroll-top.visible {{ display: flex; }}
.scroll-top:hover {{ transform: scale(1.1); }}

/* ── TAB SCROLL FADE ── */
.cat-tabs-wrap {{
  position: relative; flex-shrink: 0;
}}
.cat-tabs-wrap::after {{
  content: ''; position: absolute;
  top: 0; right: 0; bottom: 0; width: 50px;
  background: linear-gradient(90deg, transparent, #101010);
  pointer-events: none; z-index: 1;
}}
body.light .cat-tabs-wrap::after {{
  background: linear-gradient(90deg, transparent, #f0f1f4);
}}

/* ── STALE DATA BADGE ── */
.stale-badge {{
  display: inline-block;
  background: rgba(0,200,80,0.12);
  color: #00c850;
  font-size: 9px; font-weight: 700;
  padding: 1px 4px; border-radius: 2px;
  letter-spacing: 0.5px;
  margin-left: 3px;
  text-transform: uppercase;
  vertical-align: middle;
}}

/* ── KEYBOARD FOCUS ── */
.sb-item:focus-visible, .nc-item:focus-visible, .cat-tab:focus-visible {{
  outline: 2px solid var(--orange);
  outline-offset: -2px;
}}

/* ══════════════════════════════════════
   KEY EVENT CALENDAR STYLES
   ══════════════════════════════════════ */
.event-calendar-panel {{
  display: none;
  padding: 0;
  flex-direction: column;
  height: 100%;
}}
.event-calendar-panel.active {{ display: flex; }}

.ecal-header {{
  padding: 16px 20px 10px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  flex-shrink: 0;
}}
.ecal-title {{ color: var(--orange); font-size: 16px; font-weight: 700; letter-spacing: 2px; }}
.ecal-subtitle {{ color: var(--muted); font-size: 12px; }}

.ecal-filters {{
  display: flex; gap: 6px; padding: 10px 20px;
  flex-wrap: wrap; flex-shrink: 0;
  border-bottom: 1px solid var(--border2);
}}
.ecal-filter-btn {{
  background: var(--panel2); border: 1px solid var(--border);
  color: var(--muted); font-family: 'IBM Plex Mono', monospace;
  font-size: 13px; padding: 6px 14px; border-radius: 3px;
  cursor: pointer; transition: all 0.15s; letter-spacing: 0.5px;
}}
.ecal-filter-btn:hover {{ border-color: var(--orange); color: var(--text); }}
.ecal-filter-btn.active {{ background: var(--orange-dim); border-color: var(--orange); color: var(--orange); font-weight: 600; }}

.ecal-body {{
  flex: 1; overflow-y: auto; padding: 12px 20px 20px;
}}
.ecal-month-group {{
  margin-bottom: 18px;
}}
.ecal-month-label {{
  color: var(--orange); font-size: 15px; font-weight: 700;
  letter-spacing: 2px; padding: 8px 0 10px;
  border-bottom: 1px solid var(--border2);
  margin-bottom: 6px;
  position: sticky; top: 0;
  background: var(--bg); z-index: 1;
}}
body.light .ecal-month-label {{ background: var(--bg); }}

.ecal-event {{
  display: grid;
  grid-template-columns: 105px 1fr auto;
  gap: 12px; align-items: center;
  padding: 11px 10px;
  border-bottom: 1px solid var(--border2);
  transition: background 0.12s;
  border-radius: 3px;
}}
.ecal-event:hover {{ background: rgba(255,106,0,0.05); }}

.ecal-date {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 14px; color: var(--muted); font-weight: 600;
  white-space: nowrap;
}}
.ecal-event-title {{
  font-family: 'DM Sans', sans-serif;
  font-size: 16px; color: var(--text); line-height: 1.4;
}}
.ecal-event-meta {{
  display: flex; align-items: center; gap: 8px; flex-shrink: 0;
}}
.ecal-impact {{
  font-size: 12px; font-weight: 700; letter-spacing: 0.5px;
  padding: 3px 9px; border-radius: 3px;
  white-space: nowrap;
}}
.ecal-impact.high {{ background: rgba(255,51,85,0.15); color: var(--red); }}
.ecal-impact.medium {{ background: rgba(255,215,0,0.15); color: var(--yellow); }}
.ecal-impact.low {{ background: rgba(0,255,85,0.1); color: var(--green); }}

.ecal-status {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px; font-weight: 700; letter-spacing: 0.5px;
  padding: 3px 9px; border-radius: 3px;
}}
.ecal-status.today {{ background: rgba(255,51,85,0.2); color: var(--red); animation: blink 1.5s step-end infinite; }}
.ecal-status.justpassed {{ background: rgba(180,100,255,0.18); color: #c084fc; border: 1px solid rgba(180,100,255,0.3); }}
.ecal-status.thisweek {{ background: rgba(255,106,0,0.2); color: var(--orange); }}
.ecal-status.upcoming {{ background: rgba(41,182,255,0.15); color: var(--blue); }}
.ecal-status.scheduled {{ background: rgba(255,255,255,0.05); color: var(--muted); }}

.ecal-region-badge {{
  font-size: 12px; font-weight: 600; padding: 2px 8px;
  border-radius: 2px; letter-spacing: 0.5px;
  background: rgba(255,255,255,0.06); color: var(--muted);
}}

.ecal-news-section {{
  margin-top: 24px; padding-top: 16px;
  border-top: 2px solid var(--orange-dim);
}}
.ecal-news-title {{
  color: var(--orange); font-size: 14px; font-weight: 700;
  letter-spacing: 2px; margin-bottom: 12px;
}}
.ecal-news-item {{
  padding: 8px 0; border-bottom: 1px solid var(--border2);
  cursor: pointer; transition: background 0.12s;
}}
.ecal-news-item:hover {{ background: rgba(255,106,0,0.04); }}
.ecal-news-headline {{
  font-family: 'DM Sans', sans-serif;
  font-size: 14px; color: var(--text); line-height: 1.4;
}}
.ecal-news-meta {{
  font-size: 11px; color: var(--muted); margin-top: 3px;
}}
.ecal-news-expand {{
  display: none; padding: 8px 0 4px 0;
}}
.ecal-news-item.open .ecal-news-expand {{ display: block; }}
.ecal-news-summary {{
  font-family: 'DM Sans', sans-serif;
  font-size: 13px; color: #aaa; line-height: 1.6;
  margin-bottom: 6px;
}}
.ecal-news-link {{
  color: var(--orange); font-size: 12px; font-weight: 600;
  text-decoration: none; border-bottom: 1px solid rgba(255,106,0,0.3);
}}

.ecal-count-badge {{
  display: inline-block; background: var(--orange);
  color: #000; font-size: 10px; font-weight: 700;
  padding: 1px 6px; border-radius: 8px; margin-left: 6px;
}}

@media (max-width: 600px) {{
  .ecal-event {{ grid-template-columns: 70px 1fr; gap: 6px; }}
  .ecal-event-meta {{ grid-column: 1 / -1; }}
  .ecal-filters {{ padding: 8px 10px; }}
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
    <div class="hamburger" onclick="toggleSidebar()" aria-label="Menu">
      <span></span><span></span><span></span>
    </div>
    <div class="topbar-dot"></div>
    <span>🌐 NEXUSFEED</span>
  </div>
  <div class="topbar-right">
    <span>🔴 LIVE FEED</span>
    <span>📅 {current_time}</span>
    <span>✅ {total_articles} ARTICLES</span>
    <span class="theme-toggle" onclick="toggleTheme()" title="Toggle light/dark mode">🌓</span>
  </div>
</div>

<!-- CLOCK BAR -->
<div class="clockbar">
  <div class="clockbar-clocks">
    <div class="clockbar-tz">
      <span class="clockbar-tag">CST</span>
      <span class="clockbar-val" id="clockCST">--:--:--</span>
      <span class="clockbar-dot">●</span>
    </div>
    <div class="clockbar-tz">
      <span class="clockbar-tag">IST</span>
      <span class="clockbar-val" id="clockIST">--:--:--</span>
      <span class="clockbar-dot">●</span>
    </div>
    <div class="clockbar-tz">
      <span class="clockbar-tag">SGT</span>
      <span class="clockbar-val" id="clockSGT">--:--:--</span>
      <span class="clockbar-dot">●</span>
    </div>
  </div>
  <div class="clockbar-date" id="clockbarDate">--</div>
</div>

<!-- TICKER STRIP -->
<div class="ticker">
  <div class="ticker-track" id="tickerTrack">
    <!-- populated by JS -->
  </div>
</div>

<!-- SIDEBAR OVERLAY (mobile) -->
<div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

<!-- MAIN SHELL -->
<div class="shell">

  <!-- ═══ SIDEBAR ═══ -->
  <div class="sidebar">

    <!-- 1. USA ECONOMIC (collapsible) ── -->
    <div class="sb-section">
      <div class="sb-econ-hdr" onclick="toggleEcon('usa')">
        <span class="sb-econ-title usa">🇺🇸 USA ECONOMIC</span>
        <span class="sb-econ-arrow" id="arrow-usa">▼</span>
      </div>
      <div class="sb-econ-body" id="body-usa">
        <div class="sb-econ-row">
          <span class="sb-econ-key">Fed Funds Rate</span>
          <span class="sb-econ-val neu" id="sbv-fedfunds">4.25–4.50%</span>
          <span class="sb-econ-note" id="sbn-fedfunds">Target range</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">FOMC Next</span>
          <span class="sb-econ-val neu" id="sbv-fomc">Apr 28–29</span>
          <span class="sb-econ-note" id="sbn-fomc">2026</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">CPI YoY</span>
          <span class="sb-econ-val neu" id="sbv-cpi">--</span>
          <span class="sb-econ-note" id="sbn-cpi">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">Core CPI</span>
          <span class="sb-econ-val neu" id="sbv-corecpi">--</span>
          <span class="sb-econ-note" id="sbn-corecpi">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">GDP Growth</span>
          <span class="sb-econ-val neu" id="sbv-gdp">--</span>
          <span class="sb-econ-note" id="sbn-gdp">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">Unemployment</span>
          <span class="sb-econ-val neu" id="sbv-unemployment">--</span>
          <span class="sb-econ-note" id="sbn-unemployment">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">NFP</span>
          <span class="sb-econ-val neu" id="sbv-nfp">--</span>
          <span class="sb-econ-note" id="sbn-nfp">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">PPI YoY</span>
          <span class="sb-econ-val neu" id="sbv-ppi">--</span>
          <span class="sb-econ-note" id="sbn-ppi">loading…</span>
        </div>
      </div>
    </div>

    <!-- 2. INDIA ECONOMIC (collapsible) ── -->
    <div class="sb-section">
      <div class="sb-econ-hdr" onclick="toggleEcon('india')">
        <span class="sb-econ-title india">🇮🇳 INDIA ECONOMIC</span>
        <span class="sb-econ-arrow" id="arrow-india">▼</span>
      </div>
      <div class="sb-econ-body" id="body-india">
        <div class="sb-econ-row">
          <span class="sb-econ-key">Repo Rate</span>
          <span class="sb-econ-val neu" id="sbv-reporate">--</span>
          <span class="sb-econ-note" id="sbn-reporate">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">CPI</span>
          <span class="sb-econ-val neu" id="sbv-india-cpi">--</span>
          <span class="sb-econ-note" id="sbn-india-cpi">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">WPI</span>
          <span class="sb-econ-val neu" id="sbv-india-wpi">--</span>
          <span class="sb-econ-note" id="sbn-india-wpi">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">Unemployment</span>
          <span class="sb-econ-val neu" id="sbv-india-unemp">--</span>
          <span class="sb-econ-note" id="sbn-india-unemp">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">Mfg PMI</span>
          <span class="sb-econ-val pos" id="sbv-india-pmi">--</span>
          <span class="sb-econ-note" id="sbn-india-pmi">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">GDP Growth</span>
          <span class="sb-econ-val pos" id="sbv-india-gdp">--</span>
          <span class="sb-econ-note" id="sbn-india-gdp">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">Fiscal Deficit</span>
          <span class="sb-econ-val neu" id="sbv-india-fiscal">--</span>
          <span class="sb-econ-note" id="sbn-india-fiscal">loading…</span>
        </div>
        <div class="sb-econ-row">
          <span class="sb-econ-key">USD/INR</span>
          <span class="sb-econ-val neu" id="sbv-usdinr2">₹--</span>
          <span class="sb-econ-note" id="sbn-usdinr2">live</span>
        </div>
      </div>
    </div>

    <!-- 3. LIVE PRICES ── -->
    <div class="sb-section">
      <div class="sb-label">▶ LIVE PRICES</div>
      <div class="sb-ind-row"><span class="sb-ind-name">S&amp;P 500</span>    <span class="sb-ind-val neu" id="sbv-sp500">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Dow Jones</span>   <span class="sb-ind-val neu" id="sbv-dow">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Nasdaq</span>      <span class="sb-ind-val neu" id="sbv-nasdaq">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">VIX</span>         <span class="sb-ind-val neu" id="sbv-vix">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">10Y Yield</span>   <span class="sb-ind-val neu" id="sbv-us10y">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">2Y Yield</span>    <span class="sb-ind-val neu" id="sbv-us2y">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Nifty 50</span>    <span class="sb-ind-val neu" id="sbv-nifty">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Sensex</span>      <span class="sb-ind-val neu" id="sbv-sensex">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">USD/INR</span>     <span class="sb-ind-val neu" id="sbv-usdinr">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Crude Oil</span>   <span class="sb-ind-val neu" id="sbv-oil">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Gold</span>        <span class="sb-ind-val neu" id="sbv-gold">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Silver</span>      <span class="sb-ind-val neu" id="sbv-silver">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">USD Index</span>   <span class="sb-ind-val neu" id="sbv-dollar">--</span></div>
    </div>

    <!-- 4. CATEGORIES ── -->
    <div class="sb-section">
      <div class="sb-label">▶ CATEGORIES</div>
      <div class="sb-item active" id="sb-markets"            onclick="switchCat('markets',this)" tabindex="0" role="button">
        <span class="sb-name">📊 Markets</span>
        <span class="sb-count">{cat_counts["markets"]}</span>
      </div>
      <div class="sb-item" id="sb-macro_policy"      onclick="switchCat('macro_policy',this)" tabindex="0" role="button">
        <span class="sb-name">💰 Macro & Policy</span>
        <span class="sb-count">{cat_counts["macro_policy"]}</span>
      </div>
      <div class="sb-item" id="sb-banking_fx"        onclick="switchCat('banking_fx',this)" tabindex="0" role="button">
        <span class="sb-name">🏦 Banking & FX</span>
        <span class="sb-count">{cat_counts["banking_fx"]}</span>
      </div>
      <div class="sb-item" id="sb-bonds_rates"       onclick="switchCat('bonds_rates',this)" tabindex="0" role="button">
        <span class="sb-name">📈 Bonds & Rates</span>
        <span class="sb-count">{cat_counts["bonds_rates"]}</span>
      </div>
      <div class="sb-item" id="sb-commodities_energy" onclick="switchCat('commodities_energy',this)" tabindex="0" role="button">
        <span class="sb-name">📦 Commodities & Energy</span>
        <span class="sb-count">{cat_counts["commodities_energy"]}</span>
      </div>
      <div class="sb-item" id="sb-india"             onclick="switchCat('india',this)" tabindex="0" role="button">
        <span class="sb-name">🇮🇳 India</span>
        <span class="sb-count">{cat_counts["india"]}</span>
      </div>
      <div class="sb-item" id="sb-corporate"         onclick="switchCat('corporate',this)" tabindex="0" role="button">
        <span class="sb-name">🏢 Corporate</span>
        <span class="sb-count">{cat_counts["corporate"]}</span>
      </div>
      <div class="sb-item" id="sb-geopolitical"      onclick="switchCat('geopolitical',this)" tabindex="0" role="button">
        <span class="sb-name">🌍 Geopolitical</span>
        <span class="sb-count">{cat_counts["geopolitical"]}</span>
      </div>
      <div class="sb-item" id="sb-crypto"            onclick="switchCat('crypto',this)" tabindex="0" role="button">
        <span class="sb-name">📉 Crypto & Web3</span>
        <span class="sb-count">{cat_counts["crypto"]}</span>
      </div>
      <div class="sb-item" id="sb-tech_ai"           onclick="switchCat('tech_ai',this)" tabindex="0" role="button">
        <span class="sb-name">🤖 Tech & AI</span>
        <span class="sb-count">{cat_counts["tech_ai"]}</span>
      </div>
      <div class="sb-item" id="sb-asia_china"        onclick="switchCat('asia_china',this)" tabindex="0" role="button">
        <span class="sb-name">🌏 Asia & China</span>
        <span class="sb-count">{cat_counts["asia_china"]}</span>
      </div>
      <div class="sb-item" id="sb-europe_uk"         onclick="switchCat('europe_uk',this)" tabindex="0" role="button">
        <span class="sb-name">🇪🇺 Europe & UK</span>
        <span class="sb-count">{cat_counts["europe_uk"]}</span>
      </div>
      <div class="sb-item" id="sb-esg_climate"       onclick="switchCat('esg_climate',this)" tabindex="0" role="button">
        <span class="sb-name">🌱 ESG & Climate</span>
        <span class="sb-count">{cat_counts["esg_climate"]}</span>
      </div>
      <div class="sb-item" id="sb-latam"             onclick="switchCat('latam',this)" tabindex="0" role="button">
        <span class="sb-name">🌎 LATAM</span>
        <span class="sb-count">{cat_counts["latam"]}</span>
      </div>
      <div class="sb-item" id="sb-event_calendar"    onclick="switchCat('event_calendar',this)" tabindex="0" role="button">
        <span class="sb-name">📅 Event Calendar</span>
        <span class="sb-count" id="ecal-sidebar-count">--</span>
      </div>
    </div>

    <!-- Sources ── -->
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
      <div class="sb-ind-row"><span class="sb-ind-name">CoinTelegraph</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">CoinDesk</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Reuters UK</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Reuters China</span></div>
    </div>

  </div><!-- /sidebar -->

  <!-- ═══ MAIN ═══ -->
  <div class="main">

    <!-- Hidden elements kept for JS ticker/sidebar updates (panel removed – prices shown in sidebar + ticker) -->
    <div style="display:none">
      <span id="card-gift-nifty"></span><span id="val-gift-nifty"></span><span id="chg-gift-nifty"></span>
      <span id="card-dow"></span><span id="val-dow"></span><span id="chg-dow"></span>
      <span id="card-sp500"></span><span id="val-sp500"></span><span id="chg-sp500"></span>
      <span id="card-nasdaq"></span><span id="val-nasdaq"></span><span id="chg-nasdaq"></span>
      <span id="card-vix"></span><span id="val-vix"></span><span id="chg-vix"></span>
      <span id="card-us10y"></span><span id="val-us10y"></span><span id="chg-us10y"></span>
      <span id="card-us2y"></span><span id="val-us2y"></span><span id="chg-us2y"></span>
      <span id="card-oil"></span><span id="val-oil"></span><span id="chg-oil"></span>
      <span id="card-dollar"></span><span id="val-dollar"></span><span id="chg-dollar"></span>
      <span id="card-gold"></span><span id="val-gold"></span><span id="chg-gold"></span>
      <span id="card-silver"></span><span id="val-silver"></span><span id="chg-silver"></span>
    </div>

    <!-- ── CATEGORY TABS ── -->
    <div class="cat-tabs-wrap">
    <div class="cat-tabs" id="catTabs">
      <div class="cat-tab active" id="tab-markets"           onclick="switchCat('markets',null)" tabindex="0" role="tab">📊 MARKETS</div>
      <div class="cat-tab"        id="tab-macro_policy"      onclick="switchCat('macro_policy',null)" tabindex="0" role="tab">💰 MACRO</div>
      <div class="cat-tab"        id="tab-banking_fx"        onclick="switchCat('banking_fx',null)" tabindex="0" role="tab">🏦 BANKING & FX</div>
      <div class="cat-tab"        id="tab-bonds_rates"       onclick="switchCat('bonds_rates',null)" tabindex="0" role="tab">📈 BONDS</div>
      <div class="cat-tab"        id="tab-commodities_energy" onclick="switchCat('commodities_energy',null)" tabindex="0" role="tab">📦 COMMODITIES</div>
      <div class="cat-tab"        id="tab-india"             onclick="switchCat('india',null)" tabindex="0" role="tab">🇮🇳 INDIA</div>
      <div class="cat-tab"        id="tab-corporate"         onclick="switchCat('corporate',null)" tabindex="0" role="tab">🏢 CORPORATE</div>
      <div class="cat-tab"        id="tab-geopolitical"      onclick="switchCat('geopolitical',null)" tabindex="0" role="tab">🌍 GEOPOLITICAL</div>
      <div class="cat-tab"        id="tab-crypto"            onclick="switchCat('crypto',null)" tabindex="0" role="tab">📉 CRYPTO</div>
      <div class="cat-tab"        id="tab-tech_ai"           onclick="switchCat('tech_ai',null)" tabindex="0" role="tab">🤖 TECH & AI</div>
      <div class="cat-tab"        id="tab-asia_china"        onclick="switchCat('asia_china',null)" tabindex="0" role="tab">🌏 ASIA & CHINA</div>
      <div class="cat-tab"        id="tab-europe_uk"         onclick="switchCat('europe_uk',null)" tabindex="0" role="tab">🇪🇺 EUROPE & UK</div>
      <div class="cat-tab"        id="tab-esg_climate"       onclick="switchCat('esg_climate',null)" tabindex="0" role="tab">🌱 ESG & CLIMATE</div>
      <div class="cat-tab"        id="tab-latam"             onclick="switchCat('latam',null)" tabindex="0" role="tab">🌎 LATAM</div>
      <div class="cat-tab"        id="tab-event_calendar"    onclick="switchCat('event_calendar',null)" tabindex="0" role="tab">📅 EVENT CALENDAR</div>
    </div>
    </div>

    <!-- ── SEARCH BOX ── -->
    <div class="news-search">
      <div class="news-search-wrap">
        <span class="news-search-icon">🔍</span>
        <input type="text" id="newsSearchInput" placeholder="Filter headlines…" oninput="filterNews()" />
      </div>
    </div>

    <!-- ── NEWS AREA ── -->
    <div class="news-area" id="newsPanel">
      <div class="news-hdr">
        <span class="news-hdr-title" id="newsTitle">▶ MARKET UPDATES</span>
        <span class="news-hdr-meta" id="newsSubtitle">Click headline to expand · {current_time}</span>
      </div>
      <div class="news-col" id="newsCol"></div>
    </div>

    <!-- ── EVENT CALENDAR PANEL ── -->
    <div class="event-calendar-panel" id="eventCalendarPanel">
      <div class="ecal-header">
        <div>
          <div class="ecal-title">📅 KEY EVENT CALENDAR</div>
          <div class="ecal-subtitle">Market-moving dates · Auto-generated {current_time}</div>
          <div class="ecal-subtitle" id="ecalSource" style="margin-top:2px;font-size:10px"></div>
        </div>
      </div>
      <div class="ecal-filters" id="ecalFilters">
        <button class="ecal-filter-btn active" onclick="filterEvents('all')">ALL</button>
        <button class="ecal-filter-btn" onclick="filterEvents('India')">🇮🇳 INDIA</button>
        <button class="ecal-filter-btn" onclick="filterEvents('USA')">🇺🇸 USA</button>
        <button class="ecal-filter-btn" onclick="filterEvents('Europe')">🇪🇺 EUROPE</button>
        <button class="ecal-filter-btn" onclick="filterEvents('Asia')">🌏 ASIA</button>
        <button class="ecal-filter-btn" onclick="filterEvents('Global')">🌍 GLOBAL</button>
        <button class="ecal-filter-btn" onclick="filterEvents('HIGH')">🔴 HIGH IMPACT</button>
      </div>
      <div class="ecal-body" id="ecalBody">
        <!-- Populated by JS -->
      </div>
    </div>

  </div><!-- /main -->
</div><!-- /shell -->

<!-- STATUS BAR -->
<div class="statusbar">
  <span>NEXUSFEED v2 · RSS FEEDS: 46 SOURCES · 14 CATEGORIES · AUTO-REFRESH: 5 MIN · NOT FINANCIAL ADVICE</span>
  <span id="statusClock">--:-- IST</span>
</div>

<!-- SCROLL-TO-TOP -->
<button class="scroll-top" id="scrollTopBtn" onclick="scrollToTop()" title="Back to top">↑</button>

<!-- ══════════════════════════════════════════
     SCRIPTS
══════════════════════════════════════════ -->
<script>
// ── All news injected by Python ──
const NEWS_DATA = {news_json};
const EVENT_CALENDAR = {event_cal_json};
const EVENT_NEWS = {event_news_json};
const ECON_DATA = {econ_json};

// ════════════════════════════
// HYDRATE SIDEBAR FROM SERVER-SIDE DATA
// (Python-fetched, always fresh, no CORS needed)
// ════════════════════════════
function hydrateEconData() {{
  const map = {{
    'us_fedfunds':     {{ val: 'sbv-fedfunds', note: 'sbn-fedfunds' }},
    'us_cpi':          {{ val: 'sbv-cpi', note: 'sbn-cpi' }},
    'us_core_cpi':     {{ val: 'sbv-corecpi', note: 'sbn-corecpi' }},
    'us_gdp':          {{ val: 'sbv-gdp', note: 'sbn-gdp' }},
    'us_unemployment': {{ val: 'sbv-unemployment', note: 'sbn-unemployment' }},
    'us_nfp':          {{ val: 'sbv-nfp', note: 'sbn-nfp' }},
    'us_ppi':          {{ val: 'sbv-ppi', note: 'sbn-ppi' }},
    'india_repo':      {{ val: 'sbv-reporate', note: 'sbn-reporate' }},
    'india_cpi':       {{ val: 'sbv-india-cpi', note: 'sbn-india-cpi' }},
    'india_wpi':       {{ val: 'sbv-india-wpi', note: 'sbn-india-wpi' }},
    'india_unemp':     {{ val: 'sbv-india-unemp', note: 'sbn-india-unemp' }},
    'india_pmi':       {{ val: 'sbv-india-pmi', note: 'sbn-india-pmi' }},
    'india_gdp':       {{ val: 'sbv-india-gdp', note: 'sbn-india-gdp' }},
    'india_fiscal':    {{ val: 'sbv-india-fiscal', note: 'sbn-india-fiscal' }},
  }};

  for (const [key, ids] of Object.entries(map)) {{
    const d = ECON_DATA[key];
    if (!d) continue;  // fetch failed server-side, leave for JS fallback
    const el = document.getElementById(ids.val);
    if (el) {{
      el.textContent = d.value;
      el.className = 'sb-econ-val ' + (d.css || 'neu');
    }}
    if (ids.note && d.note) {{
      const noteEl = document.getElementById(ids.note);
      if (noteEl) noteEl.innerHTML = d.note + ' <span class="stale-badge">server</span>';
    }}
  }}
}}

// ── Current active category ──
let currentCat = 'markets';
let eventFilter = 'all';

// ════════════════════════════
// EVENT CALENDAR RENDERING
// ════════════════════════════
function filterEvents(filter) {{
  eventFilter = filter;
  document.querySelectorAll('.ecal-filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  renderEventCalendar();
}}

function renderEventCalendar() {{
  const body = document.getElementById('ecalBody');
  let events = EVENT_CALENDAR;

  if (eventFilter === 'HIGH') {{
    events = events.filter(e => e.impact.includes('HIGH'));
  }} else if (eventFilter !== 'all') {{
    events = events.filter(e => e.region === eventFilter);
  }}

  // Group by month
  const months = {{}};
  events.forEach(e => {{
    const key = e.date.slice(0, 7); // YYYY-MM
    if (!months[key]) months[key] = [];
    months[key].push(e);
  }});

  let html = '';
  for (const [monthKey, items] of Object.entries(months)) {{
    const d = new Date(monthKey + '-01');
    const label = d.toLocaleDateString('en-US', {{ month: 'long', year: 'numeric' }});
    html += `<div class="ecal-month-group">
      <div class="ecal-month-label">${{label.toUpperCase()}} <span style="color:var(--muted);font-size:10px">(${{items.length}} events)</span></div>`;

    items.forEach(e => {{
      const dateParts = e.date.split('-');
      const dayDate = new Date(dateParts[0], dateParts[1]-1, dateParts[2]);
      const dayStr = dayDate.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric', weekday: 'short' }});

      const impactCls = e.impact.includes('HIGH') ? 'high' : e.impact.includes('MEDIUM') ? 'medium' : 'low';
      const statusCls = e.status === 'TODAY' ? 'today'
        : e.status === 'JUST PASSED' ? 'justpassed'
        : e.status === 'THIS WEEK' ? 'thisweek'
        : e.status === 'UPCOMING' ? 'upcoming' : 'scheduled';

      // Days ago label for JUST PASSED
      const daysAgo = e.days_away < 0 ? Math.abs(e.days_away) : 0;
      const statusLabel = e.status === 'JUST PASSED'
        ? `JUST PASSED · ${{daysAgo}}d ago`
        : e.status + (e.days_away > 0 ? ' · ' + e.days_away + 'd' : '');

      // Outcome result pill (shown when actual data exists or for JUST PASSED events)
      let outcomePill = '';
      if (e.actual) {{
        outcomePill = `<span style="background:rgba(0,200,100,0.15);color:#4ade80;border:1px solid rgba(0,200,100,0.3);font-size:11px;font-weight:700;padding:2px 8px;border-radius:3px;margin-left:8px;">✓ OUTCOME: ${{e.actual}}</span>`;
      }} else if (e.status === 'JUST PASSED') {{
        outcomePill = `<span style="background:rgba(180,100,255,0.12);color:#c084fc;border:1px solid rgba(180,100,255,0.25);font-size:11px;font-weight:600;padding:2px 8px;border-radius:3px;margin-left:8px;">⏳ Result pending</span>`;
      }}

      html += `<div class="ecal-event">
        <div class="ecal-date">${{dayStr}}</div>
        <div class="ecal-event-title">${{e.title}}
          <span class="ecal-region-badge">${{e.category}}</span>
          ${{e.country ? '<span class="ecal-region-badge">' + e.country + '</span>' : ''}}
          ${{outcomePill}}
          ${{e.forecast ? '<span style="color:var(--blue);font-size:11px;margin-left:6px">Fcst: ' + e.forecast + '</span>' : ''}}
          ${{e.previous ? '<span style="color:var(--muted);font-size:11px;margin-left:4px">Prev: ' + e.previous + '</span>' : ''}}
        </div>
        <div class="ecal-event-meta">
          <span class="ecal-impact ${{impactCls}}">${{e.impact}}</span>
          <span class="ecal-status ${{statusCls}}">${{statusLabel}}</span>
        </div>
      </div>`;
    }});
    html += '</div>';
  }}

  // Add related news
  if (EVENT_NEWS.length > 0) {{
    html += `<div class="ecal-news-section">
      <div class="ecal-news-title">▶ RELATED EVENT NEWS (${{EVENT_NEWS.length}} ARTICLES)</div>`;
    EVENT_NEWS.forEach((n, i) => {{
      const link = n.link && n.link !== '#' ? `<a class="ecal-news-link" href="${{n.link}}" target="_blank">Read ↗</a>` : '';
      html += `<div class="ecal-news-item" onclick="this.classList.toggle('open')">
        <div class="ecal-news-headline">${{n.title}}</div>
        <div class="ecal-news-meta">${{n.source}} · ${{n.time}}</div>
        <div class="ecal-news-expand">
          <div class="ecal-news-summary">${{n.summary}}</div>
          ${{link}}
        </div>
      </div>`;
    }});
    html += '</div>';
  }}

  if (!html) html = '<div class="no-news">No events match this filter.</div>';
  body.innerHTML = html;

  // Update sidebar count
  const countEl = document.getElementById('ecal-sidebar-count');
  if (countEl) countEl.textContent = EVENT_CALENDAR.length;

  // Show data source
  const srcEl = document.getElementById('ecalSource');
  if (srcEl) {{
    const isLive = EVENT_CALENDAR.length > 0 && EVENT_CALENDAR[0].country;
    srcEl.innerHTML = isLive
      ? '<span style="color:var(--green)">● LIVE</span> Trading Economics API'
      : '<span style="color:var(--yellow)">● FALLBACK</span> Computed Dates';
  }}
}}

// ════════════════════════════
// RENDER NEWS — NEWSPAPER COLUMN (Option B)
// ════════════════════════════
function renderNews(cat) {{
  const d = NEWS_DATA[cat];
  if (!d) return;
  const col = document.getElementById('newsCol');
  const items = d.items;
  const query = (document.getElementById('newsSearchInput')?.value || '').toLowerCase();

  // Filter items if search query present
  const filtered = query
    ? items.filter(item => item.title.toLowerCase().includes(query) || item.summary.toLowerCase().includes(query) || item.source.toLowerCase().includes(query))
    : items;

  if (!filtered || filtered.length === 0) {{
    col.innerHTML = '<div class="no-news">' + (query ? 'No articles match your filter.' : 'No articles available for this category.') + '</div>';
    document.getElementById('newsTitle').textContent = '▶ ' + d.label + ' — 0 ARTICLES';
    return;
  }}

  // Build HTML safely — titles/sources are already escaped by Python
  col.innerHTML = filtered.map((item, i) => {{
    const num = String(i + 1).padStart(2, '0');
    const link = item.link && item.link !== '#'
      ? `<a class="nc-link" href="${{item.link}}" target="_blank" rel="noopener">Read Full Article ↗</a>`
      : '';
    return `<div class="nc-item" onclick="toggleNC(this)" tabindex="0" role="button" aria-expanded="false" id="nc-${{cat}}-${{i}}">
  <div class="nc-row">
    <span class="nc-num">${{num}}</span>
    <span class="nc-headline">${{item.title}}</span>
    <span class="nc-arrow">▼</span>
  </div>
  <div class="nc-expand-body" id="nc-exp-${{cat}}-${{i}}">
    <div class="nc-meta">
      <span class="nc-src">${{item.source}}</span>
      <span class="nc-sep">·</span>
      <span class="nc-time">${{item.time}}</span>
    </div>
    <div class="nc-summary">${{item.summary}}</div>
    ${{link}}
  </div>
</div>`;
  }}).join('');

  document.getElementById('newsTitle').textContent = '▶ ' + d.label + ' — ' + filtered.length + (query ? '/' + items.length : '') + ' ARTICLES';
}}
function toggleNC(row) {{
  row.classList.toggle('open');
  const exp = row.querySelector('.nc-expand-body');
  if (exp) exp.classList.toggle('open');
  row.setAttribute('aria-expanded', row.classList.contains('open'));
}}

// ════════════════════════════
// SEARCH / FILTER NEWS
// ════════════════════════════
function filterNews() {{
  renderNews(currentCat);
}}

// ════════════════════════════
// THEME TOGGLE (DARK ↔ LIGHT)
// ════════════════════════════
function toggleTheme() {{
  document.body.classList.toggle('light');
  const isLight = document.body.classList.contains('light');
  localStorage.setItem('nf-theme', isLight ? 'light' : 'dark');
}}
// Restore theme from last visit
if (localStorage.getItem('nf-theme') === 'light') document.body.classList.add('light');

// ════════════════════════════
// SCROLL-TO-TOP
// ════════════════════════════
function scrollToTop() {{
  const mainEl = document.querySelector('.main');
  if (mainEl) mainEl.scrollTo({{ top: 0, behavior: 'smooth' }});
}}
(function() {{
  const mainEl = document.querySelector('.main');
  const btn = document.getElementById('scrollTopBtn');
  if (mainEl && btn) {{
    mainEl.addEventListener('scroll', () => {{
      btn.classList.toggle('visible', mainEl.scrollTop > 300);
    }});
  }}
}})();

// ════════════════════════════
// HAMBURGER / SIDEBAR DRAWER
// ════════════════════════════
function toggleSidebar() {{
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const isOpen  = sidebar.classList.contains('open');
  sidebar.classList.toggle('open', !isOpen);
  overlay.classList.toggle('open', !isOpen);
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

  // Toggle panels
  const newsPanel = document.getElementById('newsPanel');
  const ecalPanel = document.getElementById('eventCalendarPanel');
  const searchBox = document.querySelector('.news-search');
  if (cat === 'event_calendar') {{
    if (newsPanel) newsPanel.style.display = 'none';
    if (ecalPanel) ecalPanel.classList.add('active');
    if (searchBox) searchBox.style.display = 'none';
    renderEventCalendar();
  }} else {{
    if (newsPanel) newsPanel.style.display = '';
    if (ecalPanel) ecalPanel.classList.remove('active');
    if (searchBox) searchBox.style.display = '';
    renderNews(cat);
  }}
}}

// ════════════════════════════
// TOGGLE ECON SECTIONS IN SIDEBAR
// ════════════════════════════
function toggleEcon(id) {{
  const body  = document.getElementById('body-'  + id);
  const arrow = document.getElementById('arrow-' + id);
  if (!body) return;
  body.classList.toggle('collapsed');
  arrow.classList.toggle('collapsed');
  // Set explicit max-height for smooth animation
  if (!body.classList.contains('collapsed')) {{
    body.style.maxHeight = body.scrollHeight + 'px';
  }} else {{
    body.style.maxHeight = '0';
  }}
}}

// ════════════════════════════
// TICKER STRIP
// ════════════════════════════
const TICKER_SYMBOLS = [
  ['GIFT NIFTY', 'gift-nifty'],
  ['DOW',    'dow'],
  ['S&P 500','sp500'],
  ['NASDAQ', 'nasdaq'],
  ['VIX',    'vix'],
  ['10Y',    'us10y'],
  ['2Y',     'us2y'],
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
    <span class="ticker-item" data-key="${{key}}">
      <span class="t-sym">${{name}}</span>
      <span class="t-val t-neu" data-tv="${{key}}">--</span>
    </span>
  `).join('');
}}

function updateTicker(key, val, pct) {{
  const els = document.querySelectorAll('[data-tv="' + key + '"]');
  if (!els.length) return;
  const p = parseFloat(pct);
  const text = val + (pct ? ' (' + (p >= 0 ? '+' : '') + pct + '%)' : '');
  const cls = 't-val ' + (p > 0 ? 't-pos' : p < 0 ? 't-neg' : 't-neu');
  els.forEach(e => {{
    e.textContent = text;
    e.className = cls;
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
  'vix':    '^VIX',
  'us10y':  '^TNX',
  'us2y':   '^IRX',
  'oil':    'CL=F',
  'dollar': 'DX-Y.NYB',
  'gold':   'GC=F',
  'silver': 'SI=F',
  'usdinr': 'INR=X'
}};

// Multiple CORS proxies for resilience
const CORS_PROXIES = [
  (u) => 'https://corsproxy.io/?' + encodeURIComponent(u),
  (u) => 'https://api.allorigins.win/get?url=' + encodeURIComponent(u),
  (u) => 'https://api.codetabs.com/v1/proxy?quest=' + encodeURIComponent(u),
  (u) => 'https://thingproxy.freeboard.io/fetch/' + u,
  (u) => u  // direct (may work for some APIs)
];

async function fetchWithProxies(url, opts = {{}}) {{
  for (const mkProxy of CORS_PROXIES) {{
    try {{
      const proxied = mkProxy(url);
      const r = await fetch(proxied, {{ mode: 'cors', signal: AbortSignal.timeout(10000), ...opts }});
      if (!r.ok) continue;
      return r;
    }} catch(e) {{ /* try next */ }}
  }}
  throw new Error('All proxies failed for ' + url);
}}

async function fetchYahoo(key, sym) {{
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${{sym}}?interval=1d&range=1d`;
  for (const mkProxy of CORS_PROXIES) {{
    try {{
      const u = mkProxy(url);
      const r = await fetch(u, {{mode: 'cors', signal: AbortSignal.timeout(8000)}});
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
      let val;
      if (['dow', 'sp500', 'nasdaq'].includes(key)) {{
        val = cur.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
      }} else if (key === 'vix') {{
        val = cur.toFixed(2);
      }} else if (['us10y', 'us2y'].includes(key)) {{
        val = cur.toFixed(2) + '%';
      }} else if (key === 'dollar') {{
        val = cur.toFixed(2);
      }} else if (key === 'usdinr') {{
        val = '₹' + cur.toFixed(2);
      }} else {{
        val = '$' + cur.toFixed(2);
      }}
      updateCard(key, val, chg, pct);
      // Extra sidebar updates for usdinr
      if (key === 'usdinr') {{
        const sbEl = document.getElementById('sbv-usdinr');
        if (sbEl) {{ sbEl.textContent = '₹' + cur.toFixed(2); }}
        const sbEl2 = document.getElementById('sbv-usdinr2');
        if (sbEl2) {{ sbEl2.textContent = '₹' + cur.toFixed(2); }}
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
  try {{
    const r = await fetchWithProxies(csvUrl);
    let text = await r.text();
    try {{ const j = JSON.parse(text); if (j.contents) text = j.contents; }} catch(e) {{}}
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
    // Update sidebar CPI
    const sbCpi = document.getElementById('sbv-cpi');
    if (sbCpi) {{ sbCpi.textContent = yoy + '%'; sbCpi.className = 'sb-econ-val ' + (parseFloat(yoy) > 3 ? 'neg' : parseFloat(yoy) <= 2 ? 'pos' : 'neu'); }}
  }} catch (e) {{
    const vEl = document.getElementById('val-cpi');
    const cEl = document.getElementById('chg-cpi');
    if (vEl) vEl.textContent = '—';
    if (cEl) cEl.textContent = '—';
    const sbCpi = document.getElementById('sbv-cpi');
    if (sbCpi) sbCpi.textContent = '—';
  }}
}}

// ════════════════════════════
// FED FUNDS RATE via FRED CSV
// ════════════════════════════
// ════════════════════════════
// SHARED FRED CSV HELPER
// ════════════════════════════
// ════════════════════════════
// USA: CORE CPI (CPILFESL)
// ════════════════════════════
// ════════════════════════════
// USA: GDP GROWTH (A191RL1Q225SBEA)
// ════════════════════════════
// ════════════════════════════
// USA: UNEMPLOYMENT (UNRATE)
// ════════════════════════════
// ════════════════════════════
// USA: NFP (PAYEMS – MoM change)
// ════════════════════════════
// ════════════════════════════
// USA: PPI YoY (PPIFIS)
// ════════════════════════════
// ════════════════════════════
// INDIA: World Bank API helper
// ════════════════════════════
// ════════════════════════════
// INDIA: CPI (World Bank FP.CPI.TOTL.ZG)
// ════════════════════════════
// ════════════════════════════
// INDIA: GDP Growth (World Bank NY.GDP.MKTP.KD.ZG)
// ════════════════════════════
// ════════════════════════════
// INDIA: Unemployment (World Bank SL.UEM.TOTL.ZS)
// ════════════════════════════
// ════════════════════════════
// INDIA: Repo Rate — 2 reliable free sources (no API key)
// ════════════════════════════// ════════════════════════════
// INDIA: WPI via World Bank (FP.WPI.TOTL)
// ════════════════════════════
// ════════════════════════════
// INDIA: Mfg PMI — no free official API;
//   try a proxy to tradingeconomics data
// ════════════════════════════
// ════════════════════════════
// INDIA: Fiscal Deficit (World Bank GC.BAL.CASH.GD.ZS)
// ════════════════════════════
// ════════════════════════════
// CLOCK & REFRESH
// ════════════════════════════
function updateClock() {{
  const now = new Date();
  const fmtSec = (tz) => now.toLocaleString('en-US', {{hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true, timeZone: tz}});
  const fmtMin = (tz) => now.toLocaleString('en-US', {{hour: '2-digit', minute: '2-digit', hour12: true, timeZone: tz}});

  const cst = fmtSec('America/Chicago');
  const ist = fmtSec('Asia/Kolkata');
  const sgt = fmtSec('Asia/Singapore');

  const elCST = document.getElementById('clockCST');
  const elIST = document.getElementById('clockIST');
  const elSGT = document.getElementById('clockSGT');
  const elDate = document.getElementById('clockbarDate');

  if (elCST) elCST.textContent = cst;
  if (elIST) elIST.textContent = ist;
  if (elSGT) elSGT.textContent = sgt;
  if (elDate) {{
    elDate.textContent = '📅 ' + now.toLocaleDateString('en-US', {{weekday:'short', month:'short', day:'numeric', year:'numeric', timeZone:'Asia/Kolkata'}});
  }}

  const st = document.getElementById('statusClock');
  if (st) st.textContent = fmtSec('Asia/Kolkata') + ' IST';
  const ref = document.getElementById('newsSubtitle');
  if (ref) {{
    ref.textContent = 'Click any headline to expand · Last refresh: ' + fmtMin('Asia/Kolkata') + ' IST';
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
// KEYBOARD NAVIGATION
// ════════════════════════════
document.addEventListener('keydown', (e) => {{
  if (e.target.classList.contains('sb-item') && (e.key === 'Enter' || e.key === ' ')) {{
    e.preventDefault();
    e.target.click();
  }}
  if (e.target.classList.contains('nc-item') && (e.key === 'Enter' || e.key === ' ')) {{
    e.preventDefault();
    toggleNC(e.target);
  }}
  if (e.target.classList.contains('cat-tab') && (e.key === 'Enter' || e.key === ' ')) {{
    e.preventDefault();
    e.target.click();
  }}
}});

// ════════════════════════════
// INIT
// ════════════════════════════
window.addEventListener('DOMContentLoaded', () => {{
  buildTicker();
  renderNews('markets');
  // Set event calendar sidebar count
  const ecalCount = document.getElementById('ecal-sidebar-count');
  if (ecalCount) ecalCount.textContent = EVENT_CALENDAR.length;

  // Hydrate sidebar with server-fetched data (instant, no CORS)
  hydrateEconData();

  // Set initial max-height for smooth collapse animation
  ['usa', 'india'].forEach(id => {{
    const body = document.getElementById('body-' + id);
    if (body) body.style.maxHeight = body.scrollHeight + 'px';
  }});

  if (!sessionStorage.getItem('visited')) {{
    document.getElementById('loadingOverlay').classList.add('visible');
    sessionStorage.setItem('visited', '1');
  }}

  loadAll();
  fetchCPI();
  // USA economic indicators (FRED)
  // India economic indicators (World Bank + RBI)
  setInterval(loadAll, 5 * 60 * 1000);
  setInterval(updateClock, 1000);

  // Scroll-to-top observer
  const mainEl = document.querySelector('.main');
  const btn = document.getElementById('scrollTopBtn');
  if (mainEl && btn) {{
    mainEl.addEventListener('scroll', () => {{
      btn.classList.toggle('visible', mainEl.scrollTop > 300);
    }});
  }}
}});
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    logging.info("")
    logging.info("=" * 70)
    logging.info("GLOBAL MARKET DASHBOARD v2 – BLOOMBERG TERMINAL THEME")
    logging.info("  14 CATEGORIES · 46+ RSS SOURCES")
    logging.info("=" * 70)

    all_news = {}
    for category, urls in RSS_SOURCES.items():
        logging.info(f"Fetching [{category.upper()}] news …")
        items = fetch_category_news(category, urls)
        all_news[category] = items
        logging.info(f"  {len(items)} articles collected")

    total = sum(len(v) for v in all_news.values())
    logging.info(f"Total articles fetched: {total}")

    logging.info("Fetching Key Event Calendar (Trading Economics API) …")
    event_calendar = fetch_live_economic_calendar()
    logging.info(f"  {len(event_calendar)} events loaded ({'LIVE' if event_calendar and event_calendar[0].get('country') else 'FALLBACK'})")

    logging.info("Fetching event-related news …")
    event_news = fetch_event_news()
    logging.info(f"  {len(event_news)} event news articles")

    logging.info("Fetching economic indicators (server-side) …")
    econ_data = fetch_all_economic_data()
    fetched = sum(1 for v in econ_data.values() if v is not None)
    logging.info(f"  {fetched}/{len(econ_data)} indicators fetched successfully")

    logging.info("Generating index.html …")
    html = generate_complete_html(all_news, event_calendar, event_news, econ_data)

    output = "index.html"
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    logging.info("=" * 70)
    logging.info(f"SUCCESS! Dashboard written to: {output}")
    logging.info("=" * 70)
    logging.info("Every time you run this script the news refreshes automatically.")
    logging.info("Click any headline in the browser to expand and read the summary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
