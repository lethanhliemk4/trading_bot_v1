# 🚀 Binance Trading Bot

Bot trading crypto tự động điều khiển qua Telegram, chạy 24/7 với Docker + MySQL.

Hệ thống đã hoàn thiện:

* Scanner thị trường
* Signal tracking
* Paper trading full flow (TP1 + trailing)
* Risk management
* Env toggle test / prod

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

## ⚙️ Env Mode

### TEST MODE

```env
APP_MODE=test
```

* Spam signal nhiều
* Cooldown ngắn
* AI always pass
* Dùng để test TP1 / trailing

### PROD MODE

```env
APP_MODE=prod
```

* Signal ít hơn
* AI thật
* Stable hơn

---

# 🧱 Tech Stack

* Python 3.13
* FastAPI
* python-telegram-bot
* MySQL
* SQLAlchemy
* Docker
* Gemini API

---

# 📁 Project Structure

```text
app/
├── api/
├── db/
├── market/
├── services/
├── telegram/
├── config.py
├── main.py
```

---

# ⚙️ Setup

## 1. Clone

```bash
git clone <repo>
cd binance-bot
```

## 2. Tạo `.env`

```env
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

ENABLE_LIVE_TRADING=false
KILL_SWITCH=false
```

## 3. Run

```bash
docker compose up -d --build
```

## 4. Log

```bash
docker logs -f binance-bot-app
```

---

# 🤖 Telegram Commands

## System

```text
/start
/status
/ping
/healthcheck
/version
/help
```

## Trade Mode

```text
/mode off
/mode paper
/mode live
/panic
```

## Signals

```text
/history
/top
/stats
```

## Paper Trading

```text
/paper_open
/paper_stats
/paper_today
/paper_close_all
/paper_reset
```

## Watchlist

```text
/watchadd BTCUSDT
/watchremove BTCUSDT
/watchlist
```

## Testing

```text
/scan BTCUSDT
/scanall
/aitest BTCUSDT
/forcealert BTCUSDT
```

---

# 🔄 Flow

## Scanner

1. Scan market
2. AI filter
3. Build strategy
4. Build risk
5. Send Telegram
6. Save DB
7. Open paper trade

## Paper Trade

1. Check price
2. Hit TP1 → close 50%
3. Activate trailing
4. Update trailing
5. Close TP2 / SL

## Performance

1. Check 5m
2. Check 15m
3. Update DB
4. Send result

---

# 🛡 Safety

* KILL_SWITCH
* Max trades
* Duplicate guard
* Daily loss breaker

---

# 📊 Verified

Đã test OK:

* Open trade
* TP1 partial
* Trailing
* SL / TP2
* Multi trade
* Env toggle

---

# 🗄 Database

* signals
* watchlist
* bot_state
* paper_trades

---

# 🔧 Debug

```bash
docker logs -f binance-bot-app
docker ps
docker compose down
docker compose up -d --build
```

---

# 🚀 Deploy

## Paper

Chạy ổn định trên VPS với Docker

## Live

Chưa bật ngay — cần thêm safeguard

---

# 🧠 Roadmap

* Dashboard
* Backtest
* AI nâng cao
* Live trading Binance

---

# 👨‍💻 Notes

* Không commit `.env`
* Test → dùng `APP_MODE=test`
* Stable → chuyển `APP_MODE=prod`

---

# ✅ Status

**Production-ready paper trading bot**
