# 🧠 PROJECT CONTEXT – BINANCE TRADING BOT

## 📍 Current Phase

* Phase: **TESTNET LIVE VALIDATION + STRATEGY OPTIMIZATION**
* Previous Stable Phase: **Paper Trading**
* Status: **Paper COMPLETED & VERIFIED**
* Status: **Testnet live engine ARMED & EXECUTED**
* Status: **Mainnet NOT ENABLED**
* Status: **Execution engine VERIFIED**
* Status: **Current weakness = strategy quality / signal filtering**

### ✅ Verified Features

* Open paper trade
* TP1 partial close (50%)
* Trailing SL activate
* Trailing SL update
* TP2 close
* SL close
* Multi trades running
* Env toggle (`APP_MODE=test / prod`)
* Scanner + AI + Risk full flow
* Duplicate guard
* Daily loss breaker
* Risk limit per trade
* Live trading engine (SAFE MODE)
* Live execution armed successfully on TESTNET
* Runtime status command
* Live guard command
* Live account command
* Live sync / sync one
* Live detail / live history / live stats / live summary
* Manual live close test
* VPS deploy flow verified
* Docker + MySQL runtime stable
* Health endpoint verified
* DB schema updated for live tracking
* Watchdog / heartbeat / loop stale protection
* Live trade execution verified end-to-end
* Live trade close verified end-to-end
* TP1 / trailing / close lifecycle verified on live engine
* Runtime cooldown anomaly fixed
* `fail_reason` DB overflow fixed
* Strategy level 2 filtering introduced
* Main flow strategy validation gate introduced

👉 **System is STABLE → CORE LOGIC MUST BE FROZEN**

---

# ❗ CRITICAL RULES (MUST FOLLOW)

## 1. 🚫 DO NOT BREAK WORKING LOGIC

* Không được sửa:

  * `paper_trade_loop`
  * TP1 logic
  * trailing logic
  * close logic
  * risk calculation
  * strategy core nếu chưa giải thích rõ

👉 Nếu cần sửa:

* phải giải thích rõ:

  * sửa gì
  * tại sao
  * ảnh hưởng phần nào
* phải chờ confirm

---

## 2. 🚫 DO NOT REMOVE / SHORTEN CODE

* Không được:

  * xóa code
  * rút gọn code
  * viết lại file ngắn hơn

👉 Nếu muốn optimize:

* phải hỏi trước
* phải đảm bảo KHÔNG đổi behavior ngoài ý muốn

---

## 3. ✅ ALWAYS RETURN FULL FILE

Khi sửa:

* luôn gửi lại **file hoàn chỉnh**
* không gửi snippet rời rạc

---

## 4. ⚠️ CONFIG FIRST – NOT LOGIC

* Ưu tiên sửa:

  * `.env`
  * config
* Tránh sửa logic core nếu chưa thật sự cần

---

## 5. 🧪 TEST MODE ≠ PROD MODE

### TEST MODE

* `APP_MODE=test`
* AI always pass
* scan rộng
* cooldown ngắn
* dùng để test flow nhanh

### PROD MODE

* `APP_MODE=prod`
* AI thật
* scan chặt
* cooldown chuẩn

👉 Không được nhầm lẫn giữa 2 mode

---

## 6. 🚨 LIVE RULE (BỔ SUNG)

* ❌ Không merge logic paper + live
* ❌ Không sửa logic khi đang chạy
* ❌ Không deploy code chưa test
* ❌ Không bật live full vốn
* ❌ Không bypass risk layer
* ❌ Không bypass duplicate guard
* ❌ Không trade mainnet khi chưa confirm
* ✅ Live là execution layer riêng
* ✅ Testnet execution được phép không cần mainnet confirm flag
* ✅ Mainnet vẫn phải có confirm flag riêng

---

## 7. 🔒 CURRENT SAFETY POSITION

### Hiện tại dự án đang ở trạng thái:

* ✅ Có thể trade **thật trên TESTNET**
* ✅ Chưa được phép trade **MAINNET**
* ✅ Có guard chặn nhầm lẫn testnet/mainnet
* ✅ Có `KILL_SWITCH`
* ✅ Có runtime guard
* ✅ Có duplicate guard
* ✅ Có daily loss breaker
* ✅ Có cooldown giữa lệnh live
* ✅ Có max trades per day
* ✅ Có max open live trades
* ✅ Có min free USDT guard
* ✅ Có notional guard
* ✅ Có strategy gate bước đầu

---

# 🧠 SYSTEM DESIGN (LOCKED)

```text
Paper = simulation engine
Live = execution layer

👉 Không được trộn logic
🧱 SYSTEM ARCHITECTURE (LOCKED)
Flow chính
Scanner Loop
scan → AI → strategy → risk → Telegram → DB → open trade
Paper Trade Loop
price → TP1 → partial → trailing → TP2/SL
Performance Loop
5m → 15m → stats → DB
Live Execution Flow (NEW)
signal → strategy → risk → validation → Binance order → sync → manage position
Live Management Flow
entry fill → sync order → TP1 hit → trailing active → TP2 / SL / TSL close

👉 Flow này đã VERIFIED → KHÔNG ĐƯỢC PHÁ
🧱 CURRENT REALITY (RẤT QUAN TRỌNG)
Điều đã được chứng minh
Engine paper hoạt động đúng
Engine live testnet hoạt động đúng
TP1 / trailing / close hoạt động đúng
Runtime guard hoạt động đúng
Cooldown bug đã được fix
DB đã lưu lifecycle live trade đúng hơn
VPS deploy + update flow đang ổn định
Điểm yếu hiện tại

❗ Không còn nằm ở execution engine

👉 Điểm yếu hiện tại nằm ở:

quality của signal
strategy filtering
anti-spam
winrate / edge
🔧 SAFE CHANGES ALLOWED
Có thể làm:
thêm logging
cải thiện message Telegram
chỉnh config .env
viết README / docs
thêm dashboard
thêm debug tools
thêm sync tools
thêm health command
thêm monitoring
thêm export / audit tools
siết strategy filter
giảm spam signal
tối ưu watchlist
thêm regime filter
Không được làm:
rewrite trading logic
thay đổi TP/SL behavior
thay đổi flow hệ thống
merge paper + live engine
bỏ guard để trade nhanh hơn
đổi behavior core mà không confirm
📊 RISK SYSTEM CONTEXT

Risk theo % vốn
Position size = risk_amount / stop_distance
Max open trades
Max notional per trade
Daily loss breaker
Kill switch
Duplicate trade guard
Runtime cooldown
Live daily trade limit
Live free balance guard
Live max open trades guard

📌 CURRENT CONFIG CONTEXT (REFERENCE)
A. Paper / safe reference
APP_MODE=test
APP_ENV=dev
ENABLE_LIVE_TRADING=false
LIVE_EXECUTION_ENABLED=false
LIVE_CONFIRM_REAL_ORDERS=false
BINANCE_USE_TESTNET=true
B. Current recommended testnet live reference
APP_MODE=prod
APP_ENV=prod
ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=false
BINANCE_USE_TESTNET=true
C. Mainnet reference (NOT FOR NOW)
APP_MODE=prod
APP_ENV=prod
ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=true
BINANCE_USE_TESTNET=false
🚀 LIVE PHASE RULES (CỰC QUAN TRỌNG)
❗ BEFORE ENABLE LIVE

Phải đảm bảo:

Paper trading stable nhiều giờ
Không có bug TP1 / trailing
Risk hoạt động đúng
Daily loss breaker OK
Duplicate guard OK
Sync hoạt động đúng
Runtime guard hoạt động đúng
Telegram control hoạt động đúng
VPS stable
DB save đúng lifecycle
🔐 LIVE SAFETY LAYER (BẮT BUỘC)

Bot chỉ trade khi:

ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
APP_ENV=prod
API key hợp lệ
API secret hợp lệ
Balance đủ
Notional hợp lệ
Cooldown pass
Daily trade limit pass
Duplicate symbol pass
KILL_SWITCH không bật
Mainnet only:
LIVE_CONFIRM_REAL_ORDERS=true
Testnet only:
không cần LIVE_CONFIRM_REAL_ORDERS=true
❗ LIVE SAFETY STRATEGY
Start SMALL
LIVE_MAX_NOTIONAL_PER_TRADE = 10–20
Limit trades
LIVE_MAX_OPEN_TRADES = 1
Keep cooldown
LIVE_TRADE_COOLDOWN_SECONDS = 180
Kill switch ALWAYS READY
KILL_SWITCH=true khi cần panic ngay
❗ NEVER DO THIS
❌ Không bật LIVE ngay với full capital
❌ Không sửa logic khi đang chạy live
❌ Không deploy code chưa test
❌ Không nhảy từ local thẳng lên mainnet
❌ Không bỏ qua /live_guard
❌ Không test mainnet trước khi testnet đủ lâu
📱 TELEGRAM CONTROL CONTEXT

Bot điều khiển qua Telegram:

Core commands
/mode paper
/mode live
/panic
/status
/runtime_status
/live_guard
/live_account
Debug commands
/scan
/scanall
/forcealert
/aitest
Live commands
/live_test
/live_open
/live_history
/live_stats
/live_summary
/live_sync
/live_sync_one
/live_detail
/live_close_test
/live_pnl_today
🧪 DEBUG CONTEXT
Paper Debug
check TP1 hit
check trailing update
check SL / TP2 close
check equity
check today PnL
Live Debug
check order placed
check fill price
check sync data
check position state
check account snapshot
check runtime guard
check close order
check history / stats / summary
📊 LIVE CHECKLIST (FINAL)
paper stable
TP1 OK
trailing OK
risk OK
API OK
balance OK
sync OK
detail OK
close OK
summary OK
stats OK
panic OK
watchdog OK
heartbeat OK
🏗️ INFRASTRUCTURE CONTEXT
Deployment style
VPS
├── binance-bot-app
└── binance-bot-mysql
Notes
Không cần Nginx
Không expose MySQL
App port bind local 127.0.0.1:8000
Docker compose healthcheck /health
MySQL container dùng volume
Logs mount ra ./logs
🗄️ DATABASE CONTEXT
LiveTrade hiện đang track:
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
Important note

Base.metadata.create_all() không migrate bảng cũ.
Nếu thêm cột mới vào model → phải cập nhật schema thủ công hoặc dùng migration.

🧩 IMPORTANT FIXES ALREADY APPLIED
1. Runtime status fix
/runtime_status từng silent fail
đã fix handler fail-safe
2. Config fix
testnet execution không còn bị block sai
mainnet vẫn bắt confirm
3. Live guard fix

is_live_execution_armed() đã sửa:

testnet không cần confirm flag
mainnet cần confirm flag
4. Live loop fix

Khi TP2 / SL / TSL hit:

không chỉ đóng DB
mà gọi close execution thật
5. DB schema fix

Đã thêm / sửa:

remaining_qty_after_tp1
raw_order_response tăng size
status default = OPEN
6. Cooldown anomaly fix

Đã gặp lỗi:

Cooldown active (-25199s < 1s)

Đã fix:

outer cooldown guard ở main.py
runtime guard trong live_trade_service.py
7. fail_reason overflow fix

Đã gặp lỗi:

Data too long for column 'fail_reason'

Đã fix:

model đổi fail_reason sang Text
DB alter thủ công:
ALTER TABLE live_trades MODIFY fail_reason TEXT;
🧠 STRATEGY CONTEXT (UPDATED)
Vấn đề cũ

System chạy được nhưng:

trade quá nhiều
failed trades quá nhiều
winrate không tốt
trade signal score thấp
trade coin volume thấp
spam alert / spam guard

👉 Kết luận: execution tốt nhưng strategy/filter yếu

Strategy level 2 đã bắt đầu áp dụng
Mục tiêu:
trade ít hơn
signal chất lượng hơn
giảm spam
improve winrate
Các filter đã định hướng / áp dụng:
score >= 60
quote_volume_5m >= 150000
volume_spike_ratio >= 1.5
atr_ratio >= 0.002
rr_tp2 >= 2.0
Strategy phải trả về:
is_valid
invalid_reason
Main flow bắt buộc phải có:
if not strategy["is_valid"]:
    continue

❗ Đây là điểm critical.
Nếu thiếu dòng này → optimize strategy không có tác dụng.

🚫 ANTI-SPAM CONTEXT
Vấn đề đã thấy
scanner tạo quá nhiều signal
bot gửi alert liên tục
risk layer phải chặn liên tục
DB/history bị spam
summary xấu dù engine không lỗi
Fix đúng hướng
strategy gate trước khi add alert
chỉ add new_alerts sau khi pass strategy
chỉ trade signal đã valid
hạn chế watchlist rác
ưu tiên coin top liquidity
🎯 CURRENT PHASE
Hiện tại nên làm gì
Focus hiện tại:

TESTNET LIVE VALIDATION + STRATEGY OPTIMIZATION

Không nên làm ngay:

MAINNET DEPLOY
tăng vốn lớn
tăng trade frequency quá mạnh
📅 7-DAY TESTNET PLAN CONTEXT
Day 1
check /status
check /live_guard
check /runtime_status
check /live_account

Goal:

bot running
db ok
binance ok
live guard armed
Day 2
test scanner
test watchlist
test signal flow
Day 3
test /live_test BTCUSDT
verify DB save
Day 4
test /live_sync
test /live_detail
Day 5
test /live_close_test
verify history / stats / pnl
Day 6
bật /mode live
để bot tự scan / tự vào lệnh testnet
Day 7
test /panic
test stability
review logs / stats / runtime
🎯 NEXT STEP

👉 Continue TESTNET LIVE PHASE (SAFE MODE)

Sau khi testnet ổn định:

mới tối ưu tiếp
mới scale config
mới nghĩ tới mainnet
🧠 NOTE

File này dùng để:

paste vào chat mới
giữ context project
đảm bảo AI không phá code
hỗ trợ debug system
hỗ trợ triển khai live an toàn
nhắc lại rule không phá logic
giữ đúng định hướng phát triển
ghi rõ rằng phase hiện tại là optimize strategy, không còn chỉ là “engine debug”
🧱 LOCKED PRINCIPLE

Scanner → AI → Strategy → Risk → Telegram → DB → Trade
Price → TP1 → Trailing → TP2 / SL

👉 Đây là flow khóa cứng
👉 Không được phá nếu chưa có confirm rõ ràng

📌 PROJECT STATUS SUMMARY
Stable
paper engine
scanner
AI filter
strategy base
risk
duplicate guard
daily loss breaker
Telegram control
armed on testnet
live guard
runtime guard
testnet execution permission
VPS deploy
live commands
live sync / detail / close
TP1 / trailing / close lifecycle
cooldown anomaly fix
DB fail_reason fix
Not yet approved
mainnet real-money deployment
high capital scaling
aggressive trade frequency
final profitable strategy claim
high-confidence edge
🧭 TRUE CURRENT INTERPRETATION

Nếu thấy:

trades cao
failed cao
closed thấp
winrate thấp

👉 Kết luận đúng là:

engine đang chạy
risk đang chặn đúng
strategy/filter đang yếu

❌ Không phải do DB cũ
❌ Không phải do execution layer hỏng
❌ Không phải do bot “không ổn” ở tầng hạ tầng

🎯 FINAL STATUS

👉 Production-ready paper trading + safe live system + testnet execution ready
👉 Engine core đã hoàn chỉnh
👉 Phase hiện tại = optimize strategy / reduce spam / improve winrate

---

# 🌐 DASHBOARD + NGINX CONTEXT (NEW)

## 🧩 Lý do bổ sung

Ban đầu system:

```text
Telegram only control

Hiện tại đã nâng cấp:

Telegram + Web Dashboard (Nuxt) + Nginx Access Layer

👉 giúp:

quan sát realtime
debug dễ hơn
không phụ thuộc hoàn toàn Telegram
🖥️ DASHBOARD CONTEXT
Stack
Nuxt 3 (Vue 3)
TailwindCSS
chạy trong Docker
gọi API từ FastAPI backend
Dashboard container
binance-bot-dashboard

Bind:

127.0.0.1:3000

👉 KHÔNG expose public

Dashboard API

Frontend gọi:

http://app:8000/api/dashboard/*
Dashboard pages
overview
live trades
signals
risk
logs
settings
paper trades
Dashboard role

👉 KHÔNG control bot (hiện tại)
👉 CHỈ để:

monitor
debug
quan sát
🌐 NGINX CONTEXT (PRODUCTION ACCESS)
Vai trò
Public Internet
    ↓
Nginx (auth + reverse proxy)
    ↓
Dashboard (localhost:3000)
Config location
/etc/nginx/conf.d/trading-dashboard.conf
Proxy flow
https://bot.yourdomain.com
→ nginx
→ http://127.0.0.1:3000
🔐 BASIC AUTH CONTEXT
Mục tiêu

👉 Không để dashboard public

File
/etc/nginx/.trading_dashboard_htpasswd
Behavior
truy cập domain → popup login
chỉ user có password mới vào được
🔒 SECURITY MODEL (UPDATED)
Trước đây
App only (localhost)
Hiện tại
App (127.0.0.1:8000)
Dashboard (127.0.0.1:3000)
↓
Nginx (public)
Nguyên tắc
❌ không expose backend
❌ không expose dashboard
❌ không expose MySQL
✅ chỉ expose nginx
⚠️ SECURITY RISKS (UPDATED)

Nếu sai config:

lộ dashboard → lộ PnL / trade
lộ API endpoint → có thể bị abuse
lộ strategy → mất edge
🧠 CURRENT SYSTEM EVOLUTION
Giai đoạn 1
Telegram bot only
Giai đoạn 2
Telegram + Live engine
Giai đoạn 3 (hiện tại)
Telegram + Live engine + Dashboard + Nginx
🎯 DASHBOARD LIMITATION

Hiện tại:

chưa có auth riêng (chỉ basic auth nginx)
chưa có write action
chưa control bot từ UI

👉 chỉ monitoring

🚀 FUTURE DASHBOARD DIRECTION
login system riêng (JWT)
control bot từ UI
panic button trên web
close all trades
live config UI
realtime websocket
multi user
🧱 UPDATED INFRASTRUCTURE

Hiện tại:

VPS
├── binance-bot-app
├── binance-bot-mysql
├── binance-bot-dashboard
└── nginx
🧠 IMPORTANT INSIGHT (UPDATED)

Hiện tại system:

Execution layer = STRONG
Strategy layer = WEAK

Dashboard giúp thấy rõ:

signal spam
risk reject nhiều
winrate thấp

👉 confirm vấn đề nằm ở strategy

📊 OBSERVABILITY UPGRADE

Trước:

Logs + Telegram

Hiện tại:

Logs + Telegram + Dashboard
🎯 CURRENT TRUE STATE

System hiện tại:

✔ Execution engine production-ready
✔ Live engine verified
✔ Infra stable
✔ Dashboard working
✔ Nginx working
✔ Security basic OK

❗ Strategy chưa tối ưu
❗ Winrate chưa cao
❗ Spam signal còn nhiều
🚨 UPDATED PRIORITY

Thứ tự ưu tiên hiện tại:

Strategy optimization
Signal filtering
Reduce spam
Improve winrate
Dashboard nâng cấp (sau)
Mainnet (sau cùng)
🔥 FINAL CONTEXT

👉 System của bạn hiện tại KHÔNG còn là:

tool demo

👉 mà là:

production trading system (infra + execution ready)
🧭 FINAL PHASE INTERPRETATION
❌ Không còn là debug engine
❌ Không còn là fix bug infra

👉 Phase hiện tại:

STRATEGY OPTIMIZATION