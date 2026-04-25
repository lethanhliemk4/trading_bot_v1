<template>
  <div>
    <div class="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Risk</h1>
        <p class="text-sm text-slate-400">
          Theo dõi giới hạn an toàn LIVE: daily loss, số lệnh/ngày, notional và free USDT.
        </p>
      </div>

      <button
        class="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div v-if="loading" class="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-400">
      Loading risk summary...
    </div>

    <div v-else>
      <div class="grid grid-cols-1 gap-4 mb-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Today PnL" :value="formatNumber(risk?.today_pnl)" />
        <StatCard label="Daily Loss Limit" :value="formatNumber(risk?.daily_loss_limit)" />
        <StatCard label="Max Open Trades" :value="risk?.max_open_trades ?? 0" />
        <StatCard label="Max Notional" :value="formatNumber(risk?.max_notional_per_trade)" />
      </div>

      <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <h2 class="mb-4 text-lg font-semibold">Live Risk Summary</h2>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <InfoRow label="Live Daily Loss Hit" :value="boolText(risk?.live_daily_loss_hit)" />
          <InfoRow label="Today Live PnL" :value="formatNumber(risk?.today_pnl)" />
          <InfoRow label="Daily Loss Limit" :value="formatNumber(risk?.daily_loss_limit)" />
          <InfoRow label="Open Live Trades" :value="risk?.open_live_trades ?? 0" />
          <InfoRow label="Max Open Live Trades" :value="risk?.max_open_trades ?? 0" />
          <InfoRow label="Trades Today" :value="risk?.trades_today ?? 0" />
          <InfoRow label="Max Trades Per Day" :value="risk?.max_trades_per_day ?? 0" />
          <InfoRow label="Max Notional Per Trade" :value="formatNumber(risk?.max_notional_per_trade)" />
          <InfoRow label="Min Free USDT" :value="formatNumber(risk?.min_free_usdt)" />
        </div>
      </section>

      <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <h2 class="mb-4 text-lg font-semibold">Risk Interpretation</h2>

        <div class="space-y-3 text-sm text-slate-300">
          <div :class="risk?.live_daily_loss_hit ? 'text-red-300' : 'text-emerald-300'">
            Daily loss breaker:
            <strong>{{ risk?.live_daily_loss_hit ? "HIT - không nên vào thêm lệnh" : "OK" }}</strong>
          </div>

          <div>
            Open trades:
            <strong>{{ risk?.open_live_trades ?? 0 }}</strong>
            /
            <strong>{{ risk?.max_open_trades ?? 0 }}</strong>
          </div>

          <div>
            Trades today:
            <strong>{{ risk?.trades_today ?? 0 }}</strong>
            /
            <strong>{{ risk?.max_trades_per_day ?? 0 }}</strong>
          </div>

          <div>
            Max notional mỗi lệnh:
            <strong>{{ formatNumber(risk?.max_notional_per_trade) }} USDT</strong>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import StatCard from "~/components/StatCard.vue"

const { get } = useApi()

const loading = ref(false)
const risk = ref<any>(null)

const load = async () => {
  loading.value = true

  const res = await get("/api/dashboard/risk")
  if (res) risk.value = res

  loading.value = false
}

const formatNumber = (value: any, digits = 2) => {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n.toFixed(digits) : "0.00"
}

const boolText = (value: any) => {
  return value ? "YES" : "NO"
}

onMounted(load)
</script>