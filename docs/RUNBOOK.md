# RUNBOOK – BINANCE TRADING BOT

> Tài liệu vận hành thực tế cho trading bot chạy trên VPS
> Dùng khi deploy, monitor, debug, hoặc xử lý sự cố production

---

# 1. THÔNG TIN HỆ THỐNG

## 1.1 Stack

* Backend: FastAPI (Python)
* DB: MySQL (Docker)
* Deploy: Docker Compose
* Control: Telegram Bot
* Exchange: Binance (REST API)

---

## 1.2 Services

| Service | Container         | Port           |
| ------- | ----------------- | -------------- |
| App     | binance-bot-app   | 127.0.0.1:8000 |
| MySQL   | binance-bot-mysql | 3306           |

---

## 1.3 Thư mục VPS

```bash
/opt/trading_bot_v1
```

---

# 2. DEPLOY & RESTART

## 2.1 Start system

```bash
cd /opt/trading_bot_v1
docker compose up -d --build
```

---

## 2.2 Stop system

```bash
docker compose down
```

---

## 2.3 Restart nhanh

```bash
docker compose restart
```

---

## 2.4 Rebuild khi update code

```bash
docker compose up -d --build
```

---

# 3. MONITOR SYSTEM

## 3.1 Check container

```bash
docker ps
```

---

## 3.2 Check logs app

```bash
docker logs -f binance-bot-app
```

---

## 3.3 Check logs mysql

```bash
docker logs -f binance-bot-mysql
```

---

## 3.4 Check health

```bash
curl http://127.0.0.1:8000/health
```

---

## 3.5 Check resource VPS

```bash
free -m
df -h
top
```

---

# 4. TELEGRAM CONTROL

## 4.1 Commands quan trọng

* `/status` → trạng thái bot
* `/runtime_status` → runtime info
* `/live_guard` → trạng thái live safety
* `/strategy_stats` → thống kê strategy
* `/mode off`
* `/mode paper`
* `/mode live`
* `/panic` → stop toàn bộ

---

## 4.2 Nguyên tắc

* Chỉ user trong `LIVE_ALLOWED_USER_IDS` mới được dùng LIVE
* Luôn test bằng PAPER trước
* Không bật LIVE khi chưa kiểm tra runtime_status

---

# 5. CHẾ ĐỘ HOẠT ĐỘNG

## OFF

* Không trade
* Scanner vẫn chạy

## PAPER

* Trade giả lập
* Test logic

## LIVE

* Trade thật
* Cần confirm + đủ điều kiện safety

---

# 6. WORKFLOW CHUẨN

## 6.1 Dev → Test

* sửa code
* test local
* push git

---

## 6.2 Deploy VPS

```bash
git pull
docker compose up -d --build
```

---

## 6.3 Kiểm tra

* docker logs
* /health
* telegram

---

## 6.4 Dry-run live

```env
LIVE_EXECUTION_ENABLED=true
LIVE_CONFIRM_REAL_ORDERS=false
```

---

## 6.5 Micro live

```env
LIVE_CONFIRM_REAL_ORDERS=true
```

⚠️ dùng vốn nhỏ

---

# 7. DEBUG NHANH

## 7.1 Bot không gửi Telegram

* check token
* check logs
* check internet VPS

---

## 7.2 Không scan coin

* check scanner logs
* check Binance API

---

## 7.3 Không vào lệnh

* check:

  * strategy reject
  * risk reject
  * live guard
  * cooldown

---

## 7.4 Lỗi DB

```bash
docker exec -it binance-bot-mysql mysql -u root -p
SHOW DATABASES;
```

---

# 8. PANIC / EMERGENCY

## 8.1 Stop ngay bot

Telegram:

```
/panic
```

---

## 8.2 Kill container

```bash
docker compose down
```

---

## 8.3 Bật kill switch

```env
KILL_SWITCH=true
```

---

# 9. BACKUP

## 9.1 Backup DB

```bash
docker exec binance-bot-mysql \
mysqldump -u root -p$MYSQL_ROOT_PASSWORD binance_bot > backup.sql
```

---

## 9.2 Restore

```bash
docker exec -i binance-bot-mysql \
mysql -u root -p$MYSQL_ROOT_PASSWORD binance_bot < backup.sql
```

---

# 10. UPDATE CODE

## 10.1 Flow chuẩn

```bash
git pull
docker compose up -d --build
```

---

## 10.2 Lưu ý

* Không update khi bot đang LIVE với vốn lớn
* Nên chuyển về OFF trước

---

# 11. COMMON LỖI

## Port 80 bị chiếm

```bash
lsof -i :80
```

---

## MySQL unhealthy

* sai password
* thiếu env

---

## Bot crash loop

```bash
docker logs -f binance-bot-app
```

---

# 12. CHECKLIST TRƯỚC KHI NGỦ 😄

* bot đang chạy ổn
* logs không lỗi
* VPS không full RAM
* Telegram nhận heartbeat
* không có trade bất thường

---

# 13. NGUYÊN TẮC VẬN HÀNH

* Không all-in
* Không sửa code khi đang LIVE
* Luôn có panic plan
* Luôn theo dõi lệnh đầu tiên mỗi ngày

---

# 14. FUTURE UPGRADE

* Dashboard web
* Auto hedge
* Multi exchange
* ML strategy
* Alert nâng cao

---

# 15. KẾT LUẬN

Runbook này giúp:

* deploy nhanh
* debug nhanh
* xử lý sự cố
* vận hành an toàn

👉 Đây là thứ phân biệt tool demo và system production

---

# 16. DASHBOARD OPERATIONS (NEW)

## 16.1 Check dashboard container

```bash
docker ps | grep dashboard
16.2 Check logs dashboard
docker logs -f binance-bot-dashboard
16.3 Test nội bộ
curl http://127.0.0.1:3000
16.4 Truy cập domain
http://bot.yourdomain.com

👉 sẽ yêu cầu login (Basic Auth)

16.5 Dashboard lỗi thường gặp
Không load
container chưa chạy
build lỗi
sai API base
Hiển thị rỗng
backend chưa có data
DB local khác VPS
API /api/dashboard/* trả rỗng
17. NGINX OPERATIONS (NEW)
17.1 Check config
nginx -t
17.2 Reload nginx
systemctl reload nginx
17.3 Restart nginx
systemctl restart nginx
17.4 Check nginx status
systemctl status nginx
17.5 Check port 80
lsof -i :80
17.6 Config file
/etc/nginx/conf.d/trading-dashboard.conf
18. BASIC AUTH MANAGEMENT (NEW)
18.1 Tạo user
htpasswd -c /etc/nginx/.trading_dashboard_htpasswd admin
18.2 Thêm user
htpasswd /etc/nginx/.trading_dashboard_htpasswd user2
18.3 Reset password
htpasswd /etc/nginx/.trading_dashboard_htpasswd admin
18.4 Check file
cat /etc/nginx/.trading_dashboard_htpasswd
19. DOMAIN / DNS CHECK (NEW)
19.1 Check DNS
ping bot.yourdomain.com
19.2 Check HTTP
curl http://bot.yourdomain.com
19.3 Check HTTPS
curl https://bot.yourdomain.com
20. SSL MANAGEMENT (NEW)
20.1 Renew SSL
certbot renew
20.2 Re-issue SSL
certbot --nginx -d bot.yourdomain.com
21. SECURITY CHECK (NEW)
21.1 Ports
ss -tuln

Chỉ nên thấy:

22 (SSH)
80 (HTTP)
443 (HTTPS)
21.2 Verify internal binding
docker ps

Check:

127.0.0.1:3000
127.0.0.1:8000
21.3 Không được phép
❌ expose 0.0.0.0:3000
❌ expose 0.0.0.0:8000
❌ expose MySQL
22. LIVE INCIDENT RESPONSE (NEW)
22.1 Bot vào lệnh sai
/panic
22.2 Đóng toàn bộ lệnh
/panic_close_all
22.3 Check ngay
docker logs -f binance-bot-app
22.4 Check DB
docker exec -it binance-bot-mysql mysql -u root -p
22.5 Restart system
docker compose restart
23. LIVE DEBUG CHECKLIST (NEW)

Nếu live không chạy:

check /live_guard
check /runtime_status
check /status
check balance
check API key
check cooldown
check daily limit
check duplicate trade
24. DASHBOARD MONITOR CHECKLIST (NEW)

Dashboard phải hiển thị:

open trades
pnl
signals
risk
logs

Nếu sai:

→ check backend API

25. PRODUCTION RULES (UPDATED)
không deploy khi đang live vốn lớn
không sửa logic core
luôn có panic plan
luôn theo dõi lệnh đầu tiên
dashboard luôn có auth
26. FINAL OPS STATE (UPDATED)

System production OK khi:

✔ backend chạy ổn
✔ mysql healthy
✔ dashboard chạy
✔ nginx chạy
✔ domain truy cập OK
✔ auth hoạt động
✔ logs sạch
✔ telegram control OK
✔ live guard OK

---

