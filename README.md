# 🚀 Binance Trading Bot

Bot trading crypto tự động điều khiển qua Telegram, chạy 24/7 với Docker + MySQL.

Hệ thống đã hoàn thiện:

* Scanner thị trường
* Signal tracking
* Paper trading full flow (TP1 + trailing)
* Risk management
* Env toggle test / prod
* Live trading engine (SAFE MODE)

---

# 📦 Features

## 🔍 Market Scanner

* Scan thị trường theo chu kỳ
* Lọc coin theo:

  * price change 5m
  * quote volume
  * volume spike
* Gửi alert Telegram
* Lưu signal vào database

---

## 📊 Signal Tracking

* Theo dõi sau:

  * 5 phút
  * 15 phút
* Tính:

  * win / lose / draw
  * max profit
  * max drawdown

---

## 🧪 Paper Trading

* LONG / SHORT
* Entry / SL / TP1 / TP2
* TP1 partial close (50%)
* Trailing stop
* TP2 / SL / TSL close
* Multi trade
* Duplicate guard

---

## 🛡 Risk Management

* Risk theo % vốn
* Position size
* Max open trades
* Max notional
* Daily loss breaker
* KILL_SWITCH

---

## 🤖 AI Filter

* `APP_MODE=test` → always pass
* `APP_MODE=prod` → dùng Gemini thật

---

## 🚨 Live Trading (SAFE MODE)

* Binance market order execution
* Balance validation
* Notional validation
* Sync trạng thái order
* Debug và kiểm tra lệnh
* Không phá logic paper

---

## ⚙️ Env Mode

### TEST MODE

```env
APP_MODE=test
Spam signal nhiều
Cooldown ngắn
AI always pass
Dùng để test TP1 / trailing
PROD MODE
APP_MODE=prod
Signal ít hơn
AI thật
Stable hơn
🧱 Tech Stack
Python 3.13
FastAPI
python-telegram-bot
MySQL
SQLAlchemy
Docker
Gemini API
Binance REST API
📁 Project Structure
app/
├── api/
├── db/
├── market/
├── services/
├── telegram/
├── config.py
├── main.py
⚙️ Setup
1. Clone
git clone <repo>
cd binance-bot
2. Tạo .env
APP_MODE=test
APP_ENV=dev

SCANNER_MAX_SYMBOLS_PER_SCAN=200
SCANNER_RESULTS_LIMIT=20
SCANNER_MIN_QUOTE_VOLUME_5M=10000
SCANNER_MIN_PRICE_CHANGE_5M=0.05
SCANNER_MIN_VOLUME_SPIKE_RATIO=1.1
TEST_MODE_COOLDOWN_SECONDS=10

TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_ALLOWED_USER_IDS=123456789

DB_HOST=mysql
DB_USER=botuser
DB_PASSWORD=pass
MYSQL_ROOT_PASSWORD=pass

GEMINI_API_KEY=your_key

RISK_CAPITAL_USDT=100
RISK_PER_TRADE_PERCENT=2
MAX_OPEN_TRADES=10
MAX_NOTIONAL_PER_TRADE=1000
DAILY_LOSS_LIMIT_USDT=20

ENABLE_LIVE_TRADING=false
LIVE_EXECUTION_ENABLED=false
LIVE_CONFIRM_REAL_ORDERS=false

KILL_SWITCH=false
3. Run
docker compose up -d --build
4. Log
docker logs -f binance-bot-app
📱 Telegram Commands
System
/start
/status
/ping
/healthcheck
/version
/help
Trade Mode
/mode off
/mode paper
/mode live
/confirm_live
/panic
Signals
/history
/top
/stats
Paper Trading
/paper_open
/paper_stats
/paper_today
/paper_close_all
/paper_reset
Watchlist
/watchadd BTCUSDT
/watchremove BTCUSDT
/watchlist
Testing
/scan BTCUSDT
/scanall
/aitest BTCUSDT
/forcealert BTCUSDT
Live
/live_test BTCUSDT
/live_open
/live_history
/live_stats
/live_sync
/live_sync_one 123
/live_close_test 123
/live_detail 123
/live_detail 123 full
🔄 Flow
Scanner
Scan market
AI filter
Build strategy
Build risk
Send Telegram
Save DB
Open paper trade
Paper Trade
Check price
Hit TP1 → close 50%
Activate trailing
Update trailing
Close TP2 / SL
Live Trade
Validate signal
Validate risk
Validate balance
Place Binance order
Sync order
Manage position (TP1 / trailing / TP2)
Performance
Check 5m
Check 15m
Update DB
Send result
🛡 Safety
KILL_SWITCH
Max trades
Duplicate guard
Daily loss breaker
Live safety layer
📊 Verified

Đã test OK:

Open trade
TP1 partial
Trailing
SL / TP2
Multi trade
Env toggle
Risk system
Duplicate guard
🗄 Database
signals
watchlist
bot_state
paper_trades
🔧 Debug
docker logs -f binance-bot-app
docker ps
docker compose down
docker compose up -d --build
🚀 Deploy
Paper

Chạy ổn định trên VPS với Docker

Live

Chỉ bật khi:

Paper stable
Risk OK
Sync OK
API OK
🧠 Roadmap
Dashboard
Backtest
AI nâng cao
Scaling system
👨‍💻 Notes
Không commit .env
Test → dùng APP_MODE=test
Stable → chuyển APP_MODE=prod
Live → bật từng bước (safe mode)
🎯 FINAL STATUS

👉 Production-ready paper trading + safe live trading system