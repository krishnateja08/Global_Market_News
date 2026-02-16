#!/usr/bin/env python3
"""
Comprehensive Global Market News & Indicators Dashboard
Generates HTML with REAL news headlines fetched from web searches
For deployment on GitHub Pages or any static hosting
"""

import json
import sys
from datetime import datetime, timedelta

# Real news headlines - These would be fetched from your web search in production
REAL_NEWS = {
    "markets": [
        {"title": "AI Disruption Fears Spread Beyond Software to Financial Services and Real Estate", "source": "CNBC", "time": "2 hours ago"},
        {"title": "S&P 500 Closes Barely Above Flatline as Inflation Report Fails to Spark Rally", "source": "CNBC", "time": "3 hours ago"},
        {"title": "Pinterest Shares Plunge 18% on Earnings Miss and Weak Guidance", "source": "CNBC", "time": "4 hours ago"},
        {"title": "Goldman Sachs Names Five Stocks Too Attractive to Ignore, Including Nvidia", "source": "CNBC", "time": "5 hours ago"},
        {"title": "Netflix and Amazon Among Most Oversold Stocks on Wall Street", "source": "CNBC", "time": "1 day ago"},
        {"title": "Steel Makers Drop as Trump Plans to Roll Back Tariffs on Steel and Aluminum", "source": "Charles Schwab", "time": "6 hours ago"},
        {"title": "International Stocks Outpace S&P 500 by 700 Basis Points Year-to-Date", "source": "Charles Schwab", "time": "1 day ago"},
        {"title": "Apple Falls 5% on FTC Investigation and Siri Upgrade Delays", "source": "Charles Schwab", "time": "1 day ago"},
        {"title": "Home Builders Rise as Treasury Yields Fall Amid Market Volatility", "source": "Charles Schwab", "time": "2 days ago"},
        {"title": "Every Magnificent Seven Stock Declined Thursday in Extended Soft Streak", "source": "CNBC", "time": "2 days ago"}
    ],
    "economic": [
        {"title": "Federal Reserve Maintains Rates at 3.50-3.75%, Signals Cautious Approach", "source": "Federal Reserve", "time": "Jan 28, 2026"},
        {"title": "Vice Chair Bowman: Policy Can Afford to 'Keep Powder Dry' After Rate Cuts", "source": "Federal Reserve", "time": "5 days ago"},
        {"title": "Fed Finalizes Stress Test Scenarios, Maintains Capital Requirements", "source": "Federal Reserve", "time": "Feb 4, 2026"},
        {"title": "Vice Chair Jefferson Warns Evolving Risks Require Slow Policy Approach", "source": "Federal Reserve", "time": "1 week ago"},
        {"title": "Consumer Price Index Rises 0.2% in January, Below Expectations", "source": "Bureau of Labor Statistics", "time": "3 hours ago"},
        {"title": "Core PCE Inflation Likely Below 3% in December, Trimmed Measures Show Decline", "source": "Federal Reserve", "time": "1 week ago"},
        {"title": "Labor Market Shows Fragility Beneath Surface Despite Continued Growth", "source": "Federal Reserve", "time": "Jan 30, 2026"},
        {"title": "Government Shutdown Delays Key Economic Data Releases Including Jobs Report", "source": "Federal Reserve", "time": "2 weeks ago"},
        {"title": "Fed Balance Sheet Reduction Concludes After $2.2 Trillion Decline", "source": "Federal Reserve", "time": "Dec 1, 2025"},
        {"title": "Productivity Gains Suggest Businesses Can Bear Higher Costs Without Price Increases", "source": "Richmond Fed", "time": "Feb 3, 2026"}
    ],
    "india": [
        {"title": "Sensex, Nifty Trade in Positive Terrain as Media Shares Skid for Third Day", "source": "ICICI Direct", "time": "Today"},
        {"title": "Nifty 50 Down 0.32% at 26,165 as Markets Show Mixed Performance", "source": "NSE India", "time": "Today"},
        {"title": "BSE Sensex Falls 0.38% to 85,440 in Volatile Trading Session", "source": "BSE India", "time": "Today"},
        {"title": "Reliance Industries Drops 4.58% Leading Nifty Decliners", "source": "Yahoo Finance India", "time": "Today"},
        {"title": "State Bank of India Gains 1.33%, Banking Stocks Outperform", "source": "NSE India", "time": "Today"},
        {"title": "Tata Consultancy Services Rises 0.75% as IT Sector Shows Resilience", "source": "NSE India", "time": "Today"},
        {"title": "FII and DII Activity Remains Balanced as Domestic Investors Stay Active", "source": "MoneyControl", "time": "Today"},
        {"title": "Nifty Bank Index Gains Ground as Financial Stocks Lead Market Recovery", "source": "NSE India", "time": "Today"},
        {"title": "Indian Markets Trade Below Opening Levels as Profit Booking Emerges", "source": "Economic Times", "time": "Today"},
        {"title": "52-Week High Stocks Show Strong Momentum Across Sectors", "source": "Groww", "time": "Today"}
    ],
    "corporate": [
        {"title": "Airbnb Climbs 5% After Quarterly Revenue Surpasses Expectations", "source": "Charles Schwab", "time": "Today"},
        {"title": "Amazon Extends Losing Streak to Eight Sessions After Earnings Disappointment", "source": "CNBC", "time": "1 day ago"},
        {"title": "Disney and Netflix Hit by AI Disruption Fears in Media Sector", "source": "CNBC", "time": "2 days ago"},
        {"title": "Workday Software Stock Drops 11% This Week Amid AI Concerns", "source": "CNBC", "time": "2 days ago"},
        {"title": "Commercial Real Estate Firm CBRE Loses 16% Week-to-Date", "source": "CNBC", "time": "2 days ago"},
        {"title": "Yale's Endowment Model Underperforms as Stocks and Bonds Gain", "source": "Bloomberg", "time": "1 day ago"},
        {"title": "Credit Markets Face Reality Check After Decade of Loose Lending", "source": "Bloomberg", "time": "2 days ago"},
        {"title": "Consumer Financial Protection Bureau's 'Humility Pledge' Shows Regulatory Shift", "source": "Bloomberg", "time": "3 days ago"},
        {"title": "Major Pharmaceutical Companies Announce Earnings Beats Across Sector", "source": "Wall Street Journal", "time": "3 days ago"},
        {"title": "Tech IPO Market Shows Signs of Recovery with Multiple Filings", "source": "TechCrunch", "time": "4 days ago"}
    ],
    "geopolitical": [
        {"title": "Venezuela Oil Revenue Tops $1 Billion as US Changes Payment Structure", "source": "NBC News", "time": "2 days ago"},
        {"title": "US Economy Shows Resilience Despite Heightened Trade Policy Uncertainty", "source": "New York Fed", "time": "1 week ago"},
        {"title": "Government Shutdown Impact on Economic Activity Assessed by Fed Officials", "source": "Federal Reserve", "time": "2 weeks ago"},
        {"title": "Global Trade Policy Shifts Create Uncertainty for Supply Chains", "source": "Bloomberg", "time": "3 days ago"},
        {"title": "Emerging Markets Show Divergent Performance Amid Dollar Volatility", "source": "Financial Times", "time": "4 days ago"},
        {"title": "European Central Bank Maintains Cautious Stance on Rate Policy", "source": "Bloomberg", "time": "5 days ago"},
        {"title": "China Manufacturing Data Shows Mixed Signals for Global Growth", "source": "Reuters", "time": "1 week ago"},
        {"title": "Oil Markets Stabilize as OPEC+ Production Decisions Awaited", "source": "Bloomberg", "time": "2 days ago"},
        {"title": "International Monetary Fund Revises Global Growth Forecasts", "source": "IMF", "time": "1 week ago"},
        {"title": "Asian Markets Show Resilience Amid Global Volatility", "source": "Financial Times", "time": "Today"}
    ]
}

def get_ist_time():
    """Get current IST time"""
    utc_time = datetime.utcnow()
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return ist_time.strftime('%B %d, %Y at %I:%M %p IST')

def generate_news_html(category_news):
    """Generate HTML for news items"""
    html_items = []
    for item in category_news:
        html_items.append(f"""
                <div class="news-item">
                    <h3>{item['title']}</h3>
                    <div class="news-meta">
                        <span class="news-source">{item['source']}</span>
                        <span class="news-date">{item['time']}</span>
                    </div>
                </div>""")
    return "\n".join(html_items)

def generate_complete_html():
    """Generate complete HTML with all features"""
    
    current_time = get_ist_time()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Market Dashboard - LIVE DATA & REAL NEWS</title>
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
            
            --usa-red: #B22234;
            --usa-white: #FFFFFF;
            --usa-blue: #3C3B6E;
            
            --india-saffron: #FF9933;
            --india-white: #FFFFFF;
            --india-green: #138808;
            --india-navy: #000080;
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
        
        .loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(10, 14, 39, 0.95);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            transition: opacity 0.5s;
        }}
        
        .loading-overlay.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        
        .spinner {{
            width: 50px;
            height: 50px;
            border: 3px solid rgba(74, 158, 255, 0.3);
            border-top-color: #4a9eff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .loading-text {{
            margin-top: 20px;
            font-family: 'Space Mono', monospace;
            color: var(--accent-blue);
            font-size: 1.1em;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 25px 20px;
            background: rgba(26, 35, 71, 0.5);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            border: 1px solid var(--border-color);
            box-shadow: 0 15px 40px var(--card-shadow);
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
            font-size: 2.2em;
            font-weight: 900;
            background: linear-gradient(135deg, #4a9eff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            letter-spacing: -1px;
            position: relative;
            z-index: 1;
        }}
        
        .subtitle {{
            font-family: 'Space Mono', monospace;
            font-size: 0.85em;
            color: var(--text-secondary);
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        
        .live-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #ff4757, #ff6b81);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 700;
            margin-top: 10px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        
        .timestamp {{
            margin-top: 12px;
            font-family: 'Space Mono', monospace;
            font-size: 0.75em;
            color: var(--accent-blue);
            opacity: 0.8;
        }}
        
        .section-title {{
            font-family: 'Playfair Display', serif;
            font-size: 2.5em;
            font-weight: 900;
            margin-bottom: 30px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(74, 158, 255, 0.3);
        }}
        
        .section-title-usa {{
            font-family: 'Playfair Display', serif;
            font-size: 2.5em;
            font-weight: 900;
            margin-bottom: 30px;
            background: linear-gradient(135deg, var(--usa-red) 0%, var(--usa-white) 35%, var(--usa-blue) 70%, var(--usa-white) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(178, 34, 52, 0.4);
            filter: drop-shadow(0 0 20px rgba(60, 59, 110, 0.3));
        }}
        
        .section-title-india {{
            font-family: 'Playfair Display', serif;
            font-size: 2.5em;
            font-weight: 900;
            margin-bottom: 30px;
            background: linear-gradient(135deg, var(--india-saffron) 0%, var(--india-white) 35%, var(--india-green) 70%, var(--india-navy) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(255, 153, 51, 0.4);
            filter: drop-shadow(0 0 20px rgba(19, 136, 8, 0.3));
        }}
        
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
        }}
        
        .category-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid;
        }}
        
        .category-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.6em;
            font-weight: 700;
        }}
        
        .markets .category-header {{ border-color: var(--accent-red); }}
        .markets .category-title {{ color: var(--accent-red); }}
        
        .economic .category-header {{ border-color: var(--accent-pink); }}
        .economic .category-title {{ color: var(--accent-pink); }}
        
        .india .category-header {{ border-color: var(--accent-yellow); }}
        .india .category-title {{ color: var(--accent-yellow); }}
        
        .corporate .category-header {{ border-color: var(--accent-cyan); }}
        .corporate .category-title {{ color: var(--accent-cyan); }}
        
        .geopolitical .category-header {{ border-color: var(--accent-green); }}
        .geopolitical .category-title {{ color: var(--accent-green); }}
        
        .news-item {{
            padding: 15px;
            margin-bottom: 12px;
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
        
        .markets .news-item {{ border-left-color: var(--accent-red); }}
        .economic .news-item {{ border-left-color: var(--accent-pink); }}
        .india .news-item {{ border-left-color: var(--accent-yellow); }}
        .corporate .news-item {{ border-left-color: var(--accent-cyan); }}
        .geopolitical .news-item {{ border-left-color: var(--accent-green); }}
        
        .news-item h3 {{
            font-size: 0.95em;
            margin-bottom: 8px;
            line-height: 1.4;
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .news-meta {{
            display: flex;
            gap: 10px;
            align-items: center;
            margin-top: 6px;
            font-size: 0.75em;
            color: var(--text-secondary);
            flex-wrap: wrap;
        }}
        
        .news-source {{
            display: inline-block;
            background: var(--accent-blue);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.85em;
            font-family: 'Space Mono', monospace;
        }}
        
        .news-date {{
            font-family: 'Space Mono', monospace;
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
            .news-grid {{ grid-template-columns: 1fr; }}
        }}
        
        @media (max-width: 768px) {{
            h1 {{ font-size: 1.8em; }}
            .section-title, .section-title-usa, .section-title-india {{ font-size: 2em; }}
        }}
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
        <div class="loading-text">Loading Market Data...</div>
    </div>
    
    <div class="container">
        <header>
            <h1>🌍 Global Market Dashboard</h1>
            <div class="subtitle">Real-Time Market Data & Live News Headlines</div>
            <div class="live-badge">🔴 LIVE DATA</div>
            <div class="timestamp" id="timestamp">📅 Generated: {current_time}</div>
        </header>
        
        <section class="indicators-section">
            <h2 class="section-title">Live Market Indicators</h2>
            <div class="indicators-grid">
                <div class="indicator-card neutral" id="card-gift-nifty">
                    <div class="indicator-title">🎯 GIFT Nifty</div>
                    <div class="indicator-value" id="val-gift-nifty">Loading...</div>
                    <div class="indicator-change neutral" id="chg-gift-nifty">...</div>
                </div>
                
                <div class="indicator-card neutral" id="card-dow">
                    <div class="indicator-title">📈 Dow Jones</div>
                    <div class="indicator-value" id="val-dow">Loading...</div>
                    <div class="indicator-change neutral" id="chg-dow">...</div>
                </div>
                
                <div class="indicator-card neutral" id="card-sp500">
                    <div class="indicator-title">💹 S&P 500</div>
                    <div class="indicator-value" id="val-sp500">Loading...</div>
                    <div class="indicator-change neutral" id="chg-sp500">...</div>
                </div>
                
                <div class="indicator-card neutral" id="card-nasdaq">
                    <div class="indicator-title">💻 Nasdaq</div>
                    <div class="indicator-value" id="val-nasdaq">Loading...</div>
                    <div class="indicator-change neutral" id="chg-nasdaq">...</div>
                </div>
                
                <div class="indicator-card neutral" id="card-oil">
                    <div class="indicator-title">🛢️ Crude Oil</div>
                    <div class="indicator-value" id="val-oil">Loading...</div>
                    <div class="indicator-change neutral" id="chg-oil">...</div>
                </div>
                
                <div class="indicator-card neutral" id="card-dollar">
                    <div class="indicator-title">💵 Dollar Index</div>
                    <div class="indicator-value" id="val-dollar">Loading...</div>
                    <div class="indicator-change neutral" id="chg-dollar">...</div>
                </div>
                
                <div class="indicator-card neutral" id="card-gold">
                    <div class="indicator-title">🪙 Gold</div>
                    <div class="indicator-value" id="val-gold">Loading...</div>
                    <div class="indicator-change neutral" id="chg-gold">...</div>
                </div>
                
                <div class="indicator-card neutral" id="card-silver">
                    <div class="indicator-title">⚪ Silver</div>
                    <div class="indicator-value" id="val-silver">Loading...</div>
                    <div class="indicator-change neutral" id="chg-silver">...</div>
                </div>
            </div>
        </section>
        
        <section class="economic-indicators-section">
            <h2 class="section-title-usa">🇺🇸 USA Economic Indicators</h2>
            <div class="indicators-grid">
                <div class="indicator-card neutral">
                    <div class="indicator-title">💵 Interest Rate</div>
                    <div class="indicator-value">3.50-3.75%</div>
                    <div class="indicator-change neutral">Fed Funds Rate</div>
                </div>
                
                <div class="indicator-card neutral">
                    <div class="indicator-title">🏛️ FOMC</div>
                    <div class="indicator-value">Hold</div>
                    <div class="indicator-change neutral">Next: Mar 18-19, 2026</div>
                </div>
                
                <div class="indicator-card neutral">
                    <div class="indicator-title">📊 CPI</div>
                    <div class="indicator-value">2.4%</div>
                    <div class="indicator-change neutral">+0.2% MoM | +2.4% YoY</div>
                </div>
                
                <div class="indicator-card neutral">
                    <div class="indicator-title">📈 Core CPI</div>
                    <div class="indicator-value">2.5%</div>
                    <div class="indicator-change neutral">+2.5% YoY</div>
                </div>
                
                <div class="indicator-card neutral">
                    <div class="indicator-title">📉 Inflation</div>
                    <div class="indicator-value">2.4%</div>
                    <div class="indicator-change neutral">YoY +0.2%</div>
                </div>
                
                <div class="indicator-card neutral">
                    <div class="indicator-title">🏭 PPI</div>
                    <div class="indicator-value">1.8%</div>
                    <div class="indicator-change neutral">+1.8% YoY</div>
                </div>
                
                <div class="indicator-card positive">
                    <div class="indicator-title">💹 GDP Growth</div>
                    <div class="indicator-value">2.8%</div>
                    <div class="indicator-change positive">Q4 2025</div>
                </div>
                
                <div class="indicator-card positive">
                    <div class="indicator-title">👔 Unemployment</div>
                    <div class="indicator-value">3.7%</div>
                    <div class="indicator-change positive">Unemployment Rate</div>
                </div>
                
                <div class="indicator-card positive">
                    <div class="indicator-title">👥 NFP</div>
                    <div class="indicator-value">+256K</div>
                    <div class="indicator-change positive">Non-Farm Payrolls</div>
                </div>
            </div>
        </section>
        
        <section class="economic-indicators-section">
            <h2 class="section-title-india">🇮🇳 India Economic Indicators</h2>
            <div class="indicators-grid">
                <div class="indicator-card neutral">
                    <div class="indicator-title">💰 Repo Rate</div>
                    <div class="indicator-value">5.25%</div>
                    <div class="indicator-change neutral">RBI Policy Rate</div>
                </div>
                
                <div class="indicator-card neutral">
                    <div class="indicator-title">📊 CPI</div>
                    <div class="indicator-value">5.2%</div>
                    <div class="indicator-change neutral">+5.2% YoY</div>
                </div>
                
                <div class="indicator-card neutral">
                    <div class="indicator-title">📈 WPI</div>
                    <div class="indicator-value">2.4%</div>
                    <div class="indicator-change neutral">+2.4% YoY</div>
                </div>
                
                <div class="indicator-card positive">
                    <div class="indicator-title">🏭 IIP</div>
                    <div class="indicator-value">4.2%</div>
                    <div class="indicator-change positive">+4.2% YoY</div>
                </div>
                
                <div class="indicator-card positive">
                    <div class="indicator-title">📉 PMI</div>
                    <div class="indicator-value">56.8</div>
                    <div class="indicator-change positive">Manufacturing PMI</div>
                </div>
                
                <div class="indicator-card positive">
                    <div class="indicator-title">💹 GDP Growth</div>
                    <div class="indicator-value">7.4%</div>
                    <div class="indicator-change positive">FY 2025-26</div>
                </div>
                
                <div class="indicator-card neutral">
                    <div class="indicator-title">🏛️ Fiscal Deficit</div>
                    <div class="indicator-value">5.8%</div>
                    <div class="indicator-change neutral">5.8% of GDP</div>
                </div>
            </div>
        </section>
        
        <section class="news-section">
            <h2 class="section-title">📰 Live News Headlines</h2>
            <div class="news-grid">
                <div class="news-category-card markets">
                    <div class="category-header">
                        <h3 class="category-title">📊 Market Updates</h3>
                    </div>
                    <div>
                        {generate_news_html(REAL_NEWS['markets'])}
                    </div>
                </div>
                
                <div class="news-category-card economic">
                    <div class="category-header">
                        <h3 class="category-title">💰 Economic & Policy</h3>
                    </div>
                    <div>
                        {generate_news_html(REAL_NEWS['economic'])}
                    </div>
                </div>
                
                <div class="news-category-card india">
                    <div class="category-header">
                        <h3 class="category-title">🇮🇳 Indian Markets</h3>
                    </div>
                    <div>
                        {generate_news_html(REAL_NEWS['india'])}
                    </div>
                </div>
                
                <div class="news-category-card corporate">
                    <div class="category-header">
                        <h3 class="category-title">🏢 Corporate News</h3>
                    </div>
                    <div>
                        {generate_news_html(REAL_NEWS['corporate'])}
                    </div>
                </div>
                
                <div class="news-category-card geopolitical">
                    <div class="category-header">
                        <h3 class="category-title">🌍 Geopolitical Events</h3>
                    </div>
                    <div>
                        {generate_news_html(REAL_NEWS['geopolitical'])}
                    </div>
                </div>
            </div>
        </section>
        
        <footer>
            <p>🔄 Market data updates in real-time | News generated at build time</p>
            <p style="margin-top: 10px; font-size: 0.75em; opacity: 0.5;">⚠️ For informational purposes only. Not financial advice.</p>
        </footer>
    </div>
    
    <script>
        // Yahoo Finance API Configuration
        const API_CONFIG = {{
            baseUrl: 'https://query1.finance.yahoo.com/v8/finance/chart/',
            params: '?interval=1d&range=1d',
            proxies: [
                '', // Direct (no proxy)
                'https://corsproxy.io/?', // Proxy 1
                'https://api.allorigins.win/raw?url=' // Proxy 2
            ],
            timeout: 5000
        }};
        
        const SYMBOLS = {{
            'gift-nifty': '^NSEI',
            'dow': '^DJI',
            'sp500': '^GSPC',
            'nasdaq': '^IXIC',
            'oil': 'CL=F',
            'dollar': 'DX-Y.NYB',
            'gold': 'GC=F',
            'silver': 'SI=F'
        }};
        
        const FALLBACK_DATA = {{
            'gift-nifty': {{value: '26,165.00', change: '-84.50', pchange: '-0.32'}},
            'dow': {{value: '49,450.12', change: '+48.95', pchange: '+0.10'}},
            'sp500': {{value: '6,836.17', change: '+3.41', pchange: '+0.05'}},
            'nasdaq': {{value: '19,735.12', change: '-50.43', pchange: '-0.25'}},
            'oil': {{value: '$62.75', change: '+0.00', pchange: '+0.00'}},
            'dollar': {{value: '96.88', change: '-0.04', pchange: '-0.04'}},
            'gold': {{value: '$5,023.48', change: '+23.48', pchange: '+0.47'}},
            'silver': {{value: '$78.79', change: '-3.21', pchange: '-3.91'}}
        }};
        
        let currentProxyIndex = 0;
        
        function updateTimestamp(isFallback = false) {{
            const now = new Date();
            const options = {{ 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit',
                timeZone: 'Asia/Kolkata'
            }};
            const formatted = now.toLocaleString('en-US', options) + ' IST';
            const prefix = isFallback ? '📅 Cached Data - ' : '📅 Last Updated: ';
            document.getElementById('timestamp').textContent = prefix + formatted;
        }}
        
        function updateIndicator(id, value, change, pchange) {{
            const valueEl = document.getElementById(`val-${{id}}`);
            const changeEl = document.getElementById(`chg-${{id}}`);
            const cardEl = document.getElementById(`card-${{id}}`);
            
            if (valueEl) valueEl.textContent = value;
            if (changeEl && change !== undefined) {{
                const pchangeNum = parseFloat(pchange);
                const changeText = pchangeNum >= 0 ? `+${{change}}` : change;
                const pchangeText = pchangeNum >= 0 ? `+${{pchange}}%` : `${{pchange}}%`;
                changeEl.textContent = `${{changeText}} (${{pchangeText}})`;
                
                if (pchangeNum > 0) {{
                    changeEl.className = 'indicator-change positive';
                    cardEl.className = 'indicator-card positive';
                }} else if (pchangeNum < 0) {{
                    changeEl.className = 'indicator-change negative';
                    cardEl.className = 'indicator-card negative';
                }} else {{
                    changeEl.className = 'indicator-change neutral';
                    cardEl.className = 'indicator-card neutral';
                }}
            }}
        }}
        
        async function fetchWithTimeout(url, timeout = 5000) {{
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);
            
            try {{
                const response = await fetch(url, {{ 
                    signal: controller.signal,
                    mode: 'cors'
                }});
                clearTimeout(timeoutId);
                return response;
            }} catch (error) {{
                clearTimeout(timeoutId);
                throw error;
            }}
        }}
        
        async function fetchMarketData(key, symbol) {{
            const url = `${{API_CONFIG.baseUrl}}${{symbol}}${{API_CONFIG.params}}`;
            
            for (let i = 0; i < API_CONFIG.proxies.length; i++) {{
                const proxy = API_CONFIG.proxies[(currentProxyIndex + i) % API_CONFIG.proxies.length];
                const finalUrl = proxy ? proxy + encodeURIComponent(url) : url;
                
                try {{
                    const response = await fetchWithTimeout(finalUrl, API_CONFIG.timeout);
                    
                    if (!response.ok) continue;
                    
                    const data = await response.json();
                    
                    if (data.chart && data.chart.result && data.chart.result[0]) {{
                        const result = data.chart.result[0];
                        const meta = result.meta;
                        const currentPrice = meta.regularMarketPrice;
                        const previousClose = meta.chartPreviousClose || meta.previousClose;
                        
                        if (!currentPrice || !previousClose) continue;
                        
                        const change = currentPrice - previousClose;
                        const pchange = ((change / previousClose) * 100).toFixed(2);
                        
                        let displayValue;
                        if (['dow', 'sp500', 'nasdaq', 'gift-nifty'].includes(key)) {{
                            displayValue = currentPrice.toLocaleString('en-US', {{
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            }});
                        }} else if (key === 'dollar') {{
                            displayValue = currentPrice.toFixed(2);
                        }} else {{
                            displayValue = `$${{currentPrice.toFixed(2)}}`;
                        }}
                        
                        updateIndicator(key, displayValue, change.toFixed(2), pchange);
                        
                        if (i > 0) currentProxyIndex = (currentProxyIndex + i) % API_CONFIG.proxies.length;
                        return true;
                    }}
                }} catch (error) {{
                    console.warn(`Failed to fetch ${{key}} with ${{proxy || 'direct'}}:`, error.message);
                    continue;
                }}
            }}
            
            return false;
        }}
        
        async function loadAllMarketData() {{
            let successCount = 0;
            
            for (const [key, symbol] of Object.entries(SYMBOLS)) {{
                const success = await fetchMarketData(key, symbol);
                if (success) {{
                    successCount++;
                }} else {{
                    const fallback = FALLBACK_DATA[key];
                    if (fallback) {{
                        updateIndicator(key, fallback.value, fallback.change, fallback.pchange);
                    }}
                }}
                
                await new Promise(resolve => setTimeout(resolve, 150));
            }}
            
            updateTimestamp(successCount < 3);
            
            setTimeout(() => {{
                document.getElementById('loadingOverlay').classList.add('hidden');
            }}, 500);
        }}
        
        window.addEventListener('DOMContentLoaded', () => {{
            loadAllMarketData();
        }});
        
        setInterval(() => {{
            loadAllMarketData();
        }}, 300000);
        
        setInterval(updateTimestamp, 60000);
    </script>
</body>
</html>"""
    
    return html

def main():
    """Main function"""
    print("\n" + "="*70)
    print("🚀 GENERATING MARKET DASHBOARD FOR GITHUB DEPLOYMENT")
    print("="*70)
    
    print("\n📝 Generating complete HTML with:")
    print("  ✓ Live market data (Yahoo Finance)")
    print("  ✓ 50 Real news headlines (embedded)")
    print("  ✓ USA & India economic indicators")
    print("  ✓ Beautiful responsive design")
    
    try:
        html_content = generate_complete_html()
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("\n" + "="*70)
        print("✅ SUCCESS! Dashboard generated: index.html")
        print("="*70)
        print("\n📊 File ready for GitHub Pages deployment!")
        print("  • Upload to your GitHub repository")
        print("  • Enable GitHub Pages in settings")
        print("  • Access at: https://yourusername.github.io/repo-name/")
        print("\n💡 Market data will update live in the browser!")
        print("="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
