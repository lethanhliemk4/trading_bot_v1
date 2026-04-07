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

# 🚀 LIVE PHASE RULES (CỰC QUAN TRỌNG)

## ❗ BEFORE ENABLE LIVE

Phải đảm bảo:

* [ ] Paper trading stable nhiều giờ
* [ ] Không có bug TP1 / trailing
* [ ] Risk hoạt động đúng
* [ ] Daily loss breaker OK

---

## ❗ LIVE SAFETY LAYER (BẮT BUỘC)

Khi làm LIVE:

### 1. Start SMALL

```text
RISK_CAPITAL_USDT = rất nhỏ (10–50)
```

### 2. Limit trades

```text
MAX_OPEN_TRADES = 1–2
```

### 3. Confirm execution

* Có thể thêm confirm Telegram trước khi đặt lệnh

### 4. Kill switch ALWAYS READY

```env
KILL_SWITCH=true
```

---

## ❗ NEVER DO THIS

* ❌ Không bật LIVE ngay với full capital
* ❌ Không sửa logic khi đang chạy live
* ❌ Không deploy code chưa test

---

# 🧱 SYSTEM ARCHITECTURE (LOCKED)

## Flow chính

### Scanner Loop

scan → AI → strategy → risk → Telegram → DB → open trade

### Paper Trade Loop

price → TP1 → partial → trailing → TP2/SL

### Performance Loop

5m → 15m → stats

👉 Flow này đã VERIFIED → KHÔNG ĐƯỢC PHÁ

---

# 🔧 SAFE CHANGES ALLOWED

Có thể làm:

* thêm logging
* cải thiện message Telegram
* chỉnh config `.env`
* viết README
* thêm dashboard

Không được làm:

* rewrite trading logic
* thay đổi TP/SL behavior

---

# 📌 CURRENT CONFIG (REFERENCE)

```env
APP_MODE=test
APP_ENV=dev
```

---

# 🎯 NEXT STEP

👉 Move to LIVE PHASE (SAFE MODE)

---

# 🧠 NOTE

File này dùng để:

* paste vào chat mới
* giữ context project
* đảm bảo AI không phá code

---

# ✅ STATUS

**Production-ready paper trading system**
