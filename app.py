import os
from flask import Flask
import schedule
import threading
import time
from datetime import datetime
import requests


app = Flask(__name__)

# ===================== Config =====================
LINE_TOKEN = "BPcmBZEV3nR2ZKYyRlQfXQ1rHCokbTfRNJt/bWx4CrxzmgLuExbmgMaMR2Pxe1A0KAy7ePwYjeoJKkRbd1H5LkaA4LdPbLHDFAIXBXc/UPB2Bj89AWcbE2a2vyb+hxRKbhlTFh7ACCxe9JPc4BlyIgdB04t89/1O/w1cDnyilFU="
USER_ID = "Uf67badb4167a1b100e7c402099bef0a7"

# ===================== Send Line =====================
def send_line(message):
    """ส่งข้อความไป Line"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": USER_ID,
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
    report += "\n🇺🇸 S&P500:\n"   
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
