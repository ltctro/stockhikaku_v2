import streamlit as st
st.set_page_config(page_title="株価比較 + 投資家心理指標", layout="wide")

api_key = st.secrets["FMP_API_KEY"]

# Secrets からパスワードを取得
APP_PASSWORD = st.secrets["APP_PASSWORD"]

# 🔐 simple password lock
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Private Access")
    pwd = st.text_input("Password", type="password")
    if pwd == APP_PASSWORD:
        st.session_state.auth = True
        st.rerun()
    else:
        st.stop()

import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
import sqlite3
import json
import os
from datetime import datetime, timedelta


# ==============================
# 💾 DB 設定(market_cache.db に保存)
# ==============================
DB_PATH = "market_cache.db"
STOCKS_CACHE_FILE = "stocks_cache.json"

def fetch_all_stocks():
    """yfinance から上場銘柄リストを取得(初回のみ)"""
    # 日本株 と 米国大型株を取得
    default_stocks = {
        # 日本 - 主要銘柄
        "7203": "トヨタ", "7267": "ホンダ", "7201": "日産", "6502": "東芝", "6758": "ソニー",
        "7974": "任天堂", "6954": "ファナック", "6981": "村田製作所", "6902": "デンソー",
        "9432": "NTT", "9433": "KDDI", "9434": "ソフトバンク", "8306": "日本銀行",
        "8308": "りそな", "8309": "三菱UFJ", "8314": "三井住友FG", "8801": "三井不動産",
        "8802": "三菱地所", "8031": "三井物産", "8058": "三菱商事", "8591": "オリックス",
        "2002": "日清製粉", "2222": "寿スピリッツ", "4503": "アステラス製薬", "4578": "大塚",
        "4661": "オリエンタルランド", "1833": "旭化成", "4183": "三菱ケミカル", "5411": "JFEスチール",
        "6367": "ダイキン", "7731": "ニコン", "8113": "ファミマ", "3382": "セブンアイ",
        "2914": "JT", "1963": "日本パイプ", "2170": "リンテック", "6326": "クボタ",
        "9766": "関西電力", "9513": "電源開発", "4005": "昭和電工", "2768": "双日",
        "9461": "百五銀行", "1820": "ルミナス", "8725": "京王電鉄", "9020": "JR東日本",
        "5108": "ブリヂストン", "7012": "川崎重工", "7272": "ヤマハ発", "5214": "日本電気硝子",
        "6645": "オムロン", "6674": "ジオマテック", "7741": "HOYA", "9022": "近鉄グループ",
        "9101": "日本郵船", "9104": "商船三井", "9107": "川崎汽船", "6098": "リクルート",
        "3086": "J.フロント", "8252": "丸井グループ", "8233": "高島屋", "9984": "ソフトバンク",
        "6701": "NEC", "8630": "野村証券", "8633": "大和証券", "6869": "シスメックス",
        "4755": "楽天", "9999": "会社A",  # ダミー
        # 米国 - 主要 500
        "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google", "AMZN": "Amazon",
        "NVDA": "Nvidia", "META": "Meta", "TSLA": "Tesla", "BRK.B": "Berkshire",
        "JPM": "JPMorgan", "V": "Visa", "JNJ": "J&J", "WMT": "Walmart",
        "MA": "Mastercard", "PG": "Procter", "PYPL": "PayPal", "INTC": "Intel",
        "AMD": "AMD", "CSCO": "Cisco", "ORCL": "Oracle", "IBM": "IBM",
        "ADBE": "Adobe", "CRM": "Salesforce", "NFLX": "Netflix", "DIS": "Disney",
        "BA": "Boeing", "CAT": "Caterpillar", "GE": "GE", "HON": "Honeywell",
        "MMM": "3M", "LMT": "Lockheed", "RTX": "Raytheon", "TXN": "Texas Inst",
        "QCOM": "Qualcomm", "AVGO": "Broadcom", "MU": "Micron", "CRM": "Salesforce",
        "COIN": "Coinbase", "NFLX": "Netflix", "ROKU": "Roku", "SPOT": "Spotify",
        "ZM": "Zoom", "SHOP": "Shopify", "UBER": "Uber", "LYFT": "Lyft",
        "ARKK": "Ark Innovation", "QQQ": "Nasdaq 100", "SPY": "S&P 500", "IVV": "iShares",
        "XOM": "ExxonMobil", "CVX": "Chevron", "COP": "ConocoPhillips", "EOG": "EOG",
        "MPC": "Marathon", "PSX": "Phillips 66", "SLB": "Schlumberger", "HAL": "Halliburton",
        "FDX": "FedEx", "UPS": "UPS", "DAL": "Delta", "UAL": "United",
        "LUV": "Southwest", "AAL": "American", "ALK": "Alaska", "SAVE": "Spirit",
        "MGM": "MGM", "WYNN": "Wynn", "LVS": "Las Vegas", "CZR": "Caesars",
        "HLT": "Hilton", "RCL": "Royal", "CCL": "Carnival", "F": "Ford",
        "GM": "GM", "TM": "Toyota", "HMC": "Honda", "SNE": "Sony", "TSM": "TSMC",
        "ASML": "ASML", "SAP": "SAP", "UBER": "Uber", "AI": "C3 Metrics",
        "MSTR": "MicroStrategy", "RIOT": "Riot", "MARA": "Marathon Digital",
        "SQ": "Block", "HOOD": "Robinhood", "TD": "TD", "RY": "RBC",
        "BNS": "BMO", "CM": "CIBC", "EIF": "Empire State", "BBY": "Best Buy",
        "TGT": "Target", "COST": "Costco", "HD": "Home Depot", "LOW": "Lowe's",
        "NKE": "Nike", "MCD": "McDonald's", "SBUX": "Starbucks", "YUM": "Yum",
        "CMG": "Chipotle", "KO": "Coca-Cola", "PEP": "PepsiCo", "MDLZ": "Mondelez",
        "KHC": "Kraft", "TSCO": "Tractor", "LB": "L Brands", "GPS": "Gap",
        "AZO": "AutoZone", "O": "Realty", "PLD": "Prologis", "AMT": "American",
        "CCI": "Crown", "DLR": "Digital", "EQIX": "Equinix", "UNIT": "Uniti",
    }
    return default_stocks

def load_stocks_from_cache():
    """JSONキャッシュから銘柄データを読み込む(なければ作成)"""
    if os.path.exists(STOCKS_CACHE_FILE):
        try:
            with open(STOCKS_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    
    # JSONキャッシュがなければ、fetch_all_stocks()で取得して保存
    stocks = fetch_all_stocks()
    try:
        with open(STOCKS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(stocks, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return stocks

def init_db():
    """DB とテーブルを作る(なければ)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_cache (
            ticker TEXT,
            date TEXT,
            close REAL,
            volume REAL,
            PRIMARY KEY (ticker, date)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fear_greed (
            date TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticker_cache (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            cached_at TEXT
        )
    """)
    
    # JSONキャッシュから銘柄データを投入
    try:
        cur.execute("SELECT COUNT(*) FROM ticker_cache")
        count = cur.fetchone()[0]
        if count == 0:  # 初回のみ
            timestamp = datetime.today().isoformat()
            all_stocks = load_stocks_from_cache()
            for ticker, name in all_stocks.items():
                cur.execute("""
                    INSERT OR REPLACE INTO ticker_cache (ticker, name, cached_at)
                    VALUES (?, ?, ?)
                """, (ticker, name, timestamp))
            conn.commit()
    except Exception:
        pass
    
    conn.close()

def save_prices(ticker: str, df: pd.DataFrame):
    """price_cache に INSERT OR REPLACE で保存"""
    if df is None or df.empty:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = []
    for idx, row in df[['Close', 'Volume']].iterrows():
        date = idx.strftime("%Y-%m-%d")
        close = None if pd.isna(row['Close']) else float(row['Close'])
        vol = None if pd.isna(row['Volume']) else float(row['Volume'])
        rows.append((ticker, date, close, vol))
    if rows:
        cur.executemany("""
            INSERT OR REPLACE INTO price_cache (ticker, date, close, volume)
            VALUES (?, ?, ?, ?)
        """, rows)
        conn.commit()
    conn.close()

def load_prices_from_db(ticker: str, start_date: str) -> pd.DataFrame:
    """DB から指定 start_date 以降のデータを取得"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT date, close, volume
        FROM price_cache
        WHERE ticker = ? AND date >= ?
        ORDER BY date
    """, conn, params=(ticker, start_date))
    conn.close()
    if df.empty:
        return pd.DataFrame()
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df.rename(columns={'close': 'Close', 'volume': 'Volume'}, inplace=True)
    return df

def update_price_if_needed(ticker: str, period: str = "1y") -> pd.DataFrame:
    """yfinance取得+DB更新"""
    init_db()
    today = datetime.today().date()
    if period == "max":
        start_date = "1900-01-01"
    else:
        mapping = {"1y": 365, "3y": 365*3, "5y": 365*5, "10y": 365*10, "3mo":90, "6mo":180, "2y":365*2}
        days = mapping.get(period, 365)
        start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    local = load_prices_from_db(ticker, start_date)
    need_fetch = local.empty or local.index.max().date() < today
    if need_fetch:
        try:
            df_new = yf.Ticker(ticker).history(period=period)
            if df_new is None or df_new.empty:
                return local
            df_new.index = pd.to_datetime(df_new.index).tz_localize(None)
            save_prices(ticker, df_new)
            combined = load_prices_from_db(ticker, start_date)
            if combined.empty:
                df_new = df_new[['Close', 'Volume']].copy()
                return df_new
            return combined
        except Exception:
            return local
    else:
        return local

@st.cache_data(ttl=86400)   # 24時間ローカルDBのみ使用
def load_price_cached(ticker: str, period: str = "1y") -> pd.DataFrame:
    return update_price_if_needed(ticker, period)

@st.cache_data
def get_company_name(ticker: str) -> str:
    """会社名を取得(キャッシュ対応)"""
    try:
        info = yf.Ticker(ticker).info
        name = info.get('longName') or info.get('shortName') or ticker
        return name
    except Exception:
        return ticker

# セクター・業界別ETFマッピング
SECTOR_ETF_MAP = {
    'Technology': 'XLK',
    'Healthcare': 'XLV',
    'Financials': 'XLF',
    'Industrials': 'XLI',
    'Energy': 'XLE',
    'Consumer Cyclical': 'XLY',
    'Consumer Defensive': 'XLP',
    'Real Estate': 'XLRE',
    'Utilities': 'XLU',
    'Basic Materials': 'XLB',
    'Unknown': None
}
# 日本株 TOPIX-17 業種別ETF(業界トレンド用)
TOPIX17_ETF_MAP = {
    "Energy": "1618",            # エネルギー資源
    "Materials": "1617",         # 素材・化学
    "Industrials": "1610",       # 電気機器
    "Consumer Cyclical": "1612", # 自動車・輸送機
    "Consumer Defensive": "1613",# 食品
    "Healthcare": "1638",        # 医薬品
    "Financials": "1615",        # 銀行
    "Real Estate": "1633",       # 不動産
    "Utilities": "1627",         # 電力・ガス
}


@st.cache_data
def get_sector_avg_per() -> dict:
    """セクターETFのPERから業界別平均PERを取得(キャッシュ対応)"""
    sector_avg = {}
    for sector, etf in SECTOR_ETF_MAP.items():
        if etf is None:
            continue
        try:
            info = yf.Ticker(etf).info
            per = info.get('trailingPE') or info.get('forwardPE')
            if per is not None:
                sector_avg[sector] = per
        except Exception:
            pass
    return sector_avg

@st.cache_data
def get_financial_metrics(ticker: str) -> dict:
    """
    yfinance を基本にしつつ、EPS が壊れていたら FMP で補完する安全版。
    forwardPE は絶対に使わない。
    公開アプリでも APIキーが漏れないよう secrets から取得する。
    """
    per = None
    pbr = None
    sector = "Unknown"

    # --- 1 yfinance で取得 ---
    try:
        info = yf.Ticker(ticker).info
        price_yf = info.get("regularMarketPrice")
        eps_yf = info.get("epsTrailingTwelveMonths")
        pbr = info.get("priceToBook")
        sector = info.get("sector", "Unknown")

        # EPS が正常なら PER を計算
        if price_yf and eps_yf and eps_yf > 0:
            per = price_yf / eps_yf

    except Exception:
        pass

    # --- 2 FMP フォールバック(yfinance が壊れていた場合のみ) ---
    if per is None:
        try:
            # secrets から APIキーを取得(公開アプリでも安全)
            api_key = st.secrets["FMP_API_KEY"]

            # 日本株は .T を付ける
            fmp_ticker = ticker if "." in ticker else f"{ticker}.T"

            url = f"https://financialmodelingprep.com/api/v3/profile/{fmp_ticker}?apikey={api_key}"
            r = requests.get(url, timeout=5).json()

            if r:
                data = r[0]
                eps_fmp = data.get("eps")
                price_fmp = data.get("price")
                pbr_fmp = data.get("priceToBook")
                sector_fmp = data.get("sector")

                # FMP の EPS が正常なら PER を計算
                if price_fmp and eps_fmp and eps_fmp > 0:
                    per = price_fmp / eps_fmp

                # PBR 補完
                if pbr is None and pbr_fmp:
                    pbr = pbr_fmp

                # セクター補完
                if sector == "Unknown" and sector_fmp:
                    sector = sector_fmp

        except Exception:
            pass

    return {
        "PER": per,
        "PBR": pbr,
        "sector": sector
    }



def search_tickers(query: str) -> dict:
    """会社名またはティッカーから検索(複数キーワード対応)"""
    query_lower = query.lower().strip()
    if not query_lower:
        return {}
    
    results = {}
    init_db()  # DB初期化(データがなければ投入)
    
    # ローカルデータベースから検索
    try:
        conn = sqlite3.connect(DB_PATH)
        # ティッカー完全一致(優先度高)
        df_exact = pd.read_sql_query("""
            SELECT ticker, name FROM ticker_cache 
            WHERE LOWER(ticker) = ?
        """, conn, params=(query_lower,))
        
        for _, row in df_exact.iterrows():
            results[row['ticker']] = row['name']
        
        # 部分一致(ティッカーと名前)
        df_partial = pd.read_sql_query("""
            SELECT ticker, name FROM ticker_cache 
            WHERE LOWER(ticker) LIKE ? OR LOWER(name) LIKE ?
            LIMIT 15
        """, conn, params=(f"%{query_lower}%", f"%{query_lower}%"))
        conn.close()
        
        for _, row in df_partial.iterrows():
            if row['ticker'] not in results:  # 重複除去
                results[row['ticker']] = row['name']
    except Exception:
        pass
    
    # キャッシュに見つからない場合、yfinanceで直接検索(ティッカーのみ)
    if not results and (len(query_lower) <= 6 and query_lower.isalnum()):
        try:
            # 日本株の場合は .T サフィックスを試す
            test_tickers = [query_lower]
            if query_lower.isdigit():
                test_tickers.append(f"{query_lower}.T")
            
            for test_ticker in test_tickers:
                try:
                    info = yf.Ticker(test_ticker).info
                    if info and info.get('regularMarketPrice'):  # 有効なティッカー
                        name = info.get('longName') or info.get('shortName') or test_ticker
                        results[test_ticker] = name
                        break
                except Exception:
                    pass
        except Exception:
            pass
    
    return results

def add_ticker_to_cache(ticker: str, name: str):
    """ティッカーをJSONキャッシュに追加"""
    try:
        stocks = load_stocks_from_cache()
        if ticker not in stocks:
            stocks[ticker] = name
            with open(STOCKS_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(stocks, f, ensure_ascii=False, indent=2)
            
            # SQLiteにも追加
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            timestamp = datetime.today().isoformat()
            cur.execute("""
                INSERT OR REPLACE INTO ticker_cache (ticker, name, cached_at)
                VALUES (?, ?, ?)
            """, (ticker, name, timestamp))
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        return False
    return False

def load_fear_greed_cached() -> pd.DataFrame:
    """Fear & Greed Index 取得(キャッシュ対応)"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df_local = pd.read_sql_query("SELECT date, value FROM fear_greed ORDER BY date", conn)
    conn.close()
    if not df_local.empty:
        df_local['date'] = pd.to_datetime(df_local['date'])
        df_local = df_local.set_index('date')
        df_local.rename(columns={'value': 'Value'}, inplace=True)
        if df_local.index.max().date() >= (datetime.today().date() - timedelta(days=2)):
            return df_local
    try:
        url = "https://api.alternative.me/fng/?limit=0&format=json"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        df = pd.DataFrame(data.get("data", []))
        if df.empty:
            return df_local if not df_local.empty else pd.DataFrame()
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
        df["value"] = df["value"].astype(int)
        df_new = df[["timestamp", "value"]].rename(columns={"timestamp": "date"})
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM fear_greed")
        rows = [(r['date'].strftime("%Y-%m-%d"), int(r['value'])) for _, r in df_new.iterrows()]
        if rows:
            cur.executemany("INSERT OR REPLACE INTO fear_greed (date, value) VALUES (?, ?)", rows)
        conn.commit()
        conn.close()
        df_new = df_new.set_index('date').sort_index()
        df_new.rename(columns={'value': 'Value'}, inplace=True)
        return df_new
    except Exception as e:
        st.warning(f"Fear & Greed Index取得失敗: {e}")
        return df_local if not df_local.empty else pd.DataFrame()


# ============================
# UI部分
# ============================
st.title("📈 株価比較 + 投資家心理指標")

# ==== 銘柄入力(会社名検索対応) ====
st.subheader("銘柄を検索")

if "selected_tickers" not in st.session_state:
    st.session_state.selected_tickers = []
if "search_results" not in st.session_state:
    st.session_state.search_results = {}

search_query = st.text_input(
    "会社名またはティッカーシンボルで検索 (例: トヨタ, Apple, 7203)",
    placeholder="会社名またはティッカーを入力"
)

if search_query and len(search_query) > 0:
    with st.spinner("検索中..."):
        st.session_state.search_results = search_tickers(search_query)
    
    if st.session_state.search_results:
        st.write("**検索結果:**")
        for symbol, name in list(st.session_state.search_results.items())[:5]:
            col1, col2, col3 = st.columns([2.5, 1, 1])
            with col1:
                st.write(f"**{symbol}** - {name}")
            with col2:
                if st.button("追加", key=f"btn_{symbol}"):
                    ticker_to_add = f"{symbol}.T" if symbol.isdigit() else symbol
                    if ticker_to_add not in st.session_state.selected_tickers:
                        st.session_state.selected_tickers.append(ticker_to_add)
                    st.rerun()
            with col3:
                if st.button("辞書に追加", key=f"cache_{symbol}"):
                    if add_ticker_to_cache(symbol, name):
                        st.success(f"✓ {symbol} を辞書に追加しました")
                    else:
                        st.info(f"{symbol} は既に辞書に登録されています")

# 選択された銘柄を表示
if st.session_state.selected_tickers:
    st.write("**選択中の銘柄:**")
    cols = st.columns(len(st.session_state.selected_tickers) + 1)
    for i, ticker in enumerate(st.session_state.selected_tickers):
        with cols[i]:
            col_name, col_remove = st.columns([4, 1])
            company_name = get_company_name(ticker)
            with col_name:
                st.write(f"• {company_name} ({ticker})")
            with col_remove:
                if st.button("削除", key=f"remove_{ticker}"):
                    st.session_state.selected_tickers.remove(ticker)
                    st.rerun()

tickers = st.session_state.selected_tickers
codes = [t.replace(".T", "") if t.endswith(".T") else t for t in tickers]

# ==== 期間と日付指定 ====
col1, col2, col3 = st.columns(3)
with col1:
    period = st.selectbox("📅 取得期間", ["1y", "3y", "5y", "10y", "max"], index=4)
with col2:
    default_date = datetime.today().replace(year=datetime.today().year - 1)
    base_date = st.date_input("基準日を選択", value=default_date)
    base_ts = pd.to_datetime(base_date)
with col3:
    end_date = st.date_input("終了日を選択", value=datetime.today())
    end_ts = pd.to_datetime(end_date)

if end_ts < base_ts:
    st.error("❌ 終了日は基準日以降を指定してください。")
    st.stop()

# ==== 投資家心理指標選択 ====
sentiment_catalog = {
    "VIX指数": "^VIX",
    "VIX3M": "^VIX3M",
    "VVIX(VIXのボラ)": "^VVIX",
    "ドル指数 DXY": "DX-Y.NYB",
    "Fear & Greed Index": "FNG",
    "信用スプレッド(HYG-TLT)": "CREDIT_SPREAD",
    "ボラティリティ偏り(VIX/VVIX)": "VOL_BIAS",
    "米10年債利回り": "^TNX"
}

sentiment_options = list(sentiment_catalog.keys())
selected_sentiments = st.multiselect(
    "💡 心理指標を選択してください(第二軸に表示)",
    sentiment_options,
    default=["VIX指数"]
)

# ==== データ取得 ====
etf_data = {}
company_names = {}

for ticker, code in zip(tickers, codes):
    df = load_price_cached(ticker, period)
    if df.empty:
        continue
    df = df[(df.index >= base_ts) & (df.index <= end_ts)]
    if df.empty:
        continue
    base_price = df["Close"].iloc[0]
    df_rel = df.copy()
    df_rel["Relative Price"] = df_rel["Close"] / base_price
    etf_data[code] = df_rel
    company_names[code] = get_company_name(ticker)

# 心理指標データ取得
sentiment_data = {}
for name in selected_sentiments:
    code = sentiment_catalog[name]
    
    if code == "FNG":
        df = load_fear_greed_cached()
    elif code == "CREDIT_SPREAD":
        df_hyg = load_price_cached("HYG", period)
        df_tlt = load_price_cached("TLT", period)
        if not df_hyg.empty and not df_tlt.empty:
            df = pd.DataFrame(index=df_hyg.index)
            df["Value"] = df_hyg["Close"] / df_tlt["Close"]
        else:
            continue
    elif code == "VOL_BIAS":
        vix = load_price_cached("^VIX", period)
        vvix = load_price_cached("^VVIX", period)
        if not vix.empty and not vvix.empty:
            df = pd.DataFrame(index=vix.index)
            df["Value"] = vix["Close"] / vvix["Close"]
        else:
            continue
    else:
        df = load_price_cached(code, period)
        if df.empty:
            continue
        df["Value"] = df["Close"]
    
    df = df[(df.index >= base_ts) & (df.index <= end_ts)]
    if df.empty:
        continue
    
    sentiment_data[name] = df

# ==== 日本株業界トレンド(TOPIX-17)チェックボックス ====
show_topix17 = st.checkbox("📊 日本株の業界トレンド(TOPIX-17 ETF)を表示する", value=False)
# ==== グラフ生成 ====
if not etf_data and not sentiment_data:
    st.error("❌ データが見つかりませんでした。別の銘柄でお試しください。")
else:
    fig = go.Figure()

    # 第一軸:株価(相対価格)
    for code, df in etf_data.items():
        display_name = company_names.get(code, code)
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["Relative Price"],
            mode="lines",
            name=display_name,
            yaxis="y",
            hovertemplate="%{x|%Y-%m-%d}<br>" + display_name + ": %{y:.2f}x<extra></extra>"
        ))

    # ==== 日本株 TOPIX-17 業界トレンド(補助線) ====
    if show_topix17 and len(etf_data) > 0:
        for sector_name, etf_code in TOPIX17_ETF_MAP.items():
            ticker = f"{etf_code}.T"
            df_topix = load_price_cached(ticker, period)
            if df_topix.empty:
                continue

            df_topix = df_topix[(df_topix.index >= base_ts) & (df_topix.index <= end_ts)]
            if df_topix.empty:
                continue

            base_price_topix = df_topix["Close"].iloc[0]
            df_topix["Relative Price"] = df_topix["Close"] / base_price_topix

            fig.add_trace(go.Scatter(
                x=df_topix.index,
                y=df_topix["Relative Price"],
                mode="lines",
                line=dict(dash="dot", width=1),
                name=f"TOPIX17 {sector_name}",
                yaxis="y",
                hovertemplate="%{x|%Y-%m-%d}<br>" + sector_name + ": %{y:.2f}x<extra></extra>"
            ))

    # 第二軸:心理指標
    sentiment_colors = {
        "VIX指数": "#FF6B6B",
        "VIX3M": "#FF8C42",
        "VVIX(VIXのボラ)": "#FFA500",
        "ドル指数 DXY": "#4ECDC4",
        "Fear & Greed Index": "#95E1D3",
        "信用スプレッド(HYG-TLT)": "#A8D8EA",
        "ボラティリティ偏り(VIX/VVIX)": "#AA96DA",
        "米10年債利回り": "#A0DE82"
    }
    
    use_sentiment = st.checkbox("💡 投資家心理指標を表示する", value=False)

    if use_sentiment:
        selected_sentiments = st.multiselect(
            "表示する心理指標を選択",
            sentiment_options,
            default=["VIX指数"]
        )
    else:
        selected_sentiments = []

    for name in selected_sentiments:
        if name not in sentiment_data:
            continue
        df = sentiment_data[name]
        color = sentiment_colors.get(name, "#999999")

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["Value"],
            mode="lines",
            line=dict(dash="dash", color=color, width=2),
            name=name,
            yaxis="y2",
            hovertemplate="%{x|%Y-%m-%d}<br>" + name + ": %{y:.2f}<extra></extra>"
        ))

    # Fear & Greed 背景ゾーン
    if "Fear & Greed Index" in selected_sentiments and "Fear & Greed Index" in sentiment_data:
        fig.add_hrect(y0=0, y1=25, fillcolor="blue", opacity=0.1,
                      layer="below", line_width=0, yref="y2",
                      annotation_text="恐怖", annotation_position="top left")
        fig.add_hrect(y0=75, y1=100, fillcolor="red", opacity=0.1,
                      layer="below", line_width=0, yref="y2",
                      annotation_text="強欲", annotation_position="top right")

    # VIX 指数のリスク帯域
    if "VIX指数" in selected_sentiments:
        fig.add_hrect(y0=0, y1=15, fillcolor="green", opacity=0.08,
                      layer="below", line_width=0, yref="y2")
        fig.add_hrect(y0=25, y1=80, fillcolor="red", opacity=0.08,
                      layer="below", line_width=0, yref="y2")

    # ==== レイアウト設定 ====
    fig.update_layout(
        title=f"📊 株価相対比較 ({base_date:%Y-%m-%d} ~ {end_date:%Y-%m-%d}) + 投資家心理指標",
        title_font_size=16,
        hovermode="x unified",
        height=600,
        yaxis=dict(
            title="<b>株価比率(基準日=1.0)</b>",
            title_font_size=11,
            gridcolor="#E8E8E8"
        ),
        yaxis2=dict(
            title="<b>心理指標値</b>",
            title_font_size=11,
            overlaying="y",
            side="right"
        ),
        xaxis=dict(
            title="<b>日付</b>",
            title_font_size=11,
            gridcolor="#E8E8E8"
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="gray",
            borderwidth=1
        ),
        plot_bgcolor="rgba(250, 250, 250, 0.5)",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=80, b=150)
    )

    config = {
        'responsive': True,
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['lasso2d']
    }
    st.plotly_chart(fig, use_container_width=True, config=config)
    # ==== データサマリー ====
    st.markdown("---")
    st.subheader("📈 銘柄パフォーマンス")

    # 業界別平均PERを取得
    sector_avg_per = get_sector_avg_per()

    # テーブル用のデータを準備
    table_data = []

    for ticker, code in zip(tickers, codes):
        if code not in etf_data:
            continue
        df = etf_data[code]
        performance = ((df["Relative Price"].iloc[-1] - 1) * 100)
        base_price = df["Close"].iloc[0]
        end_price = df["Close"].iloc[-1]
        display_name = company_names.get(code, code)

        # PER, PBRを取得
        metrics = get_financial_metrics(ticker)
        per = metrics['PER']
        pbr = metrics['PBR']
        sector = metrics['sector']

        per_str = f"{per:.2f}" if per is not None else "N/A"
        pbr_str = f"{pbr:.2f}" if pbr is not None else "N/A"

        # セクター業界平均を取得
        sector_avg_per_val = sector_avg_per.get(sector, None)
        sector_avg_str = f"{sector_avg_per_val:.2f}" if sector_avg_per_val is not None else "N/A"

        if code.isdigit():
            table_data.append({
                "銘柄": display_name,
                "セクター": sector,
                "始値": f"¥{base_price:,.0f}",
                "終値": f"¥{end_price:,.0f}",
                "変化率": f"{performance:+.2f}%",
                "PER": per_str,
                "業界平均PER": sector_avg_str,
                "PBR": pbr_str
            })
        else:
            table_data.append({
                "銘柄": display_name,
                "セクター": sector,
                "始値": f"${base_price:,.2f}",
                "終値": f"${end_price:,.2f}",
                "変化率": f"{performance:+.2f}%",
                "PER": per_str,
                "業界平均PER": sector_avg_str,
                "PBR": pbr_str
            })

    if table_data:
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)

    # セクターETF情報を表示
    st.markdown("---")
    st.subheader("📊 セクター業界平均PER(ETFベース)")
    st.caption("各セクターの業界平均PERは、以下のセクターETFのPERに基づいています")

    sector_etf_info = [
        ("Technology", "XLK", "テクノロジー企業ETF(米国)"),
        ("Healthcare", "XLV", "ヘルスケア企業ETF(米国)"),
        ("Financials", "XLF", "金融企業ETF(米国)"),
        ("Industrials", "XLI", "産業企業ETF(米国)"),
        ("Energy", "XLE", "エネルギー企業ETF(米国)"),
        ("Consumer Cyclical", "XLY", "消費財企業ETF(米国)"),
        ("Consumer Defensive", "XLP", "生活必需品企業ETF(米国)"),
        ("Real Estate", "XLRE", "不動産企業ETF(米国)"),
        ("Utilities", "XLU", "公共事業企業ETF(米国)"),
        ("Basic Materials", "XLB", "素材企業ETF(米国)"),
    ]

    sector_info_cols = st.columns(5)
    for i, (sector, etf, desc) in enumerate(sector_etf_info):
        with sector_info_cols[i % 5]:
            if sector in sector_avg_per and sector_avg_per[sector] is not None:
                per_val = sector_avg_per[sector]
                st.metric(sector, f"{per_val:.2f}",
                          help=f"{desc}\nETF: {etf}")
            else:
                st.metric(sector, "N/A", help=f"{desc}\nETF: {etf}")

    # 心理指標(最新値)
    st.markdown("---")
    st.subheader("💡 心理指標 (最新値)")

    for name, df in list(sentiment_data.items()):
        latest = df["Value"].iloc[-1]
        st.write(f"**{name}**: {latest:.2f}")
