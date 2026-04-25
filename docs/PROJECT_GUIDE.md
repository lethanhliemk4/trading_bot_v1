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
* ✅ Testnet live execution armed successfully
* ✅ Runtime guard / watchdog / heartbeat
* ✅ Live trade sync / close / detail / stats
* ✅ VPS deploy flow working
* ✅ Live execution full cycle verified (OPEN → MANAGE → CLOSE)
* ✅ TP1 hit / trailing update verified on live flow
* ✅ Runtime guard cooldown bug fixed
* ✅ `fail_reason` DB overflow issue fixed
* ✅ Strategy level 2 filter started
* ✅ Main flow updated to support strategy validation gate

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
A. PAPER / SAFE MODE
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
B. TESTNET LIVE MODE (KHUYẾN NGHỊ HIỆN TẠI)
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
C. MAINNET MODE (CHƯA BẬT NGAY)
APP_MODE=prod
APP_ENV=prod

ENABLE_LIVE_TRADING=true
BINANCE_USE_TESTNET=false
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=true

👉 Mainnet chỉ bật khi testnet ổn định đủ lâu

🚀 RUN PROJECT
docker compose up -d --build
🔍 CHECK SYSTEM
Container
docker ps
Log
docker logs -f binance-bot-app

hoặc:

docker compose logs -f app
API health
curl http://127.0.0.1:8000/health

Expected:

{"status":"ok"}
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
Confirm commands
/confirm clear_signals
/confirm paper_clear
/confirm paper_reset
🔄 DAILY COMMANDS
Update code
git pull
docker compose up -d --build
Restart
docker compose restart
Stop
docker compose down
Check log nhanh
docker compose logs --tail=100 app
⚠️ SECURITY
❗ KHÔNG commit .env
❗ Nếu lộ Telegram token → regenerate ngay
❗ Không mở port MySQL
❗ Không log API key
❗ Không share screenshot chứa secret

.gitignore tối thiểu nên có:

.env
__pycache__/
*.pyc
logs/
🧪 TEST MODE vs PROD MODE
Mode	Behavior
test	spam nhanh, AI dễ pass hơn, phù hợp debug
prod	scan thật, guard thật, phù hợp VPS testnet/mainnet
🚀 DEPLOY STRATEGY (QUAN TRỌNG)
❌ Sai
Local → LIVE
✅ Đúng
Local → VPS (paper) → ổn định → TESTNET LIVE → ổn định → MAINNET nhỏ
📊 CHECKLIST VPS OK
container chạy
Telegram phản hồi
scanner chạy
có trade mở
không crash
DB ghi dữ liệu OK
health endpoint OK
logs không spam lỗi
🔥 LIVE PHASE
Khi nào được bật live:
chạy paper ổn định
không crash
risk đúng
TP1 / trailing hoạt động chuẩn
daily loss breaker OK
duplicate guard OK
runtime guard OK
sync OK
VPS ổn định
🔐 LIVE SAFETY LAYER

Bot chỉ trade khi:

ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
APP_ENV=prod
API key hợp lệ
API secret hợp lệ
Balance đủ
Notional hợp lệ
Runtime guard pass
Daily loss chưa hit
Cooldown pass
Daily trade count pass
Duplicate trade check pass
🔥 TESTNET LIVE RULE (MỚI NHẤT)
Logic đúng hiện tại
Testnet
BINANCE_USE_TESTNET=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=false
→ vẫn được execution thật trên testnet
Mainnet
BINANCE_USE_TESTNET=false
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=true
→ mới được execution thật

👉 Đây là rule mới đã fix để:

testnet execution hoạt động đúng
mainnet vẫn an toàn
LIVE SAFE CONFIG
TESTNET LIVE
ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=false
BINANCE_USE_TESTNET=true

LIVE_MAX_NOTIONAL_PER_TRADE=20
LIVE_MAX_OPEN_TRADES=1
LIVE_DAILY_LOSS_LIMIT_USDT=5
LIVE_MIN_FREE_USDT=25
LIVE_MAX_TRADES_PER_DAY=3
LIVE_TRADE_COOLDOWN_SECONDS=180

KILL_SWITCH=false
MAINNET LIVE
ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=true
BINANCE_USE_TESTNET=false
⚠️ Cảnh báo
❌ không bật live ngay
❌ không trade full vốn
❌ không sửa logic khi đang chạy
❌ không bỏ qua /live_guard
❌ không lên mainnet nếu testnet chưa chạy đủ lâu
🚨 LIVE FEATURES
Execution
Binance market order
Quantity normalize
Min notional validation
Balance check
Retry logic
Testnet execution allowed
Trade lifecycle
TP1 hit
trailing SL activate
trailing update
TP2 / SL / TSL close
manual close
sync Binance
debug trade
Data tracking
executed_qty
remaining_qty
remaining_qty_after_tp1
avg_fill_price
realized_pnl
entry_order_id
exit_order_id
raw_order_response
🚫 DUPLICATE GUARD

Không mở lệnh nếu symbol đang có trade OPEN

🧪 DEBUG LIVE FLOW
/live_guard
/status
/runtime_status
/live_account
/live_test BTCUSDT
/live_open
/live_sync
/live_detail <id>
/live_close_test <id>
📊 LIVE CHECKLIST
paper stable
TP1 OK
trailing OK
risk OK
API OK
balance OK
sync OK
close OK
stats OK
summary OK
panic OK
🧱 SYSTEM FLOW (LOCKED)
Scanner → AI → Strategy → Risk → Telegram → DB → Trade
Price → TP1 → Trailing → TP2 / SL

👉 Không được phá flow này

🚀 SAFE LIVE STRATEGY
Local → VPS paper → stable → testnet live nhỏ → theo dõi → scale → mainnet cực nhỏ
📅 TESTNET TEST PLAN (7 DAYS)
Day 1 – Check system
/status
/live_guard
/runtime_status
/healthcheck
/live_account
/balance

Goal:

bot running
db ok
binance ok
live guard armed
Day 2 – Test scanner
/watchadd BTCUSDT
/watchadd ETHUSDT
/watchadd SOLUSDT
/watchadd BNBUSDT
/watchlist
/scanall
/scan BTCUSDT

Goal:

scanner hoạt động
có signal
không lỗi
Day 3 – Test manual live entry
/mode live
/live_test BTCUSDT
/live_open
/live_history
/live_stats

Goal:

vào lệnh được
DB lưu đúng
Day 4 – Test sync
/live_open
/live_detail 1
/live_sync
/live_sync_one 1

Goal:

sync đúng Binance
detail hiển thị đúng
Day 5 – Test close
/live_close_test 1
/live_history
/live_stats
/live_pnl_today
/live_summary

Goal:

close thành công
pnl đúng
Day 6 – Test auto mode
/mode live
/scanall
/live_open
/live_history
/live_stats
/runtime_status

Goal:

bot tự scan
tự vào lệnh nếu đủ điều kiện
không spam trade
Day 7 – Test safety
/live_guard
/runtime_status
/live_sync
/panic
/status
/mode off

Goal:

panic ok
guard ok
không treo loop
✅ FINAL TESTNET CHECKLIST
 Bot không crash
 Không spam lệnh
 Risk đúng
 Sync đúng
 Close đúng
 PnL hợp lý
 Panic hoạt động
 VPS ổn định
 Watchdog không báo lỗi giả
 Runtime status đúng
🔥 TROUBLESHOOTING (LỖI ĐÃ GẶP)
1. LIVE trading requires APP_ENV=prod
Nguyên nhân:

Bật live nhưng APP_ENV=dev

Fix:
APP_ENV=prod
2. LIVE_CONFIRM_REAL_ORDERS should not be True while BINANCE_USE_TESTNET=True
Đây là rule cũ đã được thay đổi

Hiện tại logic đúng là:

testnet: không cần confirm flag
mainnet: cần confirm flag

Nếu vẫn gặp lỗi này:

chưa pull code mới
chưa rebuild container
đang chạy code cũ
Fix:
git pull
docker compose down
docker compose up -d --build
3. /runtime_status không trả lời
Nguyên nhân:

handler crash do config/service chưa đồng bộ

Fix:
update bot.py
update config.py
update live_trade_service.py
4. /live_guard báo:
ARMED: NO
REASON: LIVE_CONFIRM_REAL_ORDERS is false
Nguyên nhân:

live_trade_service.py còn dùng logic cũ

Fix:

sửa is_live_execution_armed() để:

testnet không cần confirm
mainnet vẫn cần confirm
5. docker compose warning:
version is obsolete
Fix:

xóa dòng:

version: "3.9"
6. DB model mới nhưng bảng cũ không có cột
Ví dụ:

remaining_qty_after_tp1

Vì sao:

Base.metadata.create_all() không migrate bảng cũ

Fix SQL thủ công:
ALTER TABLE live_trades
ADD COLUMN remaining_qty_after_tp1 DOUBLE NOT NULL DEFAULT 0.0;

ALTER TABLE live_trades
MODIFY raw_order_response VARCHAR(10000);

ALTER TABLE live_trades
MODIFY status VARCHAR(30) NOT NULL DEFAULT 'OPEN';
📌 QUICK DEPLOY (TÓM TẮT)
cd /opt
git clone <repo>
cd repo
nano .env
docker compose up -d --build
docker compose logs -f app
📌 QUICK UPDATE FROM GIT
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
🧠 NOTE

File này dùng để:

giữ context project
paste sang chat mới
tránh AI phá code
hướng dẫn deploy VPS
hướng dẫn bật live an toàn
hướng dẫn test testnet 1 tuần
ghi lại các rule đã chốt
tránh lặp lại các lỗi cũ
🎯 FINAL STATUS

👉 Production-ready paper trading + safe live system + testnet execution ready


---

# 🌐 DASHBOARD + NGINX LAYER (NEW)

## 1. Dashboard (Nuxt 3)

Dashboard dùng để:

- theo dõi live trades
- theo dõi signals
- theo dõi risk
- xem logs
- quan sát runtime bot realtime

### Cấu trúc

```text
dashboard/
├── pages/
│   ├── index.vue
│   ├── live-trades.vue
│   ├── signals.vue
│   ├── risk.vue
│   ├── logs.vue
│   ├── settings.vue
│   └── paper-trades.vue
├── assets/css/main.css
├── nuxt.config.ts
├── package.json
└── Dockerfile
2. Docker Dashboard Service

Trong docker-compose.yml:

dashboard:
  build:
    context: ./dashboard
    dockerfile: Dockerfile
  container_name: binance-bot-dashboard
  restart: unless-stopped
  environment:
    TZ: ${TZ:-Asia/Ho_Chi_Minh}
    NUXT_PUBLIC_API_BASE: http://app:8000
  ports:
    - "127.0.0.1:3000:3000"
  depends_on:
    app:
      condition: service_healthy
  networks:
    - bot_net

👉 QUAN TRỌNG:

❌ KHÔNG dùng 0.0.0.0:3000
✅ CHỈ dùng 127.0.0.1:3000
3. Dashboard API Backend

Các endpoint sử dụng:

/api/dashboard/overview
/api/dashboard/live-trades
/api/dashboard/open-live-trades
/api/dashboard/signals
/api/dashboard/risk
4. Nginx Reverse Proxy

File:

/etc/nginx/conf.d/trading-dashboard.conf

Nội dung:

server {
    listen 80;
    server_name bot.yourdomain.com;

    location / {
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.trading_dashboard_htpasswd;

        proxy_pass http://127.0.0.1:3000;

        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
5. Basic Auth (BẮT BUỘC)

Cài:

yum install -y httpd-tools

Tạo user:

htpasswd -c /etc/nginx/.trading_dashboard_htpasswd admin
6. Domain Setup

DNS:

Type: A
Name: bot
Value: VPS_IP

Truy cập:

http://bot.yourdomain.com
7. HTTPS (Khuyến nghị)
yum install certbot python3-certbot-nginx -y
certbot --nginx -d bot.yourdomain.com
8. Security Layer (CRITICAL)
❌ KHÔNG expose port 3000
❌ KHÔNG expose port 8000
❌ KHÔNG expose MySQL
❌ KHÔNG public dashboard không auth
✅ chỉ nginx expose 80/443
✅ dashboard bắt buộc có password
9. Dashboard Check

Test nội bộ:

curl http://127.0.0.1:3000

Test domain:

http://bot.yourdomain.com
10. Dashboard Troubleshoot
Không load
check container dashboard
check docker logs
check API base URL
Lỗi Nginx
nginx -t
systemctl restart nginx
Login fail
kiểm tra htpasswd
tạo lại user
🔐 PRODUCTION HARDENING (NEW)
1. Network
chỉ mở port:
22 (SSH)
80 (HTTP)
443 (HTTPS)
2. Docker
restart policy: unless-stopped
log rotation bật
3. Secrets
không commit .env
không log API key
rotate key nếu lộ
4. Runtime Safety
luôn bật:
KILL_SWITCH
LIVE GUARD
DAILY LOSS LIMIT
🚨 LIVE INCIDENT HANDLING (NEW)
Khi bot lỗi
docker logs -f binance-bot-app
Khi muốn dừng khẩn cấp

Telegram:

/panic

hoặc:

/panic_close_all
Restart bot
docker compose restart
📊 DASHBOARD OBSERVABILITY (NEW)

Dashboard phải hiển thị đúng:

free USDT
open trades
PnL
signals
risk

Nếu sai:

→ kiểm tra API backend

🎯 FINAL PRODUCTION STATE (UPDATED)

Hệ thống production hoàn chỉnh khi:

✔ Backend stable
✔ Paper trading stable
✔ Live engine stable
✔ Testnet verified
✔ Dashboard running
✔ Nginx working
✔ Domain working
✔ Auth enabled
✔ Security hardened

---
