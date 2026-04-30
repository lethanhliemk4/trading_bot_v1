<template>
  <main class="min-h-screen bg-slate-100 p-6">
    <div class="mx-auto max-w-6xl">
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-slate-900">
          Binance Insight Dashboard
        </h1>
        <p class="mt-2 text-slate-600">
          Trading Mission Control - Insight First
        </p>
      </div>

      <div v-if="pending" class="text-slate-600">
        Loading dashboard...
      </div>

      <div v-else-if="error" class="rounded-xl bg-red-100 p-4 text-red-700">
        Không gọi được backend. Kiểm tra FastAPI/API Base.
      </div>

      <template v-else>
        <section class="grid gap-4 md:grid-cols-3">
          <StatCard label="Market State" :value="overview.market_state" />
          <StatCard label="Risk Status" :value="overview.risk_status" />
          <StatCard label="Strategy Status" :value="overview.strategy_status" />
          <StatCard label="Open Trades" :value="overview.open_trades" />
          <StatCard label="Today PnL" :value="overview.today_pnl" />
          <StatCard label="Recommendation" :value="overview.recommendation" />
        </section>

        <section class="mt-8">
          <h2 class="mb-4 text-xl font-bold text-slate-900">
            Trading Summary
          </h2>

          <div class="grid gap-4 md:grid-cols-3">
            <StatCard label="Today Trades" :value="tradingSummary.today_trades" />
            <StatCard label="Failed Trades" :value="tradingSummary.failed_trades" />
            <StatCard label="Fail Rate" :value="`${tradingSummary.fail_rate}%`" />
            <StatCard label="Today PnL" :value="tradingSummary.today_pnl" />
            <StatCard label="Avg Notional" :value="tradingSummary.avg_notional" />
            <StatCard
              label="Top Fail Reason"
              :value="tradingSummary.most_common_fail_reason || 'None'"
            />
          </div>
        </section>

        <section class="mt-8">
          <h2 class="mb-4 text-xl font-bold text-slate-900">
            Trade Analytics
          </h2>

          <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-600">
                <tr>
                  <th class="p-4">Symbol</th>
                  <th class="p-4">Total Trades</th>
                  <th class="p-4">Failed</th>
                  <th class="p-4">Fail Rate</th>
                  <th class="p-4">Avg Notional</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="item in tradeAnalytics"
                  :key="item.symbol"
                  class="border-t border-slate-100"
                >
                  <td class="p-4 font-semibold text-slate-900">
                    {{ item.symbol }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ item.total }}
                  </td>
                  <td class="p-4 text-red-600">
                    {{ item.failed }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ item.total > 0 ? Math.round((item.failed / item.total) * 100) : 0 }}%
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ item.avg_notional }}
                  </td>
                </tr>

                <tr v-if="tradeAnalytics.length === 0">
                  <td colspan="5" class="p-4 text-slate-500">
                    Chưa có dữ liệu trade analytics.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="mt-8">
          <h2 class="mb-4 text-xl font-bold text-slate-900">
            Recent Live Trades
          </h2>

          <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-600">
                <tr>
                  <th class="p-4">Symbol</th>
                  <th class="p-4">Side</th>
                  <th class="p-4">Status</th>
                  <th class="p-4">Entry</th>
                  <th class="p-4">Notional</th>
                  <th class="p-4">PnL</th>
                  <th class="p-4">Close Reason</th>
                  <th class="p-4">Created</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="trade in recentTrades"
                  :key="trade.id"
                  class="border-t border-slate-100"
                >
                  <td class="p-4 font-semibold text-slate-900">
                    {{ trade.symbol }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ trade.side }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ trade.status }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ trade.entry_price }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ trade.notional }}
                  </td>
                  <td
                    class="p-4"
                    :class="Number(trade.realized_pnl) < 0 ? 'text-red-600' : 'text-slate-700'"
                  >
                    {{ trade.realized_pnl }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ trade.close_reason || '-' }}
                  </td>
                  <td class="p-4 text-slate-500">
                    {{ trade.created_at }}
                  </td>
                </tr>

                <tr v-if="recentTrades.length === 0">
                  <td colspan="8" class="p-4 text-slate-500">
                    Chưa có live trade gần đây.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="mt-8">
          <h2 class="mb-4 text-xl font-bold text-slate-900">
            Insight Center
          </h2>

          <div class="grid gap-4 md:grid-cols-2">
            <InsightCard
              v-for="item in insights"
              :key="item.title"
              :level="item.level"
              :title="item.title"
              :message="item.message"
              :action="item.action"
            />
          </div>
        </section>

        <section class="mt-8">
          <h2 class="mb-4 text-xl font-bold text-slate-900">
            Failed Live Trades
          </h2>

          <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <table class="w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-600">
                <tr>
                  <th class="p-4">Symbol</th>
                  <th class="p-4">Side</th>
                  <th class="p-4">Status</th>
                  <th class="p-4">Notional</th>
                  <th class="p-4">Reason</th>
                  <th class="p-4">Created</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="trade in failedTrades"
                  :key="trade.id"
                  class="border-t border-slate-100"
                >
                  <td class="p-4 font-semibold text-slate-900">
                    {{ trade.symbol }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ trade.side }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ trade.status }}
                  </td>
                  <td class="p-4 text-slate-700">
                    {{ trade.notional }}
                  </td>
                  <td class="p-4 text-red-600">
                    {{ trade.fail_reason }}
                  </td>
                  <td class="p-4 text-slate-500">
                    {{ trade.created_at }}
                  </td>
                </tr>

                <tr v-if="failedTrades.length === 0">
                  <td colspan="6" class="p-4 text-slate-500">
                    Không có live trade lỗi.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>

<script setup lang="ts">
const {
  getOverview,
  getInsights,
  getFailedLiveTrades,
  getTradingSummary,
  getTradeAnalytics,
  getRecentLiveTrades
} = useDashboardApi()

const pending = ref(true)
const error = ref(false)

const overview = ref<any>({})
const insights = ref<any[]>([])
const failedTrades = ref<any[]>([])
const tradingSummary = ref<any>({})
const tradeAnalytics = ref<any[]>([])
const recentTrades = ref<any[]>([])

onMounted(async () => {
  try {
    const [
      overviewData,
      insightData,
      failedTradeData,
      tradingSummaryData,
      tradeAnalyticsData,
      recentTradeData
    ] = await Promise.all([
      getOverview(),
      getInsights(),
      getFailedLiveTrades(),
      getTradingSummary(),
      getTradeAnalytics(),
      getRecentLiveTrades()
    ])

    overview.value = overviewData
    insights.value = insightData as any[]
    failedTrades.value = failedTradeData as any[]
    tradingSummary.value = tradingSummaryData
    tradeAnalytics.value = tradeAnalyticsData as any[]
    recentTrades.value = recentTradeData as any[]
  } catch (e) {
    error.value = true
  } finally {
    pending.value = false
  }
})
</script>
