import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit as st

# --- Binance API base URLs (with fallback) ---
base_urls = [
    "https://data.binance.com",
    "https://api.binance.us"
]

# --- Forecast data ---
def get_forecasts():
    return {
        'BTCUSDT': 0.8, 'ETHUSDT': 0.6, 'BNBUSDT': 0.4,
        'SOLUSDT': 0.5, 'ADAUSDT': 0.3, 'XRPUSDT': 0.35,
        'DOGEUSDT': 0.2, 'AVAXUSDT': 0.25, 'TRXUSDT': 0.3, 'DOTUSDT': 0.28
    }

# --- Get daily kline data ---
def get_daily_data(symbol):
    for base_url in base_urls:
        try:
            url = f"{base_url}/api/v3/klines"
            params = {'symbol': symbol, 'interval': '1d', 'limit': 2}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            if len(data) < 2:
                continue
            y_open = float(data[0][1])
            y_close = float(data[1][4])
            y_open_time = datetime.fromtimestamp(data[1][0]/1000, tz=timezone.utc).strftime('%Y-%m-%d')
            return y_open_time, y_open, y_close
        except Exception as e:
            print(f"⚠️ {base_url} failed for {symbol}: {e}")
            continue
    raise ValueError(f"All base URLs failed for {symbol}")

# --- Constants ---
BUY_THRESHOLD = 0.5
SELL_THRESHOLD = -0.5
INVESTMENT = 100.0  # USDT

# --- Streamlit UI ---
st.set_page_config(page_title="Crypto Daily Trade Plan", layout="centered")
st.title("📈 Daily Crypto Trade Plan (UTC)")

symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
           "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "TRXUSDT", "DOTUSDT"]
forecasts = get_forecasts()
records = []

for symbol in symbols:
    try:
        date, y_open, y_close = get_daily_data(symbol)
        trade_time = (
            datetime.fromisoformat(date)
            .replace(tzinfo=timezone.utc) + timedelta(days=1)
        ).strftime('%Y-%m-%d %I:%M %p UTC')
    except Exception as e:
        st.warning(f"⚠️ Skip {symbol}: {e}")
        continue

    mom = ((y_close - y_open) / y_open) * 100
    f = forecasts.get(symbol, 0)
    score = mom + 0.5 * f

    if score >= BUY_THRESHOLD:
        advice = "Buy"
        entry = y_close
        target = entry * (1 + score / 100)
        stop = entry * (1 - score / 100)
        units = INVESTMENT / entry
        profit = (target - entry) * units
    elif score <= SELL_THRESHOLD:
        advice = "Sell"
        entry = y_close
        target = entry * (1 - abs(score) / 100)
        stop = entry * (1 + abs(score) / 100)
        units = INVESTMENT / entry
        profit = (entry - target) * units
    else:
        advice = "Hold"
        entry = target = stop = units = profit = None

    records.append({
        'Symbol': symbol,
        'Date': date,
        'Trade Time': trade_time,
        'Entry Price': round(entry, 4) if entry else '',
        'Target': round(target, 4) if target else '',
        'Stop-Loss': round(stop, 4) if stop else '',
        'Score(%)': round(score, 2),
        'Advice': advice,
        'Investment (USDT)': INVESTMENT if advice != "Hold" else '',
        'Estimated Profit (USDT)': round(profit, 2) if profit else ''
    })

# --- Display results ---
df = pd.DataFrame(records).sort_values('Score(%)', ascending=False).reset_index(drop=True)
st.dataframe(df)

# --- Donation Section ---
st.markdown("---")
st.markdown("## 💖 Crypto Donations Welcome")
st.markdown("""
If this app helped you, consider donating:

- **BTC:** `bc1qlaact2ldakvwqa7l9xd3lhp4ggrvezs0npklte`
- **TRX / USDT (TRC20):** `TBMrjoyxAuKTxBxPtaWB6uc9U5PX4JMfFu`

You can also scan the QR code below 👇
""")
try:
    st.image("eth_qr.png", width=180, caption="ETH / USDT QR")
except:
    st.warning("⚠️ eth_qr.png not found. Add it to your project folder to display donation QR.")
