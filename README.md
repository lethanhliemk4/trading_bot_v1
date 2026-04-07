# 🚀 Binance Trading Bot (Telegram + Scanner)

Bot trading crypto tự động + điều khiển qua Telegram.
Thiết kế để chạy **24/7 production** với Docker + MySQL.

---

# 📦 Features

## 🔍 Core

* Auto scan thị trường mỗi **30 giây**
* Phát hiện coin dựa trên:

  * Volume tăng mạnh
  * Price change (5m)
  * Volume spike
* Gửi alert về Telegram
* Lưu toàn bộ signal vào database

---

## 📊 Performance Tracking

* Theo dõi sau:

  * 5 phút
  * 15 phút
* Tính:

  * Win / Lose / Draw
  * Max profit
  * Max drawdown

---

## 🤖 Telegram Control

* Scan thủ công (`/scan`)
* Scan watchlist (`/scanall`)
* Quản lý watchlist
* Xem thống kê (`/stats`)
* Healthcheck hệ thống (`/healthcheck`)
* Version control (`/version`)

---

# 🧱 Tech Stack

* Python 3.13
* FastAPI
* python-telegram-bot
* MySQL (Docker)
* SQLAlchemy
* httpx
* AsyncIO

---

# ⚙️ Setup

## 1. Clone project

```bash
git clone <your-repo>
cd binance-bot
```

---

## 2. Tạo `.env`

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_ALLOWED_USER_IDS=your_telegram_id

# App
APP_ENV=dev
APP_VERSION=1.0.0

# Database
DB_HOST=mysql
DB_PORT=3306
DB_NAME=binance_bot
DB_USER=botuser
DB_PASSWORD=botpass
```

---

## 3. Run bằng Docker

```bash
docker compose up -d --build
```

---

## 4. Kiểm tra container

```bash
docker ps
```

---

# 🗄 Database

## Reset DB (nếu lỗi)

```sql
DROP TABLE signals;
DROP TABLE watchlist;
```

Sau đó:

```bash
docker compose down
docker compose up -d --build
```

---

# 🤖 Telegram Commands

---

## 🔹 System

```text
/start        - Bot chạy chưa
/status       - Trạng thái bot
/ping         - Ping nhanh
/version      - Version hiện tại
/healthcheck  - Check Telegram + DB + Binance
/help         - Danh sách lệnh
```

---

## 🔹 Signals

```text
/history  - Signal gần nhất
/top      - Signal score cao
/stats    - Thống kê performance
```

---

## 🔹 Watchlist

```text
/watchlist
/watchadd BTCUSDT
/watchremove BTCUSDT
/watchclear
```

---

## 🔹 Scan

```text
/scan BTCUSDT   - Scan 1 coin ngay
/scanall        - Scan toàn bộ watchlist
```

---

# 🔄 Flow hoạt động

## 🤖 Auto Mode

* Chạy nền 24/7
* Scan mỗi 30 giây
* Nếu có signal:

  * gửi Telegram
  * lưu DB

---

## 📊 Performance Mode

* Sau 5 phút → check kết quả
* Sau 15 phút → check lại
* Update:

  * winrate
  * profit
  * drawdown

---

## 🧠 Manual Mode

Bạn có thể điều khiển bot realtime:

```text
/scan BTCUSDT
/scanall
```

---

# 🧪 Test nhanh

## Test bot

```text
/ping
```

---

## Test toàn hệ thống

```text
/healthcheck
```

---

## Test scan

```text
/scan BTCUSDT
```

---

# 📁 Project Structure

```text
app/
├── api/
├── db/
│   ├── models.py
│   └── session.py
├── services/
│   ├── signal_service.py
│   ├── watchlist_service.py
│   └── health_service.py
├── market/
│   ├── scanner.py
│   ├── rest_client.py
│   └── ws_client.py
├── telegram/
│   └── bot.py
├── main.py
```

---

# ⚠️ Lưu ý

* Bot chỉ phản hồi user đã whitelist
* Binance API có rate limit
* Scanner auto chạy song song với command

---

# 🚀 Deploy Production

## 1. VPS

* Ubuntu / Linux
* Cài:

  * Docker
  * Docker Compose

---

## 2. ENV production

```env
APP_ENV=production
APP_VERSION=1.0.1
```

---

## 3. Run

```bash
docker compose up -d --build
```

---

# 🔧 Debug

## Xem log

```bash
docker logs -f binance-bot-app
```

---

## Vào MySQL

```bash
docker exec -it binance-bot-mysql mysql -u root -p
```

---

# 🧠 Roadmap

## Level 2

* Filter signal theo score
* Multi-user Telegram
* Web dashboard

---

## Level 3

* AI scoring (Gemini / Claude)
* Backtest engine
* Strategy tuning

---

## PRO

* Auto trade Binance
* Risk management
* Portfolio tracking

---

# 🤖 Telegram Commands

Danh sách lệnh Telegram hiện bot đang hỗ trợ.

---

## 🔹 System

```text
/start
/status
/ping
/version
/healthcheck
/help
```

### Mô tả

* `/start` — kiểm tra bot còn chạy
* `/status` — xem trạng thái bot
* `/ping` — ping nhanh
* `/version` — xem version bot hiện tại
* `/healthcheck` — kiểm tra Telegram + DB + Binance API
* `/help` — xem toàn bộ lệnh

---

## 🔹 Signals

```text
/history
/top
/stats
/delete_last_signal
/clear_signals
```

### Mô tả

* `/history` — xem signal gần nhất
* `/top` — xem signal score cao nhất
* `/stats` — xem thống kê performance 5M / 15M
* `/delete_last_signal` — xóa signal mới nhất
* `/clear_signals` — xóa toàn bộ signal

---

## 🔹 Watchlist

```text
/watchlist
/watchadd BTCUSDT
/watchremove BTCUSDT
/watchclear
```

### Mô tả

* `/watchlist` — xem watchlist hiện tại
* `/watchadd BTCUSDT` — thêm coin vào watchlist
* `/watchremove BTCUSDT` — xóa 1 coin khỏi watchlist
* `/watchclear` — xóa toàn bộ watchlist

---

## 🔹 Scan

```text
/scan BTCUSDT
/scanall
```

### Mô tả

* `/scan BTCUSDT` — scan 1 coin ngay lập tức
* `/scanall` — scan toàn bộ coin trong watchlist

---

## 🔹 AI / Testing

```text
/aitest BTCUSDT
/forcealert BTCUSDT
```

### Mô tả

* `/aitest BTCUSDT` — test AI filter trên 1 coin
* `/forcealert BTCUSDT` — ép bot gửi alert test và lưu DB ngay cả khi signal chưa đẹp

---

# 📌 Ví dụ sử dụng nhanh

## Kiểm tra bot

```text
/ping
/healthcheck
/version
```

## Thêm watchlist

```text
/watchadd BTCUSDT
/watchadd ETHUSDT
/watchadd SOLUSDT
/watchlist
```

## Scan thủ công

```text
/scan BTCUSDT
/scanall
```

## Test AI

```text
/aitest BTCUSDT
```

## Tạo dữ liệu test

```text
/forcealert BTCUSDT
/history
/top
```

## Dọn dữ liệu test

```text
/delete_last_signal
/clear_signals
```

---

# 🧪 Kết quả mẫu

## `/healthcheck`

```text
🩺 HEALTHCHECK

Telegram: OK
Database: OK
Binance API: OK
```

## `/scan BTCUSDT`

```text
🔍 SCAN RESULT

🔥 BTCUSDT
Score: 70
5m Change: +2.10%
Volume: 1.20M
Spike: x2.30
Entry: 68450.230000
```

## `/stats`

```text
📊 PERFORMANCE

⏱ 5M
Total: 12
Wins: 7 | Loses: 4 | Draws: 1
Winrate: 58.33%
Avg: +0.21%

⏱ 15M
Total: 10
Wins: 6 | Loses: 3 | Draws: 1
Winrate: 60.00%
Avg: +0.37%

📈 OVERALL
Completed Signals: 10
Avg Max Profit: +0.88%
Avg Max Drawdown: -0.42%
```


# 👨‍💻 Author

Production-ready crypto trading tool 🚀
