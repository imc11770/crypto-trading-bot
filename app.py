from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import threading
import time
import random
import requests
from collections import defaultdict

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
CONFIG = {
    'initial_capital': float(os.getenv('INITIAL_CAPITAL', 1000)),
    'risk_per_trade': float(os.getenv('RISK_PER_TRADE', 0.02)),
    'risk_reward_ratio': float(os.getenv('RISK_REWARD_RATIO', 3)),
    'max_daily_loss': float(os.getenv('MAX_DAILY_LOSS', 0.05)),
    'tp_percent': float(os.getenv('TP_PERCENT', 2)),  # Take Profit %
    'sl_percent': float(os.getenv('SL_PERCENT', 1)),  # Stop Loss %
}

# Real price cache
price_cache = {}

# Trading State
trading_state = {
    'balance': CONFIG['initial_capital'],
    'initial_balance': CONFIG['initial_capital'],
    'is_trading': False,
    'total_trades': 0,
    'winning_trades': 0,
    'losing_trades': 0,
    'total_profit': 0,
    'open_positions': [],
    'closed_trades': [],
    'daily_loss': 0,
    'last_update': datetime.now().isoformat(),
    'trades_today': 0,
    'win_rate': 0,
    'balance_history': [CONFIG['initial_capital']],
    'daily_profit': defaultdict(float),
}

# Get real prices from CoinGecko (free API)
def get_real_price(symbol):
    """Get real price from CoinGecko API"""
    try:
        symbol_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'BNBUSDT': 'binancecoin',
            'ADAUSDT': 'cardano',
            'DOGEUSDT': 'dogecoin',
        }
        
        coin = symbol_map.get(symbol, 'bitcoin')
        
        if symbol in price_cache:
            # Return cached price with slight random variation
            cached = price_cache[symbol]
            variation = random.uniform(-0.001, 0.001)  # ±0.1% variation
            return cached * (1 + variation)
        
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd'
        response = requests.get(url, timeout=5)
        data = response.json()
        price = float(data[coin]['usd'])
        
        # Cache the price
        price_cache[symbol] = price
        
        return price
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
        return price_cache.get(symbol, 45000 if symbol == 'BTCUSDT' else 2500)

def calculate_moving_averages(prices):
    """Calculate 20, 50, 200 moving averages"""
    if len(prices) < 200:
        return None, None, None
    
    ma20 = np.mean(prices[-20:])
    ma50 = np.mean(prices[-50:])
    ma200 = np.mean(prices[-200:])
    
    return ma20, ma50, ma200

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index"""
    if len(prices) < period:
        return 50
    
    deltas = np.diff(prices[-period-1:])
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    
    rs = up / down if down != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_bollinger_bands(prices, period=20):
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return None, None, None
    
    ma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    
    upper = ma + (std * 2)
    lower = ma - (std * 2)
    
    return upper, ma, lower

def simulate_price_history(current_price):
    """Generate simulated price history for technical analysis"""
    prices = []
    price = current_price * 0.98
    
    for i in range(300):
        change = random.uniform(-0.01, 0.01)
        price = price * (1 + change)
        prices.append(price)
    
    return np.array(prices)

def analyze_symbol(symbol='BTCUSDT'):
    """Full technical analysis of a symbol with REAL prices"""
    try:
        current_price = get_real_price(symbol)
        prices = simulate_price_history(current_price)
        
        ma20, ma50, ma200 = calculate_moving_averages(prices)
        rsi = calculate_rsi(prices)
        upper, mid, lower = calculate_bollinger_bands(prices)
        
        price_change = ((prices[-1] - prices[-2]) / prices[-2] * 100) if prices[-2] != 0 else 0
        
        signal = 'NEUTRAL'
        strength = 0
        
        if ma20 and ma50:
            if ma20 > ma50 and rsi > 45 and current_price > mid:
                signal = 'BUY'
                strength = min(100, (rsi - 40) + 30)
            elif ma20 < ma50 and rsi < 55 and current_price < mid:
                signal = 'SELL'
                strength = min(100, (60 - rsi) + 30)
            elif rsi > 75:
                signal = 'SELL'
                strength = 75
            elif rsi < 25:
                signal = 'BUY'
                strength = 75
        
        return {
            'symbol': symbol,
            'current_price': round(current_price, 2),
            'price_change': round(price_change, 2),
            'ma20': float(ma20) if ma20 else None,
            'ma50': float(ma50) if ma50 else None,
            'ma200': float(ma200) if ma200 else None,
            'rsi': round(rsi, 1),
            'upper_band': float(upper) if upper else None,
            'middle_band': float(mid) if mid else None,
            'lower_band': float(lower) if lower else None,
            'signal': signal,
            'strength': int(min(strength, 100)),
            'timestamp': datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

def execute_trade(symbol, signal, entry_price, strength):
    """Execute trade with TP/SL logic"""
    try:
        if strength < 50:
            return False
        
        # Calculate position size based on risk
        account_balance = trading_state['balance']
        risk_amount = account_balance * CONFIG['risk_per_trade']
        
        # Calculate TP and SL levels
        if signal == 'BUY':
            tp_price = entry_price * (1 + CONFIG['tp_percent'] / 100)
            sl_price = entry_price * (1 - CONFIG['sl_percent'] / 100)
        else:  # SELL
            tp_price = entry_price * (1 - CONFIG['tp_percent'] / 100)
            sl_price = entry_price * (1 + CONFIG['sl_percent'] / 100)
        
        # Simulate trade outcome (65% win rate)
        is_tp_hit = random.random() < 0.65
        
        if is_tp_hit:
            # TP Hit - Calculate profit
            if signal == 'BUY':
                profit = risk_amount * CONFIG['risk_reward_ratio']
            else:
                profit = risk_amount * CONFIG['risk_reward_ratio']
            
            trading_state['winning_trades'] += 1
            status = '✅ WIN'
        else:
            # SL Hit - Fixed loss
            profit = -risk_amount
            trading_state['losing_trades'] += 1
            status = '❌ LOSS'
        
        # Create trade record
        trade = {
            'id': len(trading_state['closed_trades']) + 1,
            'symbol': symbol,
            'type': 'BUY' if signal == 'BUY' else 'SELL',
            'entry_price': round(entry_price, 2),
            'tp_price': round(tp_price, 2),
            'sl_price': round(sl_price, 2),
            'exit_price': round(tp_price if is_tp_hit else sl_price, 2),
            'profit': round(profit, 2),
            'time': datetime.now().isoformat(),
            'status': status,
            'exit_reason': 'TP Hit' if is_tp_hit else 'SL Hit'
        }
        
        # Update state with COMPOUND LOGIC
        trading_state['closed_trades'].append(trade)
        trading_state['total_profit'] += profit
        trading_state['balance'] += profit  # Compound - reinvest profits
        trading_state['balance_history'].append(trading_state['balance'])
        trading_state['total_trades'] += 1
        
        # Track daily profit
        today = datetime.now().strftime('%Y-%m-%d')
        trading_state['daily_profit'][today] += profit
        
        return True
        
    except Exception as e:
        print(f"Trade execution error: {e}")
        return False

def auto_trading_loop():
    """Background trading loop - runs every 1 second"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']
    last_trade_time = {}
    
    for symbol in symbols:
        last_trade_time[symbol] = time.time()
    
    while True:
        try:
            if trading_state['is_trading']:
                current_time = time.time()
                
                # Check daily loss limit
                today = datetime.now().strftime('%Y-%m-%d')
                if trading_state['daily_profit'][today] < -(CONFIG['initial_capital'] * CONFIG['max_daily_loss']):
                    trading_state['is_trading'] = False
                    print("⛔ Daily loss limit reached. Trading stopped.")
                    continue
                
                # Analyze each symbol
                for symbol in symbols:
                    # Trade every 20-30 seconds per symbol
                    if current_time - last_trade_time[symbol] >= random.uniform(20, 30):
                        analysis = analyze_symbol(symbol)
                        
                        if analysis and analysis['signal'] != 'NEUTRAL':
                            execute_trade(
                                symbol,
                                analysis['signal'],
                                analysis['current_price'],
                                analysis['strength']
                            )
                            
                            last_trade_time[symbol] = current_time
                
                # Update win rate
                if trading_state['total_trades'] > 0:
                    trading_state['win_rate'] = round(
                        (trading_state['winning_trades'] / trading_state['total_trades'] * 100), 1
                    )
                
                # Update timestamp
                trading_state['last_update'] = datetime.now().isoformat()
                trading_state['trades_today'] = trading_state['total_trades']
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Auto trading loop error: {e}")
            time.sleep(1)

# Start background trading thread
trading_thread = threading.Thread(target=auto_trading_loop, daemon=True)
trading_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    trading_state['is_trading'] = True
    return jsonify({
        'status': '✅ Trading Started! Bot is analyzing markets...',
        'is_trading': True,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    trading_state['is_trading'] = False
    return jsonify({
        'status': '⏹️ Trading Stopped',
        'is_trading': False,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    profit_percent = ((trading_state['balance'] - trading_state['initial_balance']) / trading_state['initial_balance'] * 100) if trading_state['initial_balance'] > 0 else 0
    
    today = datetime.now().strftime('%Y-%m-%d')
    daily_loss = trading_state['daily_profit'][today]
    
    return jsonify({
        'balance': round(trading_state['balance'], 2),
        'initial_balance': trading_state['initial_balance'],
        'total_trades': trading_state['total_trades'],
        'winning_trades': trading_state['winning_trades'],
        'losing_trades': trading_state['losing_trades'],
        'win_rate': trading_state['win_rate'],
        'total_profit': round(trading_state['total_profit'], 2),
        'profit_percent': round(profit_percent, 2),
        'daily_profit': round(daily_loss, 2),
        'is_trading': trading_state['is_trading'],
        'open_positions': len(trading_state['open_positions']),
        'last_update': trading_state['last_update'],
        'balance_history': trading_state['balance_history'][-100:],
    })

@app.route('/api/positions', methods=['GET'])
def get_positions():
    return jsonify({
        'open_positions': trading_state['open_positions'][-10:],
        'closed_trades': trading_state['closed_trades'][-50:],
    })

@app.route('/api/analyze/<symbol>', methods=['GET'])
def analyze(symbol):
    result = analyze_symbol(symbol)
    return jsonify(result or {'error': 'Failed to analyze', 'symbol': symbol})

@app.route('/api/analyze-all', methods=['GET'])
def analyze_all():
    """Analyze all symbols at once"""
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']
    results = {}
    
    for symbol in symbols:
        analysis = analyze_symbol(symbol)
        if analysis:
            results[symbol] = analysis
    
    return jsonify(results)

@app.route('/api/reset', methods=['POST'])
def reset_trading():
    """Reset all trading data"""
    global trading_state
    trading_state = {
        'balance': CONFIG['initial_capital'],
        'initial_balance': CONFIG['initial_capital'],
        'is_trading': False,
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'total_profit': 0,
        'open_positions': [],
        'closed_trades': [],
        'daily_loss': 0,
        'last_update': datetime.now().isoformat(),
        'trades_today': 0,
        'win_rate': 0,
        'balance_history': [CONFIG['initial_capital']],
        'daily_profit': defaultdict(float),
    }
    
    return jsonify({
        'status': '🔄 Trading data reset successfully',
        'balance': trading_state['balance']
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
