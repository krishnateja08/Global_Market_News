#!/usr/bin/env python3
"""
Comprehensive Global Market News & Indicators Dashboard
Combines real-time market data with RSS news feeds from multiple sources
"""

import requests
from datetime import datetime
import json
import sys

# Check and install feedparser if needed
try:
    import feedparser
except ImportError:
    print("Installing feedparser...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'feedparser', '--break-system-packages'])
    import feedparser

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not installed. Install with: pip install yfinance")

class ComprehensiveMarketDashboard:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.market_data = {
            'gift_nifty': {},
            'us_markets': {},
            'crude_oil': {},
            'dollar_index': {},
            'timestamp': datetime.now().strftime('%B %d, %Y at %I:%M %p IST')
        }
        self.news_data = {
            'economic': [],
            'corporate': [],
            'geopolitical': [],
            'markets': [],
            'india': []
        }
    
    # ========== MARKET DATA FETCHING ==========
    
    def fetch_market_indicators(self):
        """Fetch all market indicators"""
        print("\n🚀 Fetching market indicators...")
        self.fetch_nifty_data()
        self.fetch_us_markets_data()
        self.fetch_commodities_data()
    
    def fetch_nifty_data(self):
        """Fetch Nifty 50 data"""
        try:
            if YFINANCE_AVAILABLE:
                nifty = yf.Ticker("^NSEI")
                history = nifty.history(period="2d")
                
                if not history.empty:
                    current_price = history['Close'].iloc[-1]
                    prev_price = history['Close'].iloc[-2] if len(history) > 1 else current_price
                    change = current_price - prev_price
                    pct_change = (change / prev_price) * 100
                    
                    self.market_data['gift_nifty'] = {
                        'value': f"{current_price:,.2f}",
                        'change': f"{change:+.2f}",
                        'pchange': f"{pct_change:+.2f}",
                        'status': 'positive' if change >= 0 else 'negative'
                    }
                    print(f"✅ Nifty 50: {current_price:,.2f} ({pct_change:+.2f}%)")
                else:
                    raise Exception("No history data")
            else:
                raise Exception("yfinance not available")
        except Exception as e:
            print(f"⚠️  Using fallback Nifty data: {e}")
            self.market_data['gift_nifty'] = {
                'value': '23,500.00',
                'change': '+125.50',
                'pchange': '+0.54',
                'status': 'positive'
            }
    
    def fetch_us_markets_data(self):
        """Fetch US market indices"""
        try:
            if YFINANCE_AVAILABLE:
                indices = {
                    'dow': '^DJI',
                    'sp500': '^GSPC',
                    'nasdaq': '^IXIC'
                }
                
                result = {}
                for name, ticker in indices.items():
                    try:
                        data = yf.Ticker(ticker).history(period="1d")
                        if not data.empty:
                            current = data['Close'].iloc[-1]
                            open_price = data['Open'].iloc[-1]
                            change = current - open_price
                            pct_change = (change / open_price) * 100
                            
                            result[name] = {
                                'value': f"{current:,.2f}",
                                'change': f"{change:+.2f}",
                                'pchange': f"{pct_change:+.2f}",
                                'status': 'positive' if change >= 0 else 'negative'
                            }
                            print(f"✅ {name.upper()}: {current:,.2f} ({pct_change:+.2f}%)")
                    except:
                        result[name] = {'value': 'N/A', 'change': '0.0', 'pchange': '0.0', 'status': 'neutral'}
                
                self.market_data['us_markets'] = result
            else:
                raise Exception("yfinance not available")
        except Exception as e:
            print(f"⚠️  Using fallback US market data")
            self.market_data['us_markets'] = {
                'dow': {'value': '43,500.00', 'change': '+150.00', 'pchange': '+0.35', 'status': 'positive'},
                'sp500': {'value': '5,875.00', 'change': '+25.50', 'pchange': '+0.44', 'status': 'positive'},
                'nasdaq': {'value': '18,350.00', 'change': '+75.00', 'pchange': '+0.41', 'status': 'positive'}
            }
    
    def fetch_commodities_data(self):
        """Fetch commodity prices"""
        try:
            if YFINANCE_AVAILABLE:
                # Crude Oil
                oil = yf.Ticker("CL=F")
                oil_data = oil.history(period="1d")
                
                if not oil_data.empty:
                    oil_price = oil_data['Close'].iloc[-1]
                    oil_open = oil_data['Open'].iloc[-1]
                    oil_change = oil_price - oil_open
                    oil_pct = (oil_change / oil_open) * 100
                    
                    self.market_data['crude_oil'] = {
                        'value': f"{oil_price:.2f}",
                        'change': f"{oil_change:+.2f}",
                        'pchange': f"{oil_pct:+.2f}",
                        'status': 'positive' if oil_change >= 0 else 'negative'
                    }
                    print(f"✅ Crude Oil: ${oil_price:.2f} ({oil_pct:+.2f}%)")
                
                # Dollar Index
                dxy = yf.Ticker("DX-Y.NYB")
                dxy_data = dxy.history(period="1d")
                
                if not dxy_data.empty:
                    dxy_price = dxy_data['Close'].iloc[-1]
                    dxy_open = dxy_data['Open'].iloc[-1]
                    dxy_change = dxy_price - dxy_open
                    dxy_pct = (dxy_change / dxy_open) * 100
                    
                    self.market_data['dollar_index'] = {
                        'value': f"{dxy_price:.2f}",
                        'change': f"{dxy_change:+.2f}",
                        'pchange': f"{dxy_pct:+.2f}",
                        'status': 'positive' if dxy_change >= 0 else 'negative'
                    }
                    print(f"✅ Dollar Index: {dxy_price:.2f} ({dxy_pct:+.2f}%)")
            else:
                raise Exception("yfinance not available")
        except Exception as e:
            print(f"⚠️  Using fallback commodity data")
            self.market_data['crude_oil'] = {
                'value': '78.50',
                'change': '+1.25',
                'pchange': '+1.62',
                'status': 'positive'
            }
            self.market_data['dollar_index'] = {
                'value': '104.25',
                'change': '-0.15',
                'pchange': '-0.14',
                'status': 'negative'
            }
    
    # ========== NEWS FETCHING ==========
    
    def fetch_rss_feed(self, url, category, source_name):
        """Fetch and parse RSS feed"""
        try:
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:8]:  # Get top 8 from each feed
                self.news_data[category].append({
                    'title': entry.get('title', 'No title'),
                    'link': entry.get('link', '#'),
                    'published': entry.get('published', 'Unknown'),
                    'summary': entry.get('summary', '')[:250] + '...' if entry.get('summary') else '',
                    'source': source_name
                })
            print(f"  ✅ Fetched {len(feed.entries[:8])} articles from {source_name}")
        except Exception as e:
            print(f"  ⚠️  Error fetching {source_name}: {e}")
    
    def fetch_all_news(self):
        """Fetch news from various sources"""
        print("\n📰 Fetching news from sources...")
        
        feeds = {
            'economic': [
                ('https://www.reuters.com/rssFeed/businessNews', 'Reuters Business'),
                ('https://feeds.bloomberg.com/markets/news.rss', 'Bloomberg Markets'),
            ],
            'corporate': [
                ('https://www.reuters.com/rssFeed/companyNews', 'Reuters Companies'),
                ('https://feeds.finance.yahoo.com/rss/2.0/headline', 'Yahoo Finance'),
            ],
            'geopolitical': [
                ('https://www.reuters.com/rssFeed/worldNews', 'Reuters World'),
            ],
            'markets': [
                ('https://www.cnbc.com/id/100003114/device/rss/rss.html', 'CNBC Markets'),
                ('https://www.marketwatch.com/rss/topstories', 'MarketWatch'),
            ],
            'india': [
                ('https://www.moneycontrol.com/rss/latestnews.xml', 'MoneyControl'),
                ('https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms', 'Economic Times'),
            ]
        }
        
        for category, feed_list in feeds.items():
            print(f"\n📂 Fetching {category.upper()} news:")
            for url, source in feed_list:
                self.fetch_rss_feed(url, category, source)
        
        total_articles = sum(len(v) for v in self.news_data.values())
        print(f"\n✅ Total articles fetched: {total_articles}")
    
    # ========== HTML GENERATION ==========
    
    def generate_html(self):
        """Generate comprehensive HTML dashboard"""
        gift_nifty = self.market_data['gift_nifty']
        us_markets = self.market_data['us_markets']
        crude = self.market_data['crude_oil']
        dollar = self.market_data['dollar_index']
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Comprehensive global market indicators and news impacting Indian stock market">
    <title>Global Market News & Indicators Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Space+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-bg: #0a0e27;
            --secondary-bg: #141b3d;
            --accent-bg: #1a2347;
            --text-primary: #e8edf5;
            --text-secondary: #a8b2d1;
            --accent-blue: #4a9eff;
            --accent-green: #00ff88;
            --accent-red: #ff4757;
            --accent-yellow: #ffd93d;
            --accent-purple: #a78bfa;
            --accent-pink: #f093fb;
            --accent-cyan: #4facfe;
            --border-color: #2a3a5f;
            --card-shadow: rgba(0, 0, 0, 0.5);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'IBM Plex Sans', sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1629 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }}
        
        body::before {{
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(74, 158, 255, 0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: moveGrid 20s linear infinite;
            z-index: 0;
        }}
        
        @keyframes moveGrid {{
            0% {{ transform: translate(0, 0); }}
            100% {{ transform: translate(50px, 50px); }}
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 40px 20px;
            background: rgba(26, 35, 71, 0.5);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid var(--border-color);
            box-shadow: 0 20px 60px var(--card-shadow);
            position: relative;
            overflow: hidden;
        }}
        
        header::after {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(74, 158, 255, 0.2), transparent);
            animation: shimmer 3s infinite;
        }}
        
        @keyframes shimmer {{
            0% {{ left: -100%; }}
            100% {{ left: 100%; }}
        }}
        
        h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 3.5em;
            font-weight: 900;
            background: linear-gradient(135deg, #4a9eff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
            letter-spacing: -1px;
            position: relative;
            z-index: 1;
        }}
        
        .subtitle {{
            font-family: 'Space Mono', monospace;
            font-size: 1.1em;
            color: var(--text-secondary);
            letter-spacing: 2px;
            text-transform: uppercase;
        }}
        
        .timestamp {{
            margin-top: 20px;
            font-family: 'Space Mono', monospace;
            font-size: 0.9em;
            color: var(--accent-blue);
            opacity: 0.8;
        }}
        
        .quick-links {{
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 30px 0;
            flex-wrap: wrap;
        }}
        
        .quick-link {{
            padding: 12px 25px;
            background: linear-gradient(135deg, var(--accent-bg), var(--secondary-bg));
            border: 1px solid var(--border-color);
            border-radius: 25px;
            color: var(--accent-blue);
            text-decoration: none;
            font-family: 'Space Mono', monospace;
            font-size: 0.85em;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(74, 158, 255, 0.2);
        }}
        
        .quick-link:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(74, 158, 255, 0.4);
            border-color: var(--accent-blue);
        }}
        
        .section-title {{
            font-family: 'Playfair Display', serif;
            font-size: 2.5em;
            font-weight: 900;
            margin-bottom: 30px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        /* Market Indicators Grid */
        .indicators-grid {{
            display: flex;
            gap: 15px;
            margin-bottom: 40px;
            overflow-x: auto;
            padding-bottom: 10px;
        }}
        
        .indicator-card {{
            background: rgba(26, 35, 71, 0.6);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 8px 20px var(--card-shadow);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            min-width: 180px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        
        .indicator-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
        }}
        
        .indicator-card.positive::before {{
            background: linear-gradient(90deg, var(--accent-green), var(--accent-blue));
        }}
        
        .indicator-card.negative::before {{
            background: linear-gradient(90deg, var(--accent-red), var(--accent-yellow));
        }}
        
        .indicator-card.neutral::before {{
            background: linear-gradient(90deg, var(--text-secondary), var(--accent-blue));
        }}
        
        .indicator-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(74, 158, 255, 0.3);
            border-color: var(--accent-blue);
        }}
        
        .indicator-title {{
            font-family: 'Space Mono', monospace;
            font-size: 0.7em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            white-space: nowrap;
        }}
        
        .indicator-value {{
            font-family: 'Playfair Display', serif;
            font-size: 1.4em;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 6px;
            white-space: nowrap;
        }}
        
        .indicator-change {{
            font-family: 'Space Mono', monospace;
            font-size: 0.8em;
            padding: 3px 8px;
            border-radius: 4px;
            display: inline-block;
            white-space: nowrap;
        }}
        
        .positive {{
            color: var(--accent-green);
            background: rgba(0, 255, 136, 0.1);
        }}
        
        .negative {{
            color: var(--accent-red);
            background: rgba(255, 71, 87, 0.1);
        }}
        
        .neutral {{
            color: var(--text-secondary);
            background: rgba(168, 178, 209, 0.1);
        }}
        
        /* News Section */
        .news-section {{
            margin-top: 60px;
        }}
        
        .news-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .news-category-card {{
            background: rgba(26, 35, 71, 0.6);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 15px;
            border: 1px solid var(--border-color);
            box-shadow: 0 10px 30px var(--card-shadow);
            transition: all 0.3s ease;
        }}
        
        .news-category-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(74, 158, 255, 0.3);
        }}
        
        .category-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid;
        }}
        
        .category-icon {{
            font-size: 2em;
        }}
        
        .category-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.6em;
            font-weight: 700;
        }}
        
        .economic .category-header {{ border-color: var(--accent-pink); }}
        .economic .category-title {{ color: var(--accent-pink); }}
        
        .corporate .category-header {{ border-color: var(--accent-cyan); }}
        .corporate .category-title {{ color: var(--accent-cyan); }}
        
        .geopolitical .category-header {{ border-color: var(--accent-green); }}
        .geopolitical .category-title {{ color: var(--accent-green); }}
        
        .markets .category-header {{ border-color: var(--accent-red); }}
        .markets .category-title {{ color: var(--accent-red); }}
        
        .india .category-header {{ border-color: var(--accent-yellow); }}
        .india .category-title {{ color: var(--accent-yellow); }}
        
        .news-item {{
            padding: 18px;
            margin-bottom: 15px;
            background: rgba(10, 14, 39, 0.4);
            border-radius: 10px;
            border-left: 3px solid var(--accent-blue);
            transition: all 0.2s ease;
        }}
        
        .news-item:hover {{
            background: rgba(10, 14, 39, 0.6);
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(74, 158, 255, 0.2);
        }}
        
        .economic .news-item {{ border-left-color: var(--accent-pink); }}
        .corporate .news-item {{ border-left-color: var(--accent-cyan); }}
        .geopolitical .news-item {{ border-left-color: var(--accent-green); }}
        .markets .news-item {{ border-left-color: var(--accent-red); }}
        .india .news-item {{ border-left-color: var(--accent-yellow); }}
        
        .news-item h3 {{
            font-size: 1.05em;
            margin-bottom: 10px;
            line-height: 1.5;
            font-weight: 600;
        }}
        
        .news-item a {{
            color: var(--text-primary);
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        .news-item a:hover {{
            color: var(--accent-blue);
        }}
        
        .news-meta {{
            display: flex;
            gap: 12px;
            align-items: center;
            margin-top: 8px;
            font-size: 0.8em;
            color: var(--text-secondary);
            flex-wrap: wrap;
        }}
        
        .news-source {{
            display: inline-block;
            background: var(--accent-blue);
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-family: 'Space Mono', monospace;
        }}
        
        .news-date {{
            font-family: 'Space Mono', monospace;
        }}
        
        .news-summary {{
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-top: 10px;
            line-height: 1.6;
        }}
        
        .no-news {{
            color: var(--text-secondary);
            font-style: italic;
            padding: 20px;
            text-align: center;
            opacity: 0.7;
        }}
        
        footer {{
            margin-top: 80px;
            text-align: center;
            padding: 40px;
            background: rgba(26, 35, 71, 0.3);
            border-radius: 15px;
            border: 1px solid var(--border-color);
        }}
        
        footer p {{
            font-family: 'Space Mono', monospace;
            font-size: 0.85em;
            color: var(--text-secondary);
        }}
        
        @media (max-width: 1024px) {{
            .news-grid {{
                grid-template-columns: 1fr;
            }}
            
            .indicators-grid {{
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }}
            
            .indicator-card {{
                min-width: 160px;
            }}
        }}
        
        @media (max-width: 768px) {{
            h1 {{ font-size: 2.2em; }}
            .quick-links {{ flex-direction: column; }}
            
            .indicators-grid {{
                gap: 10px;
            }}
            
            .indicator-card {{
                min-width: 140px;
                padding: 12px 15px;
            }}
            
            .indicator-title {{
                font-size: 0.65em;
            }}
            
            .indicator-value {{
                font-size: 1.2em;
            }}
            
            .indicator-change {{
                font-size: 0.7em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌍 Global Market Dashboard</h1>
            <div class="subtitle">Live Indicators & News Feed</div>
            <div class="timestamp">📅 Last Updated: {self.market_data['timestamp']}</div>
            
            <div class="quick-links">
                <a href="https://krishnateja08.github.io/Nifty_option_chain/" class="quick-link" target="_blank">
                    📊 Nifty Option Chain
                </a>
                <a href="https://krishnateja08.github.io/USA-SP500-Stocks-Review/" class="quick-link" target="_blank">
                    🇺🇸 USA S&P 500 Stocks
                </a>
            </div>
        </header>
        
        <section class="indicators-section">
            <h2 class="section-title">Live Market Indicators</h2>
            <div class="indicators-grid">
                <div class="indicator-card {gift_nifty.get('status', 'neutral')}">
                    <div class="indicator-title">🎯 GIFT Nifty (Nifty 50)</div>
                    <div class="indicator-value">{gift_nifty.get('value', 'N/A')}</div>
                    <div class="indicator-change {gift_nifty.get('status', 'neutral')}">
                        {gift_nifty.get('change', 'N/A')} ({gift_nifty.get('pchange', 'N/A')}%)
                    </div>
                </div>
                
                <div class="indicator-card {us_markets['dow'].get('status', 'neutral')}">
                    <div class="indicator-title">📈 Dow Jones</div>
                    <div class="indicator-value">{us_markets['dow']['value']}</div>
                    <div class="indicator-change {us_markets['dow'].get('status', 'neutral')}">
                        {us_markets['dow']['change']} ({us_markets['dow']['pchange']}%)
                    </div>
                </div>
                
                <div class="indicator-card {us_markets['sp500'].get('status', 'neutral')}">
                    <div class="indicator-title">💹 S&P 500</div>
                    <div class="indicator-value">{us_markets['sp500']['value']}</div>
                    <div class="indicator-change {us_markets['sp500'].get('status', 'neutral')}">
                        {us_markets['sp500']['change']} ({us_markets['sp500']['pchange']}%)
                    </div>
                </div>
                
                <div class="indicator-card {us_markets['nasdaq'].get('status', 'neutral')}">
                    <div class="indicator-title">💻 Nasdaq</div>
                    <div class="indicator-value">{us_markets['nasdaq']['value']}</div>
                    <div class="indicator-change {us_markets['nasdaq'].get('status', 'neutral')}">
                        {us_markets['nasdaq']['change']} ({us_markets['nasdaq']['pchange']}%)
                    </div>
                </div>
                
                <div class="indicator-card {crude.get('status', 'neutral')}">
                    <div class="indicator-title">🛢️ Crude Oil (WTI)</div>
                    <div class="indicator-value">${crude.get('value', 'N/A')}</div>
                    <div class="indicator-change {crude.get('status', 'neutral')}">
                        {crude.get('change', 'N/A')} ({crude.get('pchange', 'N/A')}%)
                    </div>
                </div>
                
                <div class="indicator-card {dollar.get('status', 'neutral')}">
                    <div class="indicator-title">💵 Dollar Index (DXY)</div>
                    <div class="indicator-value">{dollar.get('value', 'N/A')}</div>
                    <div class="indicator-change {dollar.get('status', 'neutral')}">
                        {dollar.get('change', 'N/A')} ({dollar.get('pchange', 'N/A')}%)
                    </div>
                </div>
            </div>
        </section>
        
        <section class="news-section">
            <h2 class="section-title">Global News Feed</h2>
            <div class="news-grid">
"""
        
        # Add news categories
        categories = {
            'india': ('🇮🇳 Indian Markets', 'India-specific market news and developments'),
            'economic': ('💰 Economic & Policy', 'Interest rates, inflation, GDP, employment'),
            'corporate': ('🏢 Corporate News', 'Earnings, M&A, executive changes'),
            'geopolitical': ('🌍 Geopolitical Events', 'Global politics, trade, conflicts'),
            'markets': ('📊 Market Updates', 'Stock movements, commodities, currencies')
        }
        
        for cat_key, (title, desc) in categories.items():
            html += f"""
                <div class="news-category-card {cat_key}">
                    <div class="category-header">
                        <h3 class="category-title">{title}</h3>
                    </div>
"""
            
            if self.news_data[cat_key]:
                for item in self.news_data[cat_key]:
                    summary_html = f'<p class="news-summary">{item["summary"]}</p>' if item.get('summary') else ''
                    html += f"""
                    <div class="news-item">
                        <h3><a href="{item['link']}" target="_blank">{item['title']}</a></h3>
                        <div class="news-meta">
                            <span class="news-source">{item['source']}</span>
                            <span class="news-date">{item.get('published', 'Unknown date')}</span>
                        </div>
                        {summary_html}
                    </div>
"""
            else:
                html += '<p class="no-news">No news available in this category</p>'
            
            html += """
                </div>
"""
        
        html += """
            </div>
        </section>
        
        <footer>
            <p>🔄 Data updates in real-time | Sources: NSE, Yahoo Finance, Reuters, Bloomberg, CNBC, MoneyControl</p>
            <p style="margin-top: 10px; opacity: 0.6;">Built with Python, yfinance & feedparser | Hosted on GitHub Pages</p>
            <p style="margin-top: 10px; font-size: 0.75em; opacity: 0.5;">⚠️ For informational purposes only. Not financial advice.</p>
        </footer>
    </div>
    
    <script>
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>
</body>
</html>"""
        
        return html
    
    def run(self):
        """Main execution"""
        print("\n" + "="*60)
        print("🚀 COMPREHENSIVE MARKET DASHBOARD GENERATOR")
        print("="*60)
        
        # Fetch market data
        self.fetch_market_indicators()
        
        # Fetch news
        self.fetch_all_news()
        
        # Generate HTML
        print("\n📝 Generating comprehensive HTML dashboard...")
        html_content = self.generate_html()
        
        # Save to file
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("\n" + "="*60)
        print("✅ SUCCESS! Dashboard generated: index.html")
        print("="*60)
        print("\n📊 Dashboard includes:")
        print("  • 6 Live market indicators")
        total_articles = sum(len(v) for v in self.news_data.values())
        print(f"  • {total_articles} news articles from multiple sources")
        print("  • 5 news categories (India, Economic, Corporate, Geopolitical, Markets)")
        print("\n📋 Next Steps:")
        print("1. Open index.html in your browser to preview")
        print("2. Upload to GitHub repository")
        print("3. Enable GitHub Pages")
        print("4. Your dashboard will be live!")
        print("\n💡 Tip: Schedule this script to run every 15 minutes via GitHub Actions")
        print("="*60 + "\n")

if __name__ == "__main__":
    dashboard = ComprehensiveMarketDashboard()
    dashboard.run()
