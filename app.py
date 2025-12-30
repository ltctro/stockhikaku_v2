import streamlit as st

import streamlit as st

if "authed" not in st.session_state:
    st.session_state.authed = False

if not st.session_state.authed:
    pw = st.text_input("パスワードを入力してください", type="password")
    if pw == st.secrets["nrsk"]:
        st.session_state.authed = True
        st.experimental_rerun()
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
from bs4 import BeautifulSoup


st.set_page_config(page_title="株価比較 ＋ 投資家心理指標", layout="wide")

# ==============================
# 💾 DB 設定（market_cache.db に保存）
# ==============================
DB_PATH = "market_cache.db"
STOCKS_CACHE_FILE = "stocks_cache.json"

def fetch_all_stocks():
    """yfinance から上場銘柄リストを取得（初回のみ）"""
    # 日本株 と 米国大型株を取得
    default_stocks = {
        # 日本 - 主要銘柄
        "7203": "トヨタ", "7267": "ホンダ", "7201": "日産", "6502": "東芝", "6758": "ソニー",
        "7974": "任天堂", "6954": "ファナック", "6981": "村田製作所", "6902": "デンソー",
        "9432": "NTT", "9433": "KDDI", "9434": "ソフトバンク", "8306": "日本銀行",
        "8308": "りそな", "8309": "三菱UFJ", "8314": "三井住友FG", "8801": "三井不動産",
        "8802": "三菱地所", "8031": "三井物産", "8058": "三菱商事", "8591": "オリックス",
        "2002": "日清製粉", "2222": "寿スピリッツ", "4503": "アステラス製薬", "4578": "大塚",
        "4661": "オリンパス", "1833": "旭化成", "4183": "三菱ケミカル", "5411": "JFEスチール",
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
    if os.path.exists(STOCKS_CACHE_FILE):
        try:
            with open(STOCKS_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    stocks = fetch_all_stocks()
    with open(STOCKS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)
    return stocks

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS price_cache (ticker TEXT, date TEXT, close REAL, volume REAL, PRIMARY KEY (ticker, date))")
    cur.execute("CREATE TABLE IF NOT EXISTS fear_greed (date TEXT PRIMARY KEY, value INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS ticker_cache (ticker TEXT PRIMARY KEY, name TEXT, cached_at TEXT)")
    
    cur.execute("SELECT COUNT(*) FROM ticker_cache")
    if cur.fetchone()[0] == 0:
        stocks = load_stocks_from_cache()
        ts = datetime.today().isoformat()
        cur.executemany("INSERT OR REPLACE INTO ticker_cache VALUES (?, ?, ?)", [(k, v, ts) for k, v in stocks.items()])
        conn.commit()
    conn.close()

def save_prices(ticker: str, df: pd.DataFrame):
    if df is None or df.empty: return
    conn = sqlite3.connect(DB_PATH)
    rows = [(ticker, idx.strftime("%Y-%m-%d"), float(row['Close']), float(row['Volume'])) for idx, row in df.iterrows()]
    conn.executemany("INSERT OR REPLACE INTO price_cache VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()

def load_prices_from_db(ticker: str, start_date: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT date, close as Close, volume as Volume FROM price_cache WHERE ticker = ? AND date >= ? ORDER BY date", conn, params=(ticker, start_date))
    conn.close()
    if df.empty: return pd.DataFrame()
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date')

def update_price_if_needed(ticker: str, period: str = "1y") -> pd.DataFrame:
    init_db()
    today = datetime.today().date()
    mapping = {"1y": 365, "3y": 1095, "5y": 1825, "10y": 3650, "max": 10000}
    days = mapping.get(period, 365)
    start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    
    local = load_prices_from_db(ticker, start_date)
    if local.empty or local.index.max().date() < today:
        try:
            df_new = yf.Ticker(ticker).history(period=period)
            if df_new is not None and not df_new.empty:
                df_new.index = pd.to_datetime(df_new.index).tz_localize(None)
                save_prices(ticker, df_new)
                return load_prices_from_db(ticker, start_date)
        except:
            pass
    return local

@st.cache_data
def get_company_name(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
        return info.get('longName') or info.get('shortName') or ticker
    except:
        return ticker

@st.cache_data
def get_financial_metrics(ticker: str) -> dict:
    try:
        # 🇯🇵 日本株
        if ticker.endswith(".T"):
            code = ticker.replace(".T","")

            j = requests.get(
                f"https://irbank.net/{code}/metrics.json",
                timeout=10
            ).json()

            return {
                "PER": j.get("PER"),
                "PBR": j.get("PBR"),
                "sector": yf.Ticker(ticker).info.get("sector","Unknown")
            }

        # 🇺🇸 米国株
        info = yf.Ticker(ticker).info
        return {
            "PER": info.get("trailingPE"),
            "PBR": info.get("priceToBook"),
            "sector": info.get("sector","Unknown")
        }

    except:
        return {"PER": None, "PBR": None, "sector": "Unknown"}


def search_tickers(query: str) -> dict:
    query_lower = query.lower().strip()
    if not query_lower: return {}
    results = {}
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT ticker, name FROM ticker_cache WHERE LOWER(ticker) LIKE ? OR LOWER(name) LIKE ? LIMIT 15", 
                           conn, params=(f"%{query_lower}%", f"%{query_lower}%"))
    conn.close()
    for _, row in df.iterrows():
        results[row['ticker']] = row['name']
    return results

def load_fear_greed_cached() -> pd.DataFrame:
    try:
        url = "https://api.alternative.me/fng/?limit=0&format=json"
        res = requests.get(url, timeout=10).json()
        df = pd.DataFrame(res.get("data", []))
        df["date"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
        df["Value"] = df["value"].astype(int)
        return df.set_index('date')[['Value']].sort_index()
    except:
        return pd.DataFrame()

# ============================
# UI部分
# ============================
st.title("📈 株価比較 ＋ 投資家心理指標")

if "selected_tickers" not in st.session_state:
    st.session_state.selected_tickers = []

search_query = st.text_input("銘柄検索 (例: トヨタ, 5020, Apple)")
if search_query:
    results = search_tickers(search_query)
    for symbol, name in results.items():
        if st.button(f"追加: {symbol} - {name}", key=f"add_{symbol}"):
            ticker = f"{symbol}.T" if symbol.isdigit() else symbol
            if ticker not in st.session_state.selected_tickers:
                st.session_state.selected_tickers.append(ticker)
            st.rerun()

if st.session_state.selected_tickers:
    st.write("**選択中:** " + ", ".join(st.session_state.selected_tickers))
    if st.button("選択をクリア"):
        st.session_state.selected_tickers = []
        st.rerun()

# 期間設定
col1, col2, col3 = st.columns(3)
with col1:
    period = st.selectbox("期間", ["1y", "3y", "5y", "10y", "max"], index=0)
with col2:
    base_date = st.date_input("基準日", value=datetime.today() - timedelta(days=365))
with col3:
    end_date = st.date_input("終了日", value=datetime.today())

sentiment_catalog = {"VIX指数": "^VIX", "Fear & Greed Index": "FNG", "米10年債利回り": "^TNX"}
selected_sentiments = st.multiselect("心理指標", list(sentiment_catalog.keys()), default=["VIX指数"])

# データ集計
etf_data = {}
for ticker in st.session_state.selected_tickers:
    df = update_price_if_needed(ticker, period)
    df = df[(df.index >= pd.to_datetime(base_date)) & (df.index <= pd.to_datetime(end_date))]
    if not df.empty:
        df["Relative"] = df["Close"] / df["Close"].iloc[0]
        etf_data[ticker] = df

# 心理指標
sentiment_data = {}
for name in selected_sentiments:
    code = sentiment_catalog[name]
    if code == "FNG":
        df = load_fear_greed_cached()
    else:
        df = update_price_if_needed(code, period)
        if not df.empty: df["Value"] = df["Close"]
    
    if not df.empty:
        sentiment_data[name] = df[(df.index >= pd.to_datetime(base_date)) & (df.index <= pd.to_datetime(end_date))]

# グラフ
if etf_data or sentiment_data:
    fig = go.Figure()
    for t, df in etf_data.items():
        fig.add_trace(go.Scatter(x=df.index, y=df["Relative"], name=t, yaxis="y1"))
    
    for n, df in sentiment_data.items():
        fig.add_trace(go.Scatter(x=df.index, y=df["Value"], name=n, yaxis="y2", line=dict(dash='dot')))

    fig.update_layout(
        yaxis=dict(title="相対株価"),
        yaxis2=dict(title="心理指標", overlaying="y", side="right"),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

# 指標テーブル
if etf_data:
    st.subheader("📊 財務指標まとめ")
    metrics_list = []
    for t in st.session_state.selected_tickers:
        m = get_financial_metrics(t)
        df = etf_data.get(t)
        perf = f"{(df['Relative'].iloc[-1]-1)*100:+.2f}%" if df is not None else "N/A"
        metrics_list.append({
            "銘柄": t,
            "セクター": m['sector'],
            "PER": m['PER'],
            "PBR": m['PBR'],
            "期間騰落率": perf
        })
    st.table(metrics_list)

