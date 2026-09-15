from flask import Flask, render_template, jsonify
import os
from dotenv import load_dotenv
import random
from datetime import datetime
from collections import defaultdict
import threading
import time

load_dotenv()

app = Flask(__name__)

CONFIG = {
    'initial_capital': 1000,
    'tp_percent': 3,
    'sl_percent': 1,
    'max_positions': 5,
    'risk_per_trade': 0.02,
}

trading_state = {
    'balance': 1000,
    'initial_balance': 1000,
    'is_trading': False,
    'total_trades': 0,
    'winning_trades': 0,
    'losing_trades': 0,
    'total_profit': 0,
    'open_positions': [],
    'closed_trades': [],
    'win_rate': 0,
    'balance_history': [1000],
    'daily_profit': defaultdict(float),
    'last_update': datetime.now().isoformat(),
}

def simulate_trade():
    """Simulate a trade"""
    try:
        if not trading_state['is_trading']:
            return
        
        if len(trading_state['open_positions']) >= CONFIG['max_positions']:
            return
        
        balance = trading_state['balance']
        risk_amount = balance * CONFIG['risk_per_trade']
        
        # 65% win rate
        is_win = random.random() < 0.65
        
        if is_win:
            profit = risk_amount * 3  # 3% profit
            trading_state['winning_trades'] += 1
            status = '✅ WIN'
        else:
            profit = -risk_amount  # 1% loss
            trading_state['losing_trades'] += 1
            status = '❌ LOSS'
        
        trade = {
            'id': trading_state['total_trades'] + 1,
            'symbol': random.choice(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']),
            'type': random.choice(['BUY', 'SELL']),
            'entry_price': round(random.uniform(100, 50000), 2),
            'tp_price': round(random.uniform(100, 50000), 2),
            'sl_price': round(random.uniform(100, 50000), 2),
            'exit_price': round(random.uniform(100, 50000), 2),
            'profit': round(profit, 2),
            'time': datetime.now().isoformat(),
            'status': status,
            'exit_reason': 'TP Hit (+3%)' if is_win else 'SL Hit (-1%)'
        }
        
        trading_state['closed_trades'].append(trade)
        trading_state['total_profit'] += profit
        trading_state['balance'] += profit
        trading_state['balance_history'].append(round(trading_state['balance'], 2))
        trading_state['total_trades'] += 1
        
        if trading_state['total_trades'] > 0:
            trading_state['win_rate'] = round((trading_state['winning_trades'] / trading_state['total_trades'] * 100), 1)
        
        trading_state['last_update'] = datetime.now().isoformat()
        
    except Exception as e:
        print(f"Trade error: {e}")

def auto_trading_loop():
    """Auto trading background loop"""
    while True:
        try:
            simulate_trade()
            time.sleep(2)
        except:
            time.sleep(2)

# Start trading thread
trading_thread = threading.Thread(target=auto_trading_loop, daemon=True)
trading_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/trading/start', methods=['POST'])
def start():
    trading_state['is_trading'] = True
    return jsonify({'status': '✅ Trading Started', 'is_trading': True})

@app.route('/api/trading/stop', methods=['POST'])
def stop():
    trading_state['is_trading'] = False
    return jsonify({'status': '⏹️ Trading Stopped', 'is_trading': False})

@app.route('/api/stats', methods=['GET'])
def stats():
    profit_pct = ((trading_state['balance'] - trading_state['initial_balance']) / trading_state['initial_balance'] * 100) if trading_state['initial_balance'] > 0 else 0
    return jsonify({
        'balance': round(trading_state['balance'], 2),
        'initial_balance': trading_state['initial_balance'],
        'total_trades': trading_state['total_trades'],
        'winning_trades': trading_state['winning_trades'],
        'losing_trades': trading_state['losing_trades'],
        'win_rate': trading_state['win_rate'],
        'total_profit': round(trading_state['total_profit'], 2),
        'profit_percent': round(profit_pct, 2),
        'open_positions': len(trading_state['open_positions']),
        'max_positions': CONFIG['max_positions'],
        'is_trading': trading_state['is_trading'],
        'last_update': trading_state['last_update'],
        'balance_history': trading_state['balance_history'][-100:],
    })

@app.route('/api/positions', methods=['GET'])
def positions():
    return jsonify({
        'open_positions': trading_state['open_positions'],
        'closed_trades': trading_state['closed_trades'][-50:],
    })

@app.route('/api/reset', methods=['POST'])
def reset():
    global trading_state
    trading_state = {
        'balance': 1000,
        'initial_balance': 1000,
        'is_trading': False,
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'total_profit': 0,
        'open_positions': [],
        'closed_trades': [],
        'win_rate': 0,
        'balance_history': [1000],
        'daily_profit': defaultdict(float),
        'last_update': datetime.now().isoformat(),
    }
    return jsonify({'status': '🔄 Reset successful'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
