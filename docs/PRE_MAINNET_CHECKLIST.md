# PRE MAINNET CHECKLIST

> Mục tiêu:
> Checklist cuối cùng trước khi bật REAL execution cho trading bot.
>
> Chỉ khi toàn bộ các mục bên dưới đều PASS mới được phép chuyển:
>
> `LIVE_CONFIRM_REAL_ORDERS=false` → `LIVE_CONFIRM_REAL_ORDERS=true`

---

# 1. APP / ENV CHECK

## 1.1 App environment

- [ ] `APP_ENV=prod`
- [ ] `APP_MODE=prod` hoặc mode vận hành chính thức đã được xác nhận
- [ ] `TZ=Asia/Ho_Chi_Minh`
- [ ] `.env` hiện tại là file mainnet đúng, không nhầm sang testnet / paper

## 1.2 Live arming flags

- [ ] `ENABLE_LIVE_TRADING=true`
- [ ] `LIVE_EXECUTION_ENABLED=true`
- [ ] `BINANCE_USE_TESTNET=false`
- [ ] `LIVE_CONFIRM_REAL_ORDERS=false` trong giai đoạn dry-arm
- [ ] Chỉ đổi `LIVE_CONFIRM_REAL_ORDERS=true` sau khi PASS toàn bộ checklist

## 1.3 API / Telegram

- [ ] `BINANCE_API_KEY` đã điền đúng
- [ ] `BINANCE_API_SECRET` đã điền đúng
- [ ] `TELEGRAM_BOT_TOKEN` đúng
- [ ] `TELEGRAM_ALLOWED_USER_IDS` đúng
- [ ] `LIVE_ALLOWED_USER_IDS` đúng

---

# 2. DEPLOY / CONTAINER CHECK

## 2.1 Docker services

- [ ] `binance-bot-app` đang `Up`
- [ ] `binance-bot-mysql` đang `Up (healthy)`
- [ ] app restart policy là `unless-stopped`
- [ ] mysql restart policy là `unless-stopped`

## 2.2 Healthcheck

- [ ] app health endpoint trả OK
- [ ] mysql healthcheck pass
- [ ] `docker compose ps` không có service nào unhealthy
- [ ] `docker logs` không có lỗi crash loop

## 2.3 Storage / logs

- [ ] volume MySQL đang mount đúng
- [ ] logs app đang ghi ra `./logs`
- [ ] docker log rotation đang hoạt động
- [ ] ổ đĩa VPS còn đủ dung lượng

---

# 3. DATABASE CHECK

- [ ] database connect thành công
- [ ] bảng `signals` hoạt động bình thường
- [ ] bảng `paper trades` hoạt động bình thường
- [ ] bảng `live trades` hoạt động bình thường
- [ ] bảng `bot state` hoạt động bình thường
- [ ] app startup không lỗi migration / create table

---

# 4. TELEGRAM CONTROL CHECK

## 4.1 Basic commands

- [ ] `/start` OK
- [ ] `/ping` OK
- [ ] `/status` OK
- [ ] `/version` OK
- [ ] `/healthcheck` OK
- [ ] `/help` OK

## 4.2 Runtime / guard commands

- [ ] `/runtime_status` OK
- [ ] `/live_guard` OK
- [ ] `/strategy_stats` OK

## 4.3 Trade mode commands

- [ ] `/mode off` OK
- [ ] `/mode paper` OK
- [ ] `/mode live` yêu cầu confirm đúng
- [ ] `/confirm_live` chỉ hoạt động với user được phép
- [ ] `/panic` đưa bot về `OFF` thành công

---

# 5. STRATEGY CHECK

## 5.1 Strategy build

- [ ] `build_strategy()` không lỗi với signal hợp lệ
- [ ] `build_strategy()` reject đúng với signal rác
- [ ] có `is_valid`
- [ ] có `invalid_reason`

## 5.2 Strategy gate trong scanner

- [ ] scanner loop có check:
  - [ ] `strategy = coin["strategy"]`
  - [ ] `if not strategy.get("is_valid", False): continue`
- [ ] signal fail strategy không đi tiếp xuống risk
- [ ] signal fail strategy không bị gửi Telegram như alert hợp lệ
- [ ] signal fail strategy không tạo trade

## 5.3 Strategy observability

- [ ] `STRATEGY_STATS` đang tăng đúng
- [ ] `/strategy_stats` trả số liệu hợp lý
- [ ] scan summary log có:
  - [ ] found
  - [ ] ai_rejected
  - [ ] strategy_rejected
  - [ ] risk_rejected
  - [ ] alerts

---

# 6. RISK CHECK

## 6.1 Paper risk

- [ ] `build_risk_plan()` hoạt động đúng
- [ ] chặn `MAX_OPEN_TRADES`
- [ ] chặn duplicate symbol
- [ ] chặn `MAX_NOTIONAL_PER_TRADE`
- [ ] chặn khi daily loss limit hit

## 6.2 Live risk

- [ ] `validate_live_risk_limits()` hoạt động đúng
- [ ] chặn `LIVE_MAX_OPEN_TRADES`
- [ ] chặn duplicate live trade
- [ ] chặn `LIVE_MAX_TRADES_PER_DAY`
- [ ] chặn `LIVE_MAX_NOTIONAL_PER_TRADE`
- [ ] chặn `LIVE_DAILY_LOSS_LIMIT_USDT`
- [ ] chặn nếu `KILL_SWITCH=true`

## 6.3 Balance check

- [ ] `LIVE_MIN_FREE_USDT` hoạt động đúng
- [ ] không đặt lệnh nếu free USDT dưới ngưỡng
- [ ] không đặt lệnh nếu free USDT nhỏ hơn required notional

---

# 7. PAPER TRADE CHECK

## 7.1 Open flow

- [ ] paper trade được mở đúng khi mode = PAPER
- [ ] duplicate paper trade bị chặn
- [ ] entry/sl/tp1/tp2 lưu đúng

## 7.2 Management flow

- [ ] TP1 partial close hoạt động
- [ ] trailing được kích hoạt sau TP1
- [ ] trailing SL update đúng
- [ ] TP2 close đúng
- [ ] SL close đúng
- [ ] TSL close đúng

## 7.3 Paper stats

- [ ] `/paper_open` OK
- [ ] `/paper_history` OK
- [ ] `/paper_stats` OK
- [ ] `/paper_equity` OK
- [ ] `/paper_today` OK
- [ ] `/paper_export` OK

---

# 8. LIVE ENGINE CHECK (TESTNET / DRY-RUN / PRE-MAINNET)

## 8.1 Live arming logic

- [ ] `is_live_execution_armed()` trả đúng trạng thái
- [ ] testnet cho phép execution không cần confirm flag
- [ ] mainnet bắt buộc `LIVE_CONFIRM_REAL_ORDERS=true`
- [ ] thiếu API key thì live bị block

## 8.2 Runtime live guards

- [ ] daily trade limit hoạt động
- [ ] cooldown hoạt động
- [ ] future timestamp anomaly không làm bot khóa sai
- [ ] duplicate live trade bị chặn
- [ ] KILL_SWITCH block live execution

## 8.3 Order placement flow

- [ ] normalize quantity hoạt động
- [ ] min notional validation hoạt động
- [ ] balance validation hoạt động
- [ ] market order đặt thành công trên testnet
- [ ] save live trade thành công
- [ ] post-order sync thành công

## 8.4 Sync flow

- [ ] `sync_live_trade_order()` OK
- [ ] `sync_open_live_trades()` OK
- [ ] entry order status update đúng
- [ ] executed qty update đúng
- [ ] avg fill price update đúng
- [ ] remaining qty update đúng

## 8.5 Close flow

- [ ] `execute_live_close_market_order()` OK
- [ ] close side đúng với LONG/SHORT
- [ ] executed qty close đúng
- [ ] result percent tính đúng
- [ ] realized pnl tính đúng
- [ ] status chuyển `OPEN -> CLOSED` đúng

---

# 9. LIVE SAFETY CHECK

## 9.1 Hard safety

- [ ] mainnet vẫn đang `LIVE_CONFIRM_REAL_ORDERS=false` trong dry-arm phase
- [ ] chưa bật real orders khi chưa review checklist
- [ ] `panic_stop()` test thành công

## 9.2 Recommended extra protections

- [ ] có log khi partial fill xảy ra
- [ ] có limit exposure tổng nếu bạn đã bổ sung
- [ ] có error-rate breaker nếu bạn đã bổ sung
- [ ] có log rõ fail_reason cho mọi lệnh fail

---

# 10. WATCHDOG / HEARTBEAT CHECK

- [ ] heartbeat gửi đúng chu kỳ
- [ ] watchdog gửi cảnh báo nếu loop stale
- [ ] scanner loop last seen update đúng
- [ ] paper loop last seen update đúng
- [ ] live loop last seen update đúng
- [ ] performance loop last seen update đúng

---

# 11. SIGNAL TRACKING / ANALYTICS CHECK

- [ ] signal được lưu DB đúng
- [ ] `result_5m` update đúng
- [ ] `result_15m` update đúng
- [ ] `max_profit` update đúng
- [ ] `max_drawdown` update đúng
- [ ] `/stats` trả kết quả hợp lý

---

# 12. VPS / INFRA CHECK

- [ ] VPS còn RAM đủ
- [ ] VPS còn disk đủ
- [ ] swap không bị full kéo dài
- [ ] SSH ổn định
- [ ] đồng bộ thời gian hệ thống ổn định
- [ ] không có service khác chiếm port nội bộ cần thiết

---

# 13. MAINNET DRY-ARM PHASE

## Trạng thái dry-arm đúng

- [ ] `BINANCE_USE_TESTNET=false`
- [ ] `ENABLE_LIVE_TRADING=true`
- [ ] `LIVE_EXECUTION_ENABLED=true`
- [ ] `LIVE_CONFIRM_REAL_ORDERS=false`

## Trong phase này cần xác nhận

- [ ] bot khởi động ổn
- [ ] Telegram runtime status đúng
- [ ] live guard báo đúng lý do chưa armed
- [ ] không có lệnh thật bị gửi đi
- [ ] scanner / strategy / runtime summary vẫn chạy bình thường

---

# 14. MICRO-LIVE PHASE

Chỉ bắt đầu khi tất cả mục trên PASS.

## Cấu hình micro-live

- [ ] `LIVE_CONFIRM_REAL_ORDERS=true`
- [ ] `LIVE_MAX_NOTIONAL_PER_TRADE` ở mức rất nhỏ
- [ ] `LIVE_MAX_OPEN_TRADES=1`
- [ ] `LIVE_MAX_TRADES_PER_DAY` thấp
- [ ] `LIVE_DAILY_LOSS_LIMIT_USDT` thấp
- [ ] cooldown đủ dài

## Vận hành micro-live

- [ ] theo dõi từng lệnh đầu tiên thủ công
- [ ] kiểm tra Telegram alert cho từng event
- [ ] kiểm tra DB từng trade
- [ ] kiểm tra PnL / close flow / fail_reason
- [ ] không tăng size ngay sau 1-2 lệnh thắng

---

# 15. RULE KHÔNG ĐƯỢC VI PHẠM

- [ ] Không bật `LIVE_CONFIRM_REAL_ORDERS=true` khi chưa PASS checklist
- [ ] Không tăng size lệnh quá sớm
- [ ] Không bỏ qua fail_reason trong log
- [ ] Không sửa core TP1 / trailing / live lifecycle khi đang vận hành mainnet
- [ ] Mọi thay đổi strategy phải test lại bằng testnet hoặc micro-live rất nhỏ

---

# 16. FINAL GO / NO-GO

## GO nếu:

- [ ] Toàn bộ checklist PASS
- [ ] Dry-arm phase ổn định
- [ ] Runtime / Telegram / DB / Binance đều ổn
- [ ] Safety guards đều test pass
- [ ] Bạn đã sẵn sàng xử lý sự cố nếu lệnh đầu tiên có vấn đề

## NO-GO nếu còn một trong các lỗi sau:

- [ ] strategy gate chưa chắc chắn
- [ ] risk reject không biết reason
- [ ] live guard chưa rõ trạng thái
- [ ] partial fill chưa quan sát được
- [ ] sync trade chưa ổn định
- [ ] container/app còn restart bất thường
- [ ] chưa test panic stop

---

# 17. LỆNH XÁC NHẬN CUỐI

Chỉ khi toàn bộ checklist PASS mới được phép đổi:

```env
LIVE_CONFIRM_REAL_ORDERS=true