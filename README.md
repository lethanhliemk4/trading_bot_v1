# 🚀 Binance Trading Bot

Bot trading crypto tự động điều khiển qua Telegram, chạy 24/7 với Docker + MySQL.

Hệ thống hiện tại đã hoàn thiện các phần cốt lõi:

* Scanner thị trường
* Signal tracking
* Paper trading full flow (TP1 + trailing)
* Risk management
* Env toggle test / prod
* Live trading engine (SAFE MODE)
* Testnet live execution
* Runtime guard / watchdog / heartbeat
* Sync / close / stats / detail cho live trade

---

# 🧠 Project Status

## ✅ Current Status

Bot hiện đang ở trạng thái:

* ✅ Production-ready cho **paper trading**
* ✅ **Safe live engine** đã hoàn thiện
* ✅ **Testnet execution** đã armed và test được
* ✅ VPS deploy flow hoạt động
* ✅ Docker + MySQL runtime ổn định
* ❌ Mainnet chưa bật

## 🎯 Current Phase

**TESTNET LIVE VALIDATION**

Mục tiêu hiện tại là:
* chạy bot trên VPS
* test testnet ổn định khoảng 1 tuần
* kiểm tra auto trade, sync, close, risk, guard
* chỉ sau đó mới cân nhắc mainnet

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
* Có watchlist thủ công
* Có scan từng coin hoặc scanall

---

## 📊 Signal Tracking

* Theo dõi kết quả signal sau:

  * 5 phút
  * 15 phút

* Tính:

  * win / lose / draw
  * max profit
  * max drawdown

* Lưu toàn bộ vào database

---

## 🧪 Paper Trading

* LONG / SHORT
* Entry / SL / TP1 / TP2
* TP1 partial close (50%)
* Trailing stop
* TP2 / SL / TSL close
* Multi trade
* Duplicate guard
* Daily loss breaker
* Export paper trades CSV

---

## 🛡 Risk Management

* Risk theo % vốn
* Position size
* Max open trades
* Max notional
* Daily loss breaker
* KILL_SWITCH
* Live cooldown
* Live max trades/day
* Live min free balance
* Duplicate live trade block

---

## 🤖 AI Filter

* `APP_MODE=test` → AI always pass
* `APP_MODE=prod` → dùng Gemini thật

---

## 🚨 Live Trading (SAFE MODE)

* Binance market order execution
* Balance validation
* Notional validation
* Quantity normalize
* Sync trạng thái order
* Debug và kiểm tra lệnh
* Không phá logic paper
* Testnet execution được phép
* Mainnet có confirm guard riêng
* Manual close
* Live stats / summary / detail / history

---

## ⚙️ Env Mode

### TEST MODE

```env
APP_MODE=test

Behavior:

spam signal nhiều hơn
cooldown ngắn
AI always pass
dùng để test flow nhanh
PROD MODE
APP_MODE=prod

Behavior:

signal ít hơn
AI thật
guard thật
stable hơn
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
1. Clone project
git clone <repo>
cd binance-bot
2. Tạo file .env
A. Safe / Paper mode
APP_MODE=test
APP_ENV=dev

SCANNER_MAX_SYMBOLS_PER_SCAN=80
SCANNER_RESULTS_LIMIT=10
SCANNER_MIN_QUOTE_VOLUME_5M=30000
SCANNER_MIN_PRICE_CHANGE_5M=0.8
SCANNER_MIN_VOLUME_SPIKE_RATIO=1.3
TEST_MODE_COOLDOWN_SECONDS=10

TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_ALLOWED_USER_IDS=123456789
LIVE_ALLOWED_USER_IDS=123456789

DB_HOST=mysql
DB_PORT=3306
DB_NAME=binance_bot
DB_USER=botuser
DB_PASSWORD=pass
MYSQL_ROOT_PASSWORD=pass

GEMINI_API_KEY=

RISK_CAPITAL_USDT=100
RISK_PER_TRADE_PERCENT=1
MAX_OPEN_TRADES=3
MAX_NOTIONAL_PER_TRADE=100
DAILY_LOSS_LIMIT_USDT=5

ENABLE_LIVE_TRADING=false
LIVE_EXECUTION_ENABLED=false
LIVE_CONFIRM_REAL_ORDERS=false

BINANCE_USE_TESTNET=true
KILL_SWITCH=false

TZ=Asia/Ho_Chi_Minh
B. Recommended TESTNET LIVE mode
APP_MODE=prod
APP_ENV=prod
APP_VERSION=1.0.0

TZ=Asia/Ho_Chi_Minh

SCANNER_MAX_SYMBOLS_PER_SCAN=80
SCANNER_RESULTS_LIMIT=10
SCANNER_MIN_QUOTE_VOLUME_5M=30000
SCANNER_MIN_PRICE_CHANGE_5M=0.8
SCANNER_MIN_VOLUME_SPIKE_RATIO=1.3

TEST_MODE_COOLDOWN_SECONDS=10

TELEGRAM_BOT_TOKEN=your_real_token
TELEGRAM_ALLOWED_USER_IDS=your_real_id
LIVE_ALLOWED_USER_IDS=your_real_id

DB_HOST=mysql
DB_PORT=3306
DB_NAME=binance_bot
DB_USER=botuser
DB_PASSWORD=your_real_db_password

MYSQL_ROOT_PASSWORD=your_real_root_password

GEMINI_API_KEY=

RISK_CAPITAL_USDT=100
RISK_PER_TRADE_PERCENT=1
MAX_OPEN_TRADES=3
DAILY_LOSS_LIMIT_USDT=5
MAX_NOTIONAL_PER_TRADE=100

ENABLE_LIVE_TRADING=true
KILL_SWITCH=false

BINANCE_API_KEY=your_testnet_key
BINANCE_API_SECRET=your_testnet_secret
BINANCE_USE_TESTNET=true

LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=false

BINANCE_REST_BASE_URL=https://api.binance.com
BINANCE_WS_BASE_URL=wss://stream.binance.com:9443

BINANCE_TESTNET_REST_BASE_URL=https://testnet.binance.vision
BINANCE_TESTNET_WS_BASE_URL=wss://testnet.binance.vision/ws

BINANCE_RECV_WINDOW_MS=5000
BINANCE_HTTP_TIMEOUT_SECONDS=15

LIVE_MAX_NOTIONAL_PER_TRADE=20
LIVE_MAX_OPEN_TRADES=1
LIVE_DAILY_LOSS_LIMIT_USDT=5
LIVE_MIN_FREE_USDT=25
LIVE_MAX_TRADES_PER_DAY=3
LIVE_TRADE_COOLDOWN_SECONDS=180

HEARTBEAT_INTERVAL_SECONDS=300
WATCHDOG_INTERVAL_SECONDS=60
LOOP_STALE_THRESHOLD_SECONDS=600

LIVE_PLACE_SL_TP_AFTER_ENTRY=true
LIVE_CANCEL_ENTRY_ON_PROTECTION_FAILURE=true
C. Mainnet mode (NOT NOW)
APP_MODE=prod
APP_ENV=prod

ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=true
BINANCE_USE_TESTNET=false

👉 Mainnet chỉ bật sau khi testnet chạy ổn định đủ lâu.

3. Run
docker compose up -d --build
4. Check logs
docker logs -f binance-bot-app

hoặc:

docker compose logs -f app
5. Check API health
curl http://127.0.0.1:8000/health

Expected:

{"status":"ok"}
🐳 Docker Compose

Một cấu hình phù hợp để chạy VPS:

services:
  app:
    build: .
    container_name: binance-bot-app
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      mysql:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    command: >
      sh -c "uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000}"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s

  mysql:
    image: mysql:8.0
    container_name: binance-bot-mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
      TZ: ${TZ:-Asia/Ho_Chi_Minh}
    expose:
      - "3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 20s

volumes:
  mysql_data:
📱 Telegram Commands
System
/start
/status
/ping
/healthcheck
/version
/help
/runtime_status
/live_guard
/live_account
/balance
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
/delete_last_signal
/clear_signals
Paper Trading
/paper_open
/paper_history
/paper_stats
/paper_equity
/paper_today
/paper_export
/paper_close_all
/paper_clear
/paper_reset
Watchlist
/watchadd BTCUSDT
/watchadd ETHUSDT
/watchadd SOLUSDT
/watchadd BNBUSDT
/watchremove BTCUSDT
/watchclear
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
/live_summary
/live_pnl_today
/live_sync
/live_sync_one 123
/live_close_test 123
/live_detail 123
Confirm actions
/confirm clear_signals
/confirm paper_clear
/confirm paper_reset
🔄 Flow
Scanner
Scan market
→ AI filter
→ Build strategy
→ Build risk
→ Send Telegram
→ Save DB
→ Open paper/live trade
Paper Trade
Check price
→ Hit TP1 → close 50%
→ Activate trailing
→ Update trailing
→ Close TP2 / SL / TSL
Live Trade
Validate signal
→ Validate risk
→ Validate balance
→ Place Binance order
→ Sync order
→ Manage position (TP1 / trailing / TP2 / SL / TSL)
Performance
Check 5m
→ Check 15m
→ Update DB
→ Send result
🛡 Safety
KILL_SWITCH
Max trades
Duplicate guard
Daily loss breaker
Live safety layer
Runtime cooldown
Live max trades/day
Live free balance guard
Watchdog loop stale detection
Heartbeat
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
Runtime status
Live guard
Testnet armed execution
VPS deploy flow
Health endpoint
Live sync / live close / live detail
🗄 Database
Tables
signals
watchlist
bot_state
paper_trades
live_trades
LiveTrade tracks
symbol
side
environment
exchange
entry_price
sl
tp1
tp2
rr
risk_amount
position_size
notional
requested_qty
executed_qty
remaining_qty
remaining_qty_after_tp1
avg_fill_price
entry_order_id
entry_client_order_id
entry_order_status
exit_order_id
exit_order_status
status
exit_price
result_percent
close_reason
fail_reason
tp1_hit
tp1_hit_at
trailing_sl
trailing_active
tp1_closed_size
realized_pnl
raw_order_response
opened_at
closed_at
entry_submitted_at
entry_filled_at
last_synced_at
🔧 Debug
Docker
docker logs -f binance-bot-app
docker compose logs -f app
docker ps
docker compose down
docker compose up -d --build
docker compose restart
Git deploy flow
Local
git add .
git commit -m "your message"
git push origin main
VPS
cd /opt/trading_bot_v1
git pull
docker compose down
docker compose up -d --build
docker compose logs -f app
🚀 Deploy
Paper

Chạy ổn định trên VPS với Docker

Testnet live

Chỉ bật khi:

Paper stable
Risk OK
Sync OK
API OK
Runtime guard OK
Live guard = ARMED YES
Mainnet

Chỉ bật khi:

testnet ổn định đủ lâu
không crash
close logic đúng
sync đúng
stats đúng
panic OK
config mainnet đã kiểm tra kỹ
🧪 Testnet Test Plan (1 Week)
Day 1 – Check system
/status
/live_guard
/runtime_status
/healthcheck
/live_account
/balance
Day 2 – Test scanner
/watchadd BTCUSDT
/watchadd ETHUSDT
/watchadd SOLUSDT
/watchlist
/scanall
Day 3 – Test manual entry
/mode live
/live_test BTCUSDT
/live_open
/live_history
Day 4 – Test sync
/live_open
/live_detail 1
/live_sync
/live_sync_one 1
Day 5 – Test close
/live_close_test 1
/live_history
/live_stats
/live_pnl_today
Day 6 – Test auto live
/mode live
/scanall
/live_open
/live_history
/live_stats
/runtime_status
Day 7 – Test safety
/live_guard
/runtime_status
/live_sync
/panic
/status
/mode off
🧠 Roadmap
Dashboard
Backtest
AI nâng cao
Scaling system
Better live audit
Better trailing / partial close execution
Recovery after restart
Mainnet small-size rollout
👨‍💻 Notes
Không commit .env
Test nhanh → dùng APP_MODE=test
Stable → chuyển APP_MODE=prod
Live → bật từng bước (safe mode)
Testnet execution:
BINANCE_USE_TESTNET=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=false
Mainnet execution:
BINANCE_USE_TESTNET=false
LIVE_CONFIRM_REAL_ORDERS=true
⚠️ Common Errors
1. LIVE trading requires APP_ENV=prod

Fix:

APP_ENV=prod
2. /live_guard báo ARMED: NO

Check:

ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
APP_ENV=prod
API key/secret đúng
code mới đã pull + rebuild chưa
3. DB model mới nhưng bảng cũ chưa có cột

create_all() không migrate bảng cũ.
Phải update schema thủ công hoặc dùng migration.

4. version is obsolete trong docker compose

Xóa dòng:

version: "3.9"
🎯 FINAL STATUS

👉 Production-ready paper trading + safe live trading system + testnet execution ready