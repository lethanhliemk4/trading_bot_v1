<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Risk Monitor</h1>

      <button
        class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <StatCard label="Today PnL" :value="formatUsdt(risk?.today_realized_pnl)" />
      <StatCard label="Trades Today" :value="`${risk?.today_trade_count ?? 0} / ${risk?.max_trades_per_day ?? 0}`" />
      <StatCard label="Daily Loss Hit" :value="risk?.daily_loss_limit_hit ? 'YES' : 'NO'" />
    </div>

    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4">
      <h2 class="text-lg font-semibold mb-4">Live Risk Settings</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">Max Open Trades</div>
          <div class="text-xl font-bold">{{ risk?.max_open_trades ?? "-" }}</div>
        </div>

        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">Max Trades Per Day</div>
          <div class="text-xl font-bold">{{ risk?.max_trades_per_day ?? "-" }}</div>
        </div>

        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">Max Notional Per Trade</div>
          <div class="text-xl font-bold">{{ formatUsdt(risk?.max_notional_per_trade) }}</div>
        </div>

        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">Daily Loss Limit</div>
          <div class="text-xl font-bold text-red-400">
            -{{ formatUsdtAbs(risk?.daily_loss_limit_usdt) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import StatCard from "~/components/StatCard.vue"

const { get } = useApi()

const risk = ref<any>(null)

const load = async () => {
  risk.value = await get("/api/dashboard/risk")
}

const formatUsdt = (value: any) => {
  const n = Number(value || 0)
  return `${n.toFixed(2)} USDT`
}

const formatUsdtAbs = (value: any) => {
  const n = Math.abs(Number(value || 0))
  return `${n.toFixed(2)} USDT`
}

onMounted(() => {
  load()
  setInterval(load, 5000)
})
</script>