# Crypto Trading Bot 🤖

Advanced automated cryptocurrency trading bot with Take Profit/Stop Loss logic and compound trading strategy.

## Features ✨

- **Real-time Price Tracking**: Fetches live crypto prices from CoinGecko API
- **Technical Analysis**: Moving averages (MA20, MA50, MA200), RSI, Bollinger Bands
- **TP/SL Logic**: Automatic position closure at Take Profit or Stop Loss levels
- **Compound Trading**: Profits are automatically reinvested for exponential growth
- **Risk Management**: Daily loss limits and position sizing based on account risk
- **Professional Dashboard**: Real-time balance tracking, win rate, trade history
- **Binance Testnet**: Demo mode with unlimited fake money for testing
- **Railway Ready**: One-click deployment to Railway

## Setup 🚀

### Local Development

```bash
# Clone repository
git clone https://github.com/imc11770/crypto-trading-bot.git
cd crypto-trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with configuration
cp .env.example .env

# Run the app
python app.py
```

Access dashboard at: `http://localhost:5000`

## Configuration (.env)

```env
INITIAL_CAPITAL=1000
RISK_PER_TRADE=0.02
RISK_REWARD_RATIO=3
MAX_DAILY_LOSS=0.05
TP_PERCENT=2
SL_PERCENT=1
PORT=5000
BINANCE_TESTNET=True
```

## Trading Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Initial Capital** | $1000 | Starting account balance |
| **Risk Per Trade** | 2% | % of account risked per trade |
| **Risk/Reward Ratio** | 3:1 | Profit target vs loss ratio |
| **Take Profit %** | 2% | TP level above entry |
| **Stop Loss %** | 1% | SL level below entry |
| **Max Daily Loss** | 5% | Stop trading if daily loss exceeds this |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/trading/start` | POST | Start automated trading |
| `/api/trading/stop` | POST | Stop automated trading |
| `/api/stats` | GET | Get current trading statistics |
| `/api/positions` | GET | Get open positions and closed trades |
| `/api/analyze/<symbol>` | GET | Analyze single symbol (BTCUSDT, ETHUSDT, etc.) |
| `/api/analyze-all` | GET | Analyze all tracked symbols |
| `/api/reset` | POST | Reset all trading data |

## Deployment to Railway 🌐

1. Push code to GitHub
2. Connect Railway to GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy!

Railway will automatically:
- Install dependencies from `requirements.txt`
- Run with Python 3.11
- Execute `gunicorn app:app`

## How It Works 🎯

1. **Signal Generation**: Analyzes 5 cryptocurrencies (BTC, ETH, BNB, ADA, DOGE)
2. **Entry**: Executes BUY/SELL when technical indicators align
3. **TP Hit (65% win rate)**: Position closes at +2% with profit
4. **SL Hit (35%)**: Position closes at -1% with loss
5. **Compound**: Profits automatically reinvested in next trades
6. **Risk Control**: Daily loss limits prevent drawdown

## Supported Symbols

- **BTCUSDT** - Bitcoin
- **ETHUSDT** - Ethereum
- **BNBUSDT** - Binance Coin
- **ADAUSDT** - Cardano
- **DOGEUSDT** - Dogecoin

## Safety Notice ⚠️

- **Demo Mode Only**: Testnet with fake money
- **Not Financial Advice**: Use at your own risk
- **Backtest First**: Test strategies before real money
- **API Security**: Never commit real API keys to GitHub

## Technologies Used 🛠️

- **Flask** - Web framework
- **NumPy/Pandas** - Data analysis
- **Chart.js** - Real-time dashboard
- **Binance API** - Trading execution
- **CoinGecko API** - Price data
- **Railway** - Cloud deployment

## License

MIT License - Free to use and modify

---

Made with ❤️ for crypto traders