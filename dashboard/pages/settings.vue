<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold">Settings</h1>
      <p class="text-sm text-slate-400">
        Xem trạng thái cấu hình LIVE hiện tại. Page này chỉ đọc, không thay đổi bot.
      </p>
    </div>

    <button
      class="mb-6 rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
      @click="load"
    >
      Refresh
    </button>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <h2 class="mb-4 text-lg font-semibold">Bot Config</h2>

        <div class="grid gap-3">
          <InfoRow label="Trade Mode" :value="overview?.bot?.trade_mode" />
          <InfoRow label="Auto Trade" :value="boolText(overview?.bot?.auto_trade_enabled)" />
          <InfoRow label="App Env" :value="overview?.bot?.app_env" />
          <InfoRow label="Kill Switch" :value="boolText(overview?.bot?.kill_switch)" />
          <InfoRow label="Live Enabled" :value="boolText(overview?.bot?.live_enabled)" />
          <InfoRow label="Binance Testnet" :value="boolText(overview?.account?.binance_use_testnet)" />
          <InfoRow label="Live Execution Armed" :value="boolText(overview?.account?.live_execution_armed)" />
        </div>
      </section>

      <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <h2 class="mb-4 text-lg font-semibold">Live Risk Config</h2>

        <div class="grid gap-3">
          <InfoRow label="Free USDT" :value="formatNumber(overview?.account?.free_usdt)" />
          <InfoRow label="Daily Loss Limit" :value="formatNumber(risk?.daily_loss_limit)" />
          <InfoRow label="Max Open Trades" :value="risk?.max_open_trades ?? 0" />
          <InfoRow label="Max Trades Per Day" :value="risk?.max_trades_per_day ?? 0" />
          <InfoRow label="Max Notional Per Trade" :value="formatNumber(risk?.max_notional_per_trade)" />
          <InfoRow label="Min Free USDT" :value="formatNumber(risk?.min_free_usdt)" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()

const overview = ref<any>(null)
const risk = ref<any>(null)

const load = async () => {
  const [overviewRes, riskRes] = await Promise.all([
    get("/api/dashboard/overview"),
    get("/api/dashboard/risk"),
  ])

  if (overviewRes) overview.value = overviewRes
  if (riskRes) risk.value = riskRes
}

const boolText = (value: any) => {
  return value ? "ON" : "OFF"
}

const formatNumber = (value: any, digits = 2) => {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n.toFixed(digits) : "0.00"
}

onMounted(load)
</script>