<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Overview</h1>

    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      <StatCard label="Free USDT" :value="overview?.account?.free_usdt ?? 0" />
      <StatCard label="Today PnL" :value="overview?.live?.today_pnl ?? 0" />
      <StatCard label="Trades Today" :value="overview?.live?.closed ?? 0" />
      <StatCard label="Open Trades" :value="overview?.live?.open ?? 0" />
      <StatCard label="Winrate %" :value="overview?.live?.winrate ?? 0" />
      <StatCard label="TP1 Hits" :value="overview?.live?.tp1_hits ?? 0" />
    </div>

    <!-- Bot status -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 mb-6">
      <h2 class="text-lg font-semibold mb-3">Bot Status</h2>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <div class="text-slate-400">Mode</div>
          <div>{{ overview?.bot?.trade_mode }}</div>
        </div>

        <div>
          <div class="text-slate-400">Auto Trade</div>
          <div>{{ overview?.bot?.auto_trade_enabled }}</div>
        </div>

        <div>
          <div class="text-slate-400">Live Enabled</div>
          <div>{{ overview?.bot?.live_enabled }}</div>
        </div>

        <div>
          <div class="text-slate-400">Kill Switch</div>
          <div>{{ overview?.bot?.kill_switch }}</div>
        </div>
      </div>
    </div>

    <!-- Risk -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4">
      <h2 class="text-lg font-semibold mb-3">Risk</h2>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <div class="text-slate-400">Max Trades/Day</div>
          <div>{{ overview?.risk?.max_trades_per_day }}</div>
        </div>

        <div>
          <div class="text-slate-400">Daily Loss Limit</div>
          <div>{{ overview?.risk?.daily_loss_limit }}</div>
        </div>

        <div>
          <div class="text-slate-400">Max Open Trades</div>
          <div>{{ overview?.risk?.max_open_trades }}</div>
        </div>

        <div>
          <div class="text-slate-400">Max Notional</div>
          <div>{{ overview?.risk?.max_notional_per_trade }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import StatCard from "~/components/StatCard.vue"

const { get } = useApi()

const overview = ref<any>(null)

const load = async () => {
  overview.value = await get("/api/dashboard/overview")
}

onMounted(() => {
  load()

  // auto refresh mỗi 5s
  setInterval(load, 5000)
})
</script>