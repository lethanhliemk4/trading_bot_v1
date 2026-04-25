<template>
  <div>
    <div class="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Overview</h1>
        <p class="text-sm text-slate-400">
          Live trading dashboard · auto refresh mỗi 5 giây
        </p>
      </div>

      <div class="text-xs text-slate-400">
        Last update:
        <span class="text-slate-200">{{ lastUpdated || "N/A" }}</span>
      </div>
    </div>

    <div v-if="loading && !overview" class="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-400">
      Loading dashboard...
    </div>

    <div v-else>
      <div class="grid grid-cols-1 gap-4 mb-6 md:grid-cols-3 lg:grid-cols-6">
        <StatCard label="Free USDT" :value="formatNumber(overview?.account?.free_usdt)" />
        <StatCard label="Today PnL" :value="formatNumber(overview?.live?.today_pnl)" />
        <StatCard label="Open Trades" :value="overview?.live?.open ?? 0" />
        <StatCard label="Closed" :value="overview?.live?.closed ?? 0" />
        <StatCard label="Winrate %" :value="formatNumber(overview?.live?.winrate)" />
        <StatCard label="TP1 Hits" :value="overview?.live?.tp1_hits ?? 0" />
      </div>

      <div class="grid grid-cols-1 gap-6 mb-6 lg:grid-cols-2">
        <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <h2 class="mb-4 text-lg font-semibold">Bot Status</h2>

          <div class="grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
            <InfoItem label="Trade Mode" :value="overview?.bot?.trade_mode" />
            <InfoItem label="Auto Trade" :value="formatBool(overview?.bot?.auto_trade_enabled)" />
            <InfoItem label="App Env" :value="overview?.bot?.app_env" />
            <InfoItem label="Kill Switch" :value="formatBool(overview?.bot?.kill_switch)" />
            <InfoItem label="Live Enabled" :value="formatBool(overview?.bot?.live_enabled)" />
            <InfoItem label="Testnet" :value="formatBool(overview?.account?.binance_use_testnet)" />
          </div>
        </section>

        <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <h2 class="mb-4 text-lg font-semibold">Live Guard</h2>

          <div class="grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
            <InfoItem label="Execution Armed" :value="formatBool(overview?.account?.live_execution_armed)" />
            <InfoItem label="Failed" :value="overview?.live?.failed ?? 0" />
            <InfoItem label="Wins" :value="overview?.live?.wins ?? 0" />
            <InfoItem label="Loses" :value="overview?.live?.loses ?? 0" />
            <InfoItem label="Draws" :value="overview?.live?.draws ?? 0" />
            <InfoItem label="Total" :value="overview?.live?.total ?? 0" />
          </div>
        </section>
      </div>

      <section class="mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-4">
        <h2 class="mb-4 text-lg font-semibold">Risk Summary</h2>

        <div class="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
          <InfoItem label="Max Trades/Day" :value="overview?.risk?.max_trades_per_day" />
          <InfoItem label="Daily Loss Limit" :value="overview?.risk?.daily_loss_limit" />
          <InfoItem label="Max Open Trades" :value="overview?.risk?.max_open_trades" />
          <InfoItem label="Max Notional" :value="overview?.risk?.max_notional_per_trade" />
        </div>
      </section>

      <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-lg font-semibold">Recent Live Trades</h2>
            <NuxtLink to="/live-trades" class="text-sm text-cyan-400 hover:text-cyan-300">
              View all
            </NuxtLink>
          </div>

          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead class="text-left text-slate-400">
                <tr>
                  <th class="py-2 pr-4">Symbol</th>
                  <th class="py-2 pr-4">Side</th>
                  <th class="py-2 pr-4">Status</th>
                  <th class="py-2 pr-4">PnL</th>
                  <th class="py-2 pr-4">Result %</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="trade in recentTrades"
                  :key="trade.id"
                  class="border-t border-slate-800"
                >
                  <td class="py-2 pr-4 font-medium">{{ trade.symbol }}</td>
                  <td class="py-2 pr-4">{{ trade.side }}</td>
                  <td class="py-2 pr-4">{{ trade.status }}</td>
                  <td class="py-2 pr-4" :class="numberClass(trade.realized_pnl)">
                    {{ formatNumber(trade.realized_pnl) }}
                  </td>
                  <td class="py-2 pr-4" :class="numberClass(trade.result_percent)">
                    {{ formatNumber(trade.result_percent) }}
                  </td>
                </tr>

                <tr v-if="recentTrades.length === 0">
                  <td colspan="5" class="py-4 text-slate-500">
                    Chưa có live trade.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-lg font-semibold">Latest Signals</h2>
            <NuxtLink to="/signals" class="text-sm text-cyan-400 hover:text-cyan-300">
              View all
            </NuxtLink>
          </div>

          <div class="space-y-3">
            <div
              v-for="signal in latestSignals"
              :key="signal.id"
              class="rounded-xl border border-slate-800 bg-slate-950 p-3"
            >
              <div class="flex items-center justify-between">
                <div class="font-medium">{{ signal.symbol }} · {{ signal.side }}</div>
                <div class="text-sm text-slate-400">Score {{ signal.score }}</div>
              </div>

              <div class="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-400 md:grid-cols-4">
                <div>5m: {{ formatNumber(signal.price_change_5m) }}%</div>
                <div>Spike: x{{ formatNumber(signal.volume_spike_ratio) }}</div>
                <div>R5m: {{ formatNumber(signal.result_5m) }}</div>
                <div>R15m: {{ formatNumber(signal.result_15m) }}</div>
              </div>
            </div>

            <div v-if="latestSignals.length === 0" class="text-sm text-slate-500">
              Chưa có signal.
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import StatCard from "~/components/StatCard.vue"

const { get } = useApi()

const overview = ref<any>(null)
const liveTrades = ref<any>({ items: [] })
const signals = ref<any>({ items: [] })
const loading = ref(false)
const lastUpdated = ref("")

let timer: ReturnType<typeof setInterval> | null = null

const recentTrades = computed(() => {
  return liveTrades.value?.items?.slice(0, 5) ?? []
})

const latestSignals = computed(() => {
  return signals.value?.items?.slice(0, 5) ?? []
})

const load = async () => {
  loading.value = true

  const [overviewRes, tradesRes, signalsRes] = await Promise.all([
    get("/api/dashboard/overview"),
    get("/api/dashboard/live-trades?limit=5"),
    get("/api/dashboard/signals?limit=5"),
  ])

  if (overviewRes) overview.value = overviewRes
  if (tradesRes) liveTrades.value = tradesRes
  if (signalsRes) signals.value = signalsRes

  lastUpdated.value = new Date().toLocaleString()
  loading.value = false
}

const formatNumber = (value: any) => {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n.toFixed(2) : "0.00"
}

const formatBool = (value: any) => {
  return value ? "ON" : "OFF"
}

const numberClass = (value: any) => {
  const n = Number(value ?? 0)

  if (n > 0) return "text-emerald-400"
  if (n < 0) return "text-red-400"

  return "text-slate-300"
}

onMounted(() => {
  load()
  timer = setInterval(load, 5000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>