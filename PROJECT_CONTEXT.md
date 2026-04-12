# 🧠 PROJECT CONTEXT – BINANCE TRADING BOT

## 📍 Current Phase

* Phase: **Paper Trading**
* Status: **COMPLETED & VERIFIED**

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
  * strategy core

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
* phải đảm bảo KHÔNG đổi behavior

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
* Tránh sửa logic core

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
* ❌ Không trade khi chưa confirm
* ✅ Live là execution layer riêng

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

👉 Flow này đã VERIFIED → KHÔNG ĐƯỢC PHÁ

🔧 SAFE CHANGES ALLOWED

Có thể làm:

thêm logging
cải thiện message Telegram
chỉnh config .env
viết README
thêm dashboard
thêm debug tools
thêm sync tools

Không được làm:

rewrite trading logic
thay đổi TP/SL behavior
thay đổi flow hệ thống
📊 RISK SYSTEM CONTEXT
Risk theo % vốn
Position size = risk_amount / stop_distance
Max open trades
Max notional per trade
Daily loss breaker
Kill switch
Duplicate trade guard
📌 CURRENT CONFIG (REFERENCE)
APP_MODE=test
APP_ENV=dev
🚀 LIVE PHASE RULES (CỰC QUAN TRỌNG)
❗ BEFORE ENABLE LIVE

Phải đảm bảo:

 Paper trading stable nhiều giờ
 Không có bug TP1 / trailing
 Risk hoạt động đúng
 Daily loss breaker OK
 Duplicate guard OK
 Sync hoạt động đúng
🔐 LIVE SAFETY LAYER (BẮT BUỘC)

Bot chỉ trade khi:

ENABLE_LIVE_TRADING=true
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=true
APP_ENV=prod
API key hợp lệ
API secret hợp lệ
Balance đủ
Notional hợp lệ
❗ LIVE SAFETY STRATEGY
1. Start SMALL
RISK_CAPITAL_USDT = 10–50
2. Limit trades
MAX_OPEN_TRADES = 1–2
3. Confirm execution
Có thể cần Telegram confirm trước khi đặt lệnh
4. Kill switch ALWAYS READY
KILL_SWITCH=true
❗ NEVER DO THIS
❌ Không bật LIVE ngay với full capital
❌ Không sửa logic khi đang chạy live
❌ Không deploy code chưa test
📱 TELEGRAM CONTROL CONTEXT

Bot điều khiển qua Telegram:

Core commands
/mode paper
/mode live
/panic
Debug commands
/scan
/forcealert
/aitest
Live commands
/live_test
/live_open
/live_sync
/live_detail
🧪 DEBUG CONTEXT
Paper Debug
check TP1 hit
check trailing update
check SL / TP2 close
Live Debug
check order placed
check fill price
check sync data
check position state
📊 LIVE CHECKLIST (FINAL)
 paper stable
 TP1 OK
 trailing OK
 risk OK
 API OK
 balance OK
 sync OK
 detail OK
🎯 NEXT STEP

👉 Move to LIVE PHASE (SAFE MODE)

🧠 NOTE

File này dùng để:

paste vào chat mới
giữ context project
đảm bảo AI không phá code
hỗ trợ debug system
hỗ trợ triển khai live an toàn