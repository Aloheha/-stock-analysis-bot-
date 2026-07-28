import os
from flask import Flask
import schedule
import threading
import time
from datetime import datetime
import requests
import yfinance as yf

app = Flask(__name__)

# ===================== Config =====================
LINE_TOKEN = "YOUR_LINE_CHANNEL_ACCESS_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# ===================== Send Line =====================
def send_line(message):
    """ส่งข้อความไป Line"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": CHAT_ID,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("✅ ส่ง Line สำเร็จ!")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# ===================== Analyze Stock =====================
def analyze_stock(symbol, market='SET'):
    """วิเคราะห์หุ้น"""
    try:
        if market == 'SET':
            full_symbol = f"{symbol}.BK"
        else:
            full_symbol = symbol
        
        data = yf.download(full_symbol, period='100d', progress=False)
        
        if data.empty:
            return None
        
        current_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        sma20 = data['Close'].rolling(20).mean().iloc[-1]
        sma50 = data['Close'].rolling(50).mean().iloc[-1]
        sma200 = data['Close'].rolling(200).mean().iloc[-1]
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]
        
        ema12 = data['Close'].ewm(span=12).mean()
        ema26 = data['Close'].ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        macd_val = macd.iloc[-1]
        
        if sma20 > sma50 > sma200:
            trend = "⬆️ UPTREND"
        elif sma20 < sma50 < sma200:
            trend = "⬇️ DOWNTREND"
        else:
            trend = "➡️ SIDEWAYS"
        
        support = data['Low'].tail(20).min()
        resistance = data['High'].tail(20).max()
        
        avg_vol = data['Volume'].tail(20).mean()
        current_vol = data['Volume'].iloc[-1]
        vol_ratio = current_vol / avg_vol
        
        if vol_ratio > 1.5:
            volume_signal = "🔴 Very High"
        elif vol_ratio > 1.2:
            volume_signal = "🟠 High"
        else:
            volume_signal = "🟡 Normal"
        
        return {
            'symbol': symbol,
            'market': market,
            'price': round(current_price, 2),
            'change': round(change_pct, 2),
            'trend': trend,
            'sma20': round(sma20, 2),
            'sma50': round(sma50, 2),
            'sma200': round(sma200, 2),
            'rsi': round(rsi_val, 2),
            'macd': round(macd_val, 3),
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'volume': volume_signal,
        }
    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {str(e)}")
        return None

# ===================== Generate Report =====================
def generate_report():
    """สร้างรายงานและส่ง Line"""
    
    print(f"\n{'='*60}")
    print(f"📊 Report at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    set_stocks = ['DELTA', 'HANA', 'PTT', 'CPALL', 'SCC']
    sp_stocks = ['NVDA', 'MSFT', 'AAPL', 'AMZN', 'GOOG']
    
    report = f"""
📊 Daily Stock Analysis
{datetime.now().strftime('%Y-%m-%d %H:%M')}

🇹🇭 SET100:
"""
    
    for stock in set_stocks:
        result = analyze_stock(stock, 'SET')
        if result:
            report += f"""
{result['symbol']}: ฿{result['price']} ({result['change']:+.1f}%)
  Trend: {result['trend']} | RSI: {result['rsi']} | MACD: {result['macd']}
  SMA: {result['sma20']}/{result['sma50']}/{result['sma200']}
  S/R: ฿{result['support']}/฿{result['resistance']}
  Vol: {result['volume']}
"""
    
    report += "\n🇺🇸 S&P500:\n"
    
    for stock in sp_stocks:
        result = analyze_stock(stock, 'US')
        if result:
            report += f"""
{result['symbol']}: ${result['price']} ({result['change']:+.1f}%)
  Trend: {result['trend']} | RSI: {result['rsi']} | MACD: {result['macd']}
  SMA: {result['sma20']}/{result['sma50']}/{result['sma200']}
  S/R: ${result['support']}/{result['resistance']}
  Vol: {result['volume']}
"""
    
    report += "\n✅ Report sent!"
    
    print(report)
    send_line(report)

# ===================== Schedule =====================
def run_scheduler():
    """รัน Scheduler"""
    schedule.every().day.at("07:30").do(generate_report)
    schedule.every().day.at("09:30").do(generate_report)
    
    print("⏰ Scheduler started!")
    print("📅 Tasks: 07:30 AM & 09:30 AM\n")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# ===================== Flask Routes =====================
@app.route('/')
def home():
    return '<h1>📊 Stock Analysis Bot</h1><p>Status: ✅ Running</p>', 200

@app.route('/run', methods=['GET'])
def run_now():
    generate_report()
    return "✅ Report sent!", 200

# ===================== Main =====================
if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
