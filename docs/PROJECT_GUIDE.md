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

# 🏗️ ARCHITECTURE

```text
VPS
├── binance-bot-app
└── binance-bot-mysql
```

* Không cần Nginx
* Không expose MySQL
* Bot chạy Telegram polling

---

# 📦 REQUIREMENTS

## VPS cần có:

* Docker
* Docker Compose
* Git

Check:

```bash
docker --version
docker compose version
git --version
```

---

# 📥 CLONE PROJECT

```bash
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

---

# ⚙️ ENV CONFIG (VPS)

```env
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

ENABLE_LIVE_TRADING=false
KILL_SWITCH=false

TZ=Asia/Ho_Chi_Minh
```

---

# 🚀 RUN PROJECT

```bash
docker compose up -d --build
```

---

# 🔍 CHECK SYSTEM

## Container

```bash
docker ps
```

## Log

```bash
docker logs -f binance-bot-app
```

---

# 📱 TELEGRAM TEST

```text
/start
/status
/mode paper
/paper_today
```

Test tay:

```text
/forcealert BTCUSDT
```

---

# 🔄 DAILY COMMANDS

## Update code

```bash
git pull
docker compose up -d --build
```

## Restart

```bash
docker compose restart
```

## Stop

```bash
docker compose down
```

---

# ⚠️ SECURITY

## ❗ KHÔNG commit .env

```gitignore
.env
```

## ❗ Nếu lộ Telegram token

→ regenerate ngay

## ❗ Không mở port MySQL

---

# 🧪 TEST MODE vs PROD MODE

| Mode | Behavior                 |
| ---- | ------------------------ |
| test | spam nhanh, AI luôn pass |
| prod | scan thật, AI thật       |

---

# 🚀 DEPLOY STRATEGY (QUAN TRỌNG)

## ❌ Sai

Local → LIVE

## ✅ Đúng

```text
Local → VPS (paper) → ổn định → LIVE
```

---

# 📊 CHECKLIST VPS OK

* [ ] container chạy
* [ ] Telegram phản hồi
* [ ] scanner chạy
* [ ] có trade mở
* [ ] không crash

---

# 🔥 LIVE PHASE (CHƯA LÀM NGAY)

## Khi nào được bật live:

* chạy paper ổn định
* không crash
* risk đúng

---

## LIVE SAFE CONFIG

```env
ENABLE_LIVE_TRADING=true
RISK_CAPITAL_USDT=10
MAX_OPEN_TRADES=1
```

---

## ⚠️ Cảnh báo

* ❌ không bật live ngay
* ❌ không trade full vốn
* ❌ không sửa logic khi đang chạy

---

# 🧱 SYSTEM FLOW (LOCKED)

```text
Scanner → AI → Strategy → Risk → Telegram → DB → Trade
```

```text
Price → TP1 → Trailing → TP2 / SL
```

👉 Không được phá flow này

---

# 🎯 FINAL STATUS

👉 **Production-ready paper trading system**

---

# 📌 QUICK DEPLOY (TÓM TẮT)

```bash
cd /opt
git clone <repo>
cd repo
nano .env
docker compose up -d --build
docker logs -f binance-bot-app
```

---

# 🧠 NOTE

File này dùng để:

* giữ context project
* paste sang chat mới
* tránh AI phá code

---
