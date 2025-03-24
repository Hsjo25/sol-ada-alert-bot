import requests
import time
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
CHAT_ID = '@SufianOdeh'
API_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/'

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

def get_price(symbol):
    try:
        url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT'
        response = requests.get(url)
        data = response.json()
        return float(data['price'])
    except:
        return None

def send_message(text):
    url = API_URL + 'sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': text}
    requests.post(url, data=payload)

def monitor_prices():
    while True:
        for symbol in TARGETS:
            price = get_price(symbol)
            if price is None:
                continue

            levels = TARGETS[symbol]
            s = status[symbol]

            if not s['buy_alerted'] and price <= levels['buy']:
                send_message(f'🔵 {symbol} وصلت لنقطة الشراء: {price}$')
                s['buy_alerted'] = True

            if not s['tp_alerted'] and price >= levels['take_profit']:
                send_message(f'💰 {symbol} وصلت لهدف الربح: {price}$')
                s['tp_alerted'] = True

            if not s['sl_alerted'] and price <= levels['stop_loss']:
                send_message(f'⛔️ {symbol} ضربت وقف الخسارة: {price}$')
                s['sl_alerted'] = True

        time.sleep(30)

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def telegram_webhook():
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
        send_message(reply)
    elif text.lower() == '/start':
        send_message("👋 تم تفعيل التنبيهات لـ SOL و ADA، اكتب /status لأي تحديثات")
    else:
        send_message("❓ أمر غير معروف. جرب /status أو /start")

    return {'ok': True}

if __name__ == '__main__':
    import threading
    threading.Thread(target=monitor_prices).start()
    app.run(host='0.0.0.0', port=5000)
