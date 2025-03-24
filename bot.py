import requests
import time
import threading
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = '7691730618:AAEI4pRNuVj4ImwALThbxg0PTfIIhVqfK40'
API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/'
CHAT_ID = '@SufianOdeh'

FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSfF1TIpFc8ih6QyZfbQ5rFVoQOMLtQogPlmrRDL8quPUnX2iQ/formResponse'
ENTRY_IDS = {
    'coin': 'entry.1509386362',
    'type': 'entry.1332060171',
    'price': 'entry.1397094650'
}

TARGETS = {
    'SOL': {
        'buy': 134.0,
        'take_profit': 150.0,
        'stop_loss': 120.0
    },
    'ADA': {
        'buy': 0.5800,
        'take_profit': 0.7380,
        'stop_loss': 0.6700
    }
}

status = {
    'SOL': {'buy_alerted': False, 'tp_alerted': False, 'sl_alerted': False},
    'ADA': {'buy_alerted': False, 'tp_alerted': False, 'sl_alerted': False}
}

hourly_active = True

def get_price(symbol):
    try:
        symbol_map = {
            'SOL': 'solana',
            'ADA': 'cardano'
        }
        coin_id = symbol_map.get(symbol.upper())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data[coin_id]['usd'])
        else:
            print(f"[ERROR] CoinGecko API status: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] CoinGecko Exception: {e}")
        return None

def send_message(chat_id, text):
    url = API_URL + 'sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, data=payload)

def send_alert(text):
    url = API_URL + 'sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': text}
    requests.post(url, data=payload)

def submit_to_form(symbol, price, alert_type):
    data = {
        ENTRY_IDS['coin']: symbol,
        ENTRY_IDS['type']: alert_type,
        ENTRY_IDS['price']: price
    }
    requests.post(FORM_URL, data=data)

def monitor_prices():
    while True:
        for symbol in TARGETS:
            price = get_price(symbol)
            if price is None:
                continue

            levels = TARGETS[symbol]
            s = status[symbol]

            if not s['buy_alerted'] and price <= levels['buy']:
                send_alert(f'🔵 {symbol} وصلت لنقطة الشراء: {price}$')
                submit_to_form(symbol, price, 'شراء')
                s['buy_alerted'] = True

            if not s['tp_alerted'] and price >= levels['take_profit']:
                send_alert(f'💰 {symbol} وصلت لهدف الربح: {price}$')
                submit_to_form(symbol, price, 'هدف')
                s['tp_alerted'] = True

            if not s['sl_alerted'] and price <= levels['stop_loss']:
                send_alert(f'⛔️ {symbol} ضربت وقف الخسارة: {price}$')
                submit_to_form(symbol, price, 'خسارة')
                s['sl_alerted'] = True

        time.sleep(30)

def hourly_report():
    global hourly_active
    while True:
        if hourly_active:
            now = datetime.now().strftime('%H:%M')
            report = f"🕐 تقرير الساعة {now}\n\n"
            for symbol in TARGETS:
                price = get_price(symbol)
                if price:
                    entry = TARGETS[symbol]['buy']
                    diff = round(price - entry, 4)
                    report += f"🔹 {symbol}: {price}$\n- دخول: {entry}$\n- فرق: {'+' if diff >= 0 else ''}{diff}$\n\n"
            send_alert(report)
        time.sleep(3600)

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def telegram_webhook():
    global hourly_active
    data = request.get_json()
    message = data.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')

    if text.lower() == '/status':
        reply = ''
        for symbol in TARGETS:
            current = get_price(symbol)
            levels = TARGETS[symbol]
            reply += f"{symbol} السعر الحالي: {current}$\n"
            reply += f"- دخول: {levels['buy']}$\n- هدف: {levels['take_profit']}$\n- وقف خسارة: {levels['stop_loss']}$\n\n"
            submit_to_form(symbol, current, 'STATUS')
        send_message(chat_id, reply)
    elif text.lower() == '/start':
        send_message(chat_id, "👋 تم تفعيل التنبيهات لـ SOL و ADA، اكتب /status لأي تحديثات")
    elif text.lower() == '/hourly_on':
        hourly_active = True
        send_message(chat_id, "✅ تم تفعيل التقرير التلقائي كل ساعة")
    elif text.lower() == '/hourly_off':
        hourly_active = False
        send_message(chat_id, "⛔️ تم إيقاف التقرير التلقائي")
    else:
        send_message(chat_id, "❓ أمر غير معروف. جرب /status أو /start أو /hourly_on أو /hourly_off")

    return {'ok': True}

if __name__ == '__main__':
    threading.Thread(target=monitor_prices).start()
    threading.Thread(target=hourly_report).start()
    app.run(host='0.0.0.0', port=5000)
