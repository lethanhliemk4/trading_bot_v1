<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold">Logs</h1>
      <p class="text-sm text-slate-400">
        Dashboard hiện chưa đọc trực tiếp log file. Dùng các lệnh dưới để xem log production.
      </p>
    </div>

    <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <h2 class="mb-4 text-lg font-semibold">App Logs</h2>

      <pre class="overflow-x-auto rounded-xl bg-slate-950 p-4 text-sm text-slate-300"><code>docker logs -f binance-bot-app</code></pre>
    </section>

    <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <h2 class="mb-4 text-lg font-semibold">MySQL Logs</h2>

      <pre class="overflow-x-auto rounded-xl bg-slate-950 p-4 text-sm text-slate-300"><code>docker logs -f binance-bot-mysql</code></pre>
    </section>

    <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <h2 class="mb-4 text-lg font-semibold">Compose Logs</h2>

      <pre class="overflow-x-auto rounded-xl bg-slate-950 p-4 text-sm text-slate-300"><code>cd /opt/trading_bot_v1
docker compose logs -f app</code></pre>
    </section>

    <section class="mt-6 rounded-2xl border border-yellow-500/30 bg-yellow-500/10 p-4">
      <h2 class="mb-2 text-lg font-semibold text-yellow-300">Ghi chú</h2>
      <p class="text-sm text-yellow-100">
        Không nên expose raw logs qua public API nếu dashboard chưa có auth. Log có thể chứa lỗi, symbol, trạng thái lệnh hoặc thông tin nhạy cảm.
      </p>
    </section>
  </div>
</template>