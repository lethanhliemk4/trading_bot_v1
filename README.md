# 📊 Binance Insight Dashboard

> Read-only dashboard để theo dõi và phân tích trading bot Binance
> **Production-ready – chạy trên VPS với Docker**

---

# 🧠 Overview

**Binance Insight Dashboard** là hệ thống giám sát trading bot:

* Không gửi lệnh
* Không sửa bot
* Không can thiệp database

👉 Chỉ:

* đọc dữ liệu từ MySQL
* phân tích
* hiển thị dashboard

---

# 🏗️ Architecture

## 🔹 Mô hình thực tế (2 VPS)

```txt
VPS 1 (Trading Bot)
├── FastAPI Bot
├── MySQL (Docker)
└── Port: 127.0.0.1:3306

VPS 2 (Dashboard)
├── FastAPI Dashboard API
├── Nuxt 3 Frontend
├── Nginx
└── SSH Tunnel → VPS 1 MySQL
```

---

# 📁 Project Structure

```txt
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── dashboard/
│   │   │   ├── service.py
│   │   │   ├── insight_engine.py
│   │   │   └── router.py
│   │   ├── db/
│   │   │   └── session.py
│   │   └── models/
│   │
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── components/
│   │   ├── StatCard.vue
│   │   └── InsightCard.vue
│   │
│   ├── composables/
│   │   └── useDashboardApi.ts
│   │
│   ├── pages/
│   │   └── index.vue
│   │
│   ├── Dockerfile
│   ├── nuxt.config.ts
│   ├── package.json
│   └── package-lock.json
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

# ⚙️ Tech Stack

## Backend

* FastAPI
* SQLAlchemy
* PyMySQL

## Frontend

* Nuxt 3 (Vue 3 + TypeScript)
* Tailwind CSS

## DevOps

* Docker Compose
* Nginx
* VPS (Ubuntu)

---

# 📦 Features

## 🔹 Overview

* Market state
* Risk status
* Strategy status
* Open trades
* Today PnL

---

## 🔹 Trading Summary

* Total trades
* Failed trades
* Fail rate
* Avg notional
* Top fail reason

---

## 🔹 Trade Analytics

* Theo từng symbol
* Total / Failed / Fail rate
* Avg notional

---

## 🔹 Recent Live Trades (READ-ONLY)

* Symbol / Side / Status
* Entry / Notional
* PnL
* Close reason
* Timestamp

---

## 🔹 Failed Trades

* Danh sách trade lỗi
* Debug cực nhanh

---

## 🔹 Insight Center

* Cảnh báo tự động:

  * Fail rate cao
  * PnL âm
  * Không có trade

---

# 📡 API Endpoints

```txt
GET /api/dashboard/overview
GET /api/dashboard/insights
GET /api/dashboard/trading-summary
GET /api/dashboard/trade-analytics
GET /api/dashboard/live-trades/recent
GET /api/dashboard/live-trades/errors
```

---

# 🔐 Environment

Tạo file:

```bash
backend/.env
```

Ví dụ:

```env
APP_ENV=prod
APP_VERSION=1.0.0

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8001

DB_HOST=172.17.0.1
DB_PORT=3307
DB_NAME=binance_bot
DB_USER=botuser
DB_PASSWORD=your_password
```

---

# 🔗 Database Setup (2 VPS)

## 🎯 Mục tiêu

Dashboard (VPS 2) đọc DB từ Bot (VPS 1)
👉 KHÔNG mở MySQL ra internet

---

## 🔹 Bước 1: VPS 1 (Bot)

MySQL chỉ bind local:

```yaml
ports:
  - "127.0.0.1:3306:3306"
```

---

## 🔹 Bước 2: VPS 2 tạo SSH tunnel

```bash
ssh -p 2018 -f -N -L 172.17.0.1:3307:127.0.0.1:3306 root@VPS1_IP
```

---

## 🔹 Bước 3: Kiểm tra

```bash
ss -tulnp | grep 3307
```

Kết quả:

```txt
172.17.0.1:3307 LISTEN
```

---

## 🔹 Bước 4: Config backend

```env
DB_HOST=172.17.0.1
DB_PORT=3307
```

---

## 🔹 Bước 5: Rebuild

```bash
docker compose up -d --build backend
```

---

# 🚀 Run Dashboard

```bash
docker compose up -d --build
```

---

# 🌐 Nginx Config

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8002/api/;
        proxy_http_version 1.1;
    }

    location / {
        proxy_pass http://127.0.0.1:3000/;
    }
}
```

---

# 🧪 Test

```bash
curl http://127.0.0.1:8002/api/dashboard/overview
curl http://127.0.0.1:8002/api/dashboard/trade-analytics
```

---

# 🔄 Deploy Workflow

## Local

```bash
git add .
git commit -m "update dashboard"
git push origin dashboard
```

---

## VPS

```bash
cd /opt/dashboard
git fetch origin dashboard
git reset --hard origin/dashboard
docker compose up -d --build
```

---

# ⚠️ Design Rules

Dashboard này:

❌ KHÔNG được:

* gửi lệnh trade
* sửa DB
* thay đổi bot

✅ CHỈ:

* đọc dữ liệu
* hiển thị UI
* phân tích

---

# 🧠 Real Insight

Ví dụ:

```txt
Fail Rate = 100%
Reason = Notional < 5
```

👉 Bot không lỗi logic
👉 Nhưng config sai → Binance reject

---

# 🔮 Roadmap

* [ ] PnL chart
* [ ] Win rate
* [ ] Time filter (24h / 7d)
* [ ] Auto refresh
* [ ] Dark mode

---

# 👨‍💻 Author

Liêm Lê
https://github.com/lethanhliemk4

---

# ⭐ License

MIT
