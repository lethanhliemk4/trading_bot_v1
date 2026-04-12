# 🚀 BINANCE TRADING BOT – FULL DEPLOY & OPERATION GUIDE

---

# 🧠 PROJECT OVERVIEW

## Current Status

* ✅ Paper trading: DONE & VERIFIED
* ✅ TP1 partial close
* ✅ Trailing SL
* ✅ Multi trades
* ✅ Scanner + AI + Risk
* ✅ Env toggle (test / prod)
* ✅ Live trading engine (SAFE MODE)

👉 **System is stable → DO NOT BREAK CORE LOGIC**

---

# ❗ CRITICAL RULES

## 1. 🚫 Không phá logic đang chạy

Không được sửa:

* paper_trade_loop
* TP1 / trailing
* risk logic
* strategy

👉 Nếu muốn sửa:

* phải giải thích
* phải confirm trước

---

## 2. 🚫 Không xóa / rút gọn code

* Không rewrite file
* Không làm file ngắn lại

---

## 3. ✅ Luôn trả file hoàn chỉnh khi sửa

---

## 4. ⚙️ Ưu tiên config (.env), không sửa core

---

## 5. 🚨 LIVE RULE (BỔ SUNG)

* ❌ Không merge logic paper + live
* ❌ Không sửa logic khi đang chạy
* ❌ Không deploy code chưa test
* ❌ Không bật live full vốn
* ❌ Không bypass risk layer
* ❌ Không bypass duplicate guard
* ✅ Live là execution layer riêng

---

# 🧠 SYSTEM DESIGN (QUAN TRỌNG NHẤT)

```text
Paper = simulation engine
Live = execution layer

👉 Không được trộn 2 logic này

🏗️ ARCHITECTURE
VPS
├── binance-bot-app
└── binance-bot-mysql
Không cần Nginx
Không expose MySQL
Bot chạy Telegram polling
Có thể scale thêm worker sau này
📦 REQUIREMENTS
VPS cần có:
Docker
Docker Compose
Git

Check:

docker --version
docker compose version
git --version
📥 CLONE PROJECT
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
⚙️ ENV CONFIG (VPS)
APP_MODE=prod
APP_ENV=dev

SCANNER_MAX_SYMBOLS_PER_SCAN=80
SCANNER_RESULTS_LIMIT=10

TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_ALLOWED_USER_IDS=your_id
LIVE_ALLOWED_USER_IDS=your_id

DB_HOST=mysql
DB_PORT=3306
DB_NAME=binance_bot
DB_USER=botuser
DB_PASSWORD=your_password

MYSQL_ROOT_PASSWORD=your_root_password

GEMINI_API_KEY=your_key

RISK_CAPITAL_USDT=100
RISK_PER_TRADE_PERCENT=2
MAX_OPEN_TRADES=5
MAX_NOTIONAL_PER_TRADE=1000
DAILY_LOSS_LIMIT_USDT=20

ENABLE_LIVE_TRADING=false
LIVE_EXECUTION_ENABLED=false
LIVE_CONFIRM_REAL_ORDERS=false

KILL_SWITCH=false

TZ=Asia/Ho_Chi_Minh
🚀 RUN PROJECT
docker compose up -d --build
🔍 CHECK SYSTEM
Container
docker ps
Log
docker logs -f binance-bot-app
📱 TELEGRAM TEST
/start
/status
/mode paper
/paper_today

Test tay:

/forcealert BTCUSDT
📱 TELEGRAM COMMANDS
System
/start
/status
/ping
/version
/healthcheck
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
🔄 DAILY COMMANDS
Update code
git pull
docker compose up -d --build
Restart
docker compose restart
Stop
docker compose down
⚠️ SECURITY
❗ KHÔNG commit .env
.env
❗ Nếu lộ Telegram token

→ regenerate ngay

❗ Không mở port MySQL
❗ Không log API key
🧪 TEST MODE vs PROD MODE
Mode	Behavior
test	spam nhanh, AI luôn pass
prod	scan thật, AI thật
🚀 DEPLOY STRATEGY (QUAN TRỌNG)
❌ Sai

Local → LIVE

✅ Đúng
Local → VPS (paper) → ổn định → LIVE
📊 CHECKLIST VPS OK
 container chạy
 Telegram phản hồi
 scanner chạy
 có trade mở
 không crash
 DB ghi dữ liệu OK
🔥 LIVE PHASE
Khi nào được bật live:
chạy paper ổn định
không crash
risk đúng
TP1 / trailing hoạt động chuẩn
daily loss breaker OK
🔐 LIVE SAFETY LAYER

Bot chỉ trade khi:

ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=true
APP_ENV=prod
API key hợp lệ
API secret hợp lệ
Balance đủ
Notional hợp lệ
LIVE SAFE CONFIG
ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=true

RISK_CAPITAL_USDT=10
MAX_OPEN_TRADES=1
KILL_SWITCH=false
⚠️ Cảnh báo
❌ không bật live ngay
❌ không trade full vốn
❌ không sửa logic khi đang chạy
🚨 LIVE FEATURES
Execution
Binance market order
Quantity normalize
Min notional validation
Balance check
Trade lifecycle
TP1 hit
trailing SL activate
trailing update
TP2 / SL / TSL close
Control
manual close
sync Binance
debug trade
Data tracking
executed_qty
remaining_qty
avg_fill_price
realized_pnl
🚫 DUPLICATE GUARD
Không mở lệnh nếu symbol đang có trade OPEN
🧪 DEBUG LIVE FLOW
bật config nhỏ
/live_test BTCUSDT
/live_open
/live_sync
/live_detail <id>
/live_detail <id> full
📊 LIVE CHECKLIST
 paper stable
 TP1 OK
 trailing OK
 risk OK
 API OK
 balance OK
🧱 SYSTEM FLOW (LOCKED)
Scanner → AI → Strategy → Risk → Telegram → DB → Trade
Price → TP1 → Trailing → TP2 / SL

👉 Không được phá flow này

🚀 SAFE LIVE STRATEGY
Local → VPS paper → stable → live nhỏ → theo dõi → scale
🎯 FINAL STATUS

👉 Production-ready paper trading + safe live system

📌 QUICK DEPLOY (TÓM TẮT)
cd /opt
git clone <repo>
cd repo
nano .env
docker compose up -d --build
docker logs -f binance-bot-app
🧠 NOTE

File này dùng để:

giữ context project
paste sang chat mới
tránh AI phá code
hướng dẫn deploy VPS
hướng dẫn bật live an toàn