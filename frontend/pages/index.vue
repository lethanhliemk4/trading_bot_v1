<template>
  <main class="min-h-screen bg-slate-950 p-6 text-slate-100">
    <div class="mx-auto max-w-7xl">
      <div class="mb-8 overflow-hidden rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 p-6 shadow-2xl">
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div class="mb-3 flex flex-wrap items-center gap-3">
              <span class="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
                LIVE MONITORING
              </span>

              <span
                class="rounded-full px-3 py-1 text-xs font-semibold"
                :class="getRiskBadgeClass(overview.risk_status)"
              >
                Risk: {{ overview.risk_status || 'UNKNOWN' }}
              </span>

              <span
                class="rounded-full px-3 py-1 text-xs font-semibold"
                :class="getStrategyBadgeClass(overview.strategy_status)"
              >
                Strategy: {{ overview.strategy_status || 'UNKNOWN' }}
              </span>
            </div>

            <h1 class="text-3xl font-bold tracking-tight text-white md:text-4xl">
              Binance Insight Dashboard
            </h1>

            <p class="mt-2 text-slate-400">
              Trading Mission Control - Insight First
            </p>
          </div>

          <div class="rounded-2xl border border-slate-700 bg-slate-950/60 p-4 text-right">
            <p class="text-xs uppercase tracking-wide text-slate-500">
              Today PnL
            </p>
            <p
              class="mt-1 text-3xl font-black"
              :class="getPnlClass(overview.today_pnl)"
            >
              {{ formatNumber(overview.today_pnl, 4) }}
            </p>
            <p class="mt-1 text-xs text-slate-500">
              Read-only dashboard
            </p>
          </div>
        </div>
      </div>

      <div v-if="pending" class="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">
        Loading dashboard...
      </div>

      <div v-else-if="error" class="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
        Không gọi được backend. Kiểm tra FastAPI/API Base.
      </div>

      <template v-else>
        <section class="grid gap-4 md:grid-cols-3">
          <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
            <p class="text-sm text-slate-400">
              Market State
            </p>
            <p class="mt-3 text-2xl font-black text-white">
              {{ overview.market_state }}
            </p>
          </div>

          <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
            <p class="text-sm text-slate-400">
              Risk Status
            </p>
            <p class="mt-3 text-2xl font-black" :class="getRiskTextClass(overview.risk_status)">
              {{ overview.risk_status }}
            </p>
          </div>

          <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
            <p class="text-sm text-slate-400">
              Strategy Status
            </p>
            <p class="mt-3 text-2xl font-black" :class="getStrategyTextClass(overview.strategy_status)">
              {{ overview.strategy_status }}
            </p>
          </div>

          <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
            <p class="text-sm text-slate-400">
              Open Trades
            </p>
            <p class="mt-3 text-2xl font-black text-white">
              {{ overview.open_trades }}
            </p>
          </div>

          <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
            <p class="text-sm text-slate-400">
              Today PnL
            </p>
            <p class="mt-3 text-2xl font-black" :class="getPnlClass(overview.today_pnl)">
              {{ formatNumber(overview.today_pnl, 4) }}
            </p>
          </div>

          <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
            <p class="text-sm text-slate-400">
              Recommendation
            </p>
            <p class="mt-3 text-2xl font-black text-white">
              {{ overview.recommendation }}
            </p>
          </div>
        </section>

        <section class="mt-8">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-xl font-bold text-white">
              Trading Summary
            </h2>
            <span class="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-400">
              Today
            </span>
          </div>

          <div class="grid gap-4 md:grid-cols-3">
            <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
              <p class="text-sm text-slate-400">
                Today Trades
              </p>
              <p class="mt-3 text-2xl font-black text-white">
                {{ tradingSummary.today_trades }}
              </p>
            </div>

            <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
              <p class="text-sm text-slate-400">
                Failed Trades
              </p>
              <p class="mt-3 text-2xl font-black text-red-400">
                {{ tradingSummary.failed_trades }}
              </p>
            </div>

            <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
              <p class="text-sm text-slate-400">
                Fail Rate
              </p>
              <p
                class="mt-3 text-2xl font-black"
                :class="Number(tradingSummary.fail_rate) >= 70 ? 'text-red-400' : Number(tradingSummary.fail_rate) >= 30 ? 'text-amber-400' : 'text-emerald-400'"
              >
                {{ tradingSummary.fail_rate }}%
              </p>
            </div>

            <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
              <p class="text-sm text-slate-400">
                Today PnL
              </p>
              <p class="mt-3 text-2xl font-black" :class="getPnlClass(tradingSummary.today_pnl)">
                {{ formatNumber(tradingSummary.today_pnl, 4) }}
              </p>
            </div>

            <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
              <p class="text-sm text-slate-400">
                Avg Notional
              </p>
              <p class="mt-3 text-2xl font-black text-white">
                {{ formatNumber(tradingSummary.avg_notional, 4) }}
              </p>
            </div>

            <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
              <p class="text-sm text-slate-400">
                Top Fail Reason
              </p>
              <p class="mt-3 text-lg font-black leading-snug text-red-300">
                {{ tradingSummary.most_common_fail_reason || 'None' }}
              </p>
            </div>
          </div>
        </section>

        <section class="mt-8">
          <div class="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 class="text-xl font-bold text-white">
                Winrate Analytics
              </h2>
              <p class="mt-1 text-sm text-slate-500">
                Biểu đồ tròn Win / Loss / Fail, tính từ recent live trades đã tải.
              </p>
            </div>

            <select
              v-model="winrateRange"
              class="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
            >
              <option value="7d">7 ngày</option>
              <option value="30d">Tháng</option>
              <option value="90d">Quý</option>
              <option value="365d">Năm</option>
            </select>
          </div>

          <div class="grid gap-4 lg:grid-cols-3">
            <div class="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg lg:col-span-1">
              <div class="mx-auto flex h-56 w-56 items-center justify-center rounded-full"
                :style="{ background: winratePieBackground }"
              >
                <div class="flex h-32 w-32 flex-col items-center justify-center rounded-full border border-slate-800 bg-slate-950 text-center shadow-inner">
                  <p class="text-xs uppercase tracking-wide text-slate-500">
                    Winrate
                  </p>
                  <p class="mt-1 text-3xl font-black text-emerald-400">
                    {{ winratePercent }}%
                  </p>
                  <p class="mt-1 text-xs text-slate-500">
                    {{ winrateTotal }} trades
                  </p>
                </div>
              </div>

              <div class="mt-6 grid grid-cols-3 gap-3 text-center text-sm">
                <div class="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3">
                  <p class="text-xl font-black text-emerald-400">
                    {{ winrateData.win }}
                  </p>
                  <p class="text-slate-400">
                    Win
                  </p>
                </div>

                <div class="rounded-xl border border-red-500/20 bg-red-500/10 p-3">
                  <p class="text-xl font-black text-red-400">
                    {{ winrateData.loss }}
                  </p>
                  <p class="text-slate-400">
                    Loss
                  </p>
                </div>

                <div class="rounded-xl border border-amber-500/20 bg-amber-500/10 p-3">
                  <p class="text-xl font-black text-amber-400">
                    {{ winrateData.fail }}
                  </p>
                  <p class="text-slate-400">
                    Fail
                  </p>
                </div>
              </div>
            </div>

            <div class="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg lg:col-span-2">
              <h3 class="text-lg font-bold text-white">
                Winrate Breakdown
              </h3>

              <div class="mt-5 space-y-4">
                <div>
                  <div class="mb-2 flex justify-between text-sm">
                    <span class="text-slate-300">Win</span>
                    <span class="font-semibold text-emerald-400">{{ winrateBreakdown.win }}%</span>
                  </div>
                  <div class="h-3 overflow-hidden rounded-full bg-slate-800">
                    <div class="h-full rounded-full bg-emerald-500" :style="{ width: `${winrateBreakdown.win}%` }"></div>
                  </div>
                </div>

                <div>
                  <div class="mb-2 flex justify-between text-sm">
                    <span class="text-slate-300">Loss</span>
                    <span class="font-semibold text-red-400">{{ winrateBreakdown.loss }}%</span>
                  </div>
                  <div class="h-3 overflow-hidden rounded-full bg-slate-800">
                    <div class="h-full rounded-full bg-red-500" :style="{ width: `${winrateBreakdown.loss}%` }"></div>
                  </div>
                </div>

                <div>
                  <div class="mb-2 flex justify-between text-sm">
                    <span class="text-slate-300">Fail</span>
                    <span class="font-semibold text-amber-400">{{ winrateBreakdown.fail }}%</span>
                  </div>
                  <div class="h-3 overflow-hidden rounded-full bg-slate-800">
                    <div class="h-full rounded-full bg-amber-500" :style="{ width: `${winrateBreakdown.fail}%` }"></div>
                  </div>
                </div>
              </div>

              <div class="mt-6 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
                Filter hiện tại:
                <span class="font-semibold text-slate-200">
                  {{ winrateRangeLabel }}
                </span>
                —
                dữ liệu được tính read-only từ recent live trades.
              </div>
            </div>
          </div>
        </section>

        <section class="mt-8">
          <div class="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 class="text-xl font-bold text-white">
                Trade Analytics
              </h2>
              <p class="mt-1 text-sm text-slate-500">
                Filter theo ngày sẽ tính lại analytics từ recent live trades đã tải.
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <span class="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-400">
                Symbol performance
              </span>

              <input
                v-model="analyticsFilterFrom"
                type="date"
                class="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              />

              <input
                v-model="analyticsFilterTo"
                type="date"
                class="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              />

              <button
                type="button"
                class="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700"
                @click="clearAnalyticsFilter"
              >
                Clear
              </button>
            </div>
          </div>

          <div class="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-lg">
            <div class="max-h-[420px] overflow-y-auto">
              <table class="w-full text-left text-sm">
                <thead class="sticky top-0 z-10 bg-slate-800 text-slate-300">
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
                    v-for="item in filteredTradeAnalytics"
                    :key="item.symbol"
                    class="border-t border-slate-800 hover:bg-slate-800/70"
                  >
                    <td class="p-4 font-semibold text-white">
                      {{ item.symbol }}
                    </td>
                    <td class="p-4 text-slate-300">
                      {{ item.total }}
                    </td>
                    <td class="p-4 font-semibold text-red-400">
                      {{ item.failed }}
                    </td>
                    <td class="p-4">
                      <span
                        class="rounded-full px-2 py-1 text-xs font-semibold"
                        :class="getFailRateBadgeClass(item.total > 0 ? Math.round((item.failed / item.total) * 100) : 0)"
                      >
                        {{ item.total > 0 ? Math.round((item.failed / item.total) * 100) : 0 }}%
                      </span>
                    </td>
                    <td class="p-4 text-slate-300">
                      {{ formatNumber(item.avg_notional, 4) }}
                    </td>
                  </tr>

                  <tr v-if="filteredTradeAnalytics.length === 0">
                    <td colspan="5" class="p-4 text-slate-400">
                      Chưa có dữ liệu trade analytics trong khoảng ngày đã chọn.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section class="mt-8">
          <div class="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 class="text-xl font-bold text-white">
                Recent Live Trades
              </h2>
              <p class="mt-1 text-sm text-slate-500">
                Hiển thị lệnh gần đây, chỉ đọc dữ liệu từ DB.
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <span class="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-400">
                Read-only
              </span>

              <input
                v-model="recentFilterFrom"
                type="date"
                class="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              />

              <input
                v-model="recentFilterTo"
                type="date"
                class="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              />

              <button
                type="button"
                class="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700"
                @click="clearRecentFilter"
              >
                Clear
              </button>
            </div>
          </div>

          <div class="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-lg">
            <div class="max-h-[420px] overflow-y-auto">
              <table class="w-full text-left text-sm">
                <thead class="sticky top-0 z-10 bg-slate-800 text-slate-300">
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
                    v-for="trade in filteredRecentTrades"
                    :key="trade.id"
                    class="border-t border-slate-800 hover:bg-slate-800/70"
                  >
                    <td class="p-4 font-semibold text-white">
                      {{ trade.symbol }}
                    </td>
                    <td class="p-4 text-slate-300">
                      {{ trade.side }}
                    </td>
                    <td class="p-4">
                      <span
                        class="rounded-full px-2 py-1 text-xs font-semibold"
                        :class="getTradeStatusBadgeClass(trade.status)"
                      >
                        {{ trade.status }}
                      </span>
                    </td>
                    <td class="p-4 text-slate-300">
                      {{ trade.entry_price }}
                    </td>
                    <td class="p-4 text-slate-300">
                      {{ formatNumber(trade.notional, 5) }}
                    </td>
                    <td
                      class="p-4 font-semibold"
                      :class="getPnlClass(trade.realized_pnl)"
                    >
                      {{ formatNumber(trade.realized_pnl, 5) }}
                    </td>
                    <td class="p-4 text-slate-300">
                      {{ trade.close_reason || '-' }}
                    </td>
                    <td class="p-4 text-slate-400">
                      {{ trade.created_at }}
                    </td>
                  </tr>

                  <tr v-if="filteredRecentTrades.length === 0">
                    <td colspan="8" class="p-4 text-slate-400">
                      Chưa có live trade gần đây trong khoảng ngày đã chọn.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section class="mt-8">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-xl font-bold text-white">
              Insight Center
            </h2>
            <span class="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-400">
              Auto alerts
            </span>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div
              v-for="item in insights"
              :key="item.title"
              class="rounded-2xl border p-5 shadow-lg"
              :class="getInsightCardClass(item.level)"
            >
              <div class="mb-3 flex items-center justify-between gap-3">
                <h3 class="font-bold text-white">
                  {{ item.title }}
                </h3>
                <span
                  class="rounded-full px-2 py-1 text-xs font-semibold"
                  :class="getInsightBadgeClass(item.level)"
                >
                  {{ item.level }}
                </span>
              </div>

              <p class="text-sm leading-6 text-slate-300">
                {{ item.message }}
              </p>

              <p class="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Action: {{ item.action }}
              </p>
            </div>
          </div>
        </section>

        <section class="mt-8">
          <div class="mb-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 class="text-xl font-bold text-white">
                Failed Live Trades
              </h2>
              <p class="mt-1 text-sm text-slate-500">
                Danh sách lỗi để debug, chỉ đọc dữ liệu.
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <span class="rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-xs text-red-300">
                Debug
              </span>

              <input
                v-model="failedFilterFrom"
                type="date"
                class="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              />

              <input
                v-model="failedFilterTo"
                type="date"
                class="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 outline-none focus:border-blue-500"
              />

              <button
                type="button"
                class="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700"
                @click="clearFailedFilter"
              >
                Clear
              </button>
            </div>
          </div>

          <div class="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-lg">
            <div class="max-h-[420px] overflow-y-auto">
              <table class="w-full text-left text-sm">
                <thead class="sticky top-0 z-10 bg-slate-800 text-slate-300">
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
                    v-for="trade in filteredFailedTrades"
                    :key="trade.id"
                    class="border-t border-slate-800 hover:bg-slate-800/70"
                  >
                    <td class="p-4 font-semibold text-white">
                      {{ trade.symbol }}
                    </td>
                    <td class="p-4 text-slate-300">
                      {{ trade.side }}
                    </td>
                    <td class="p-4">
                      <span
                        class="rounded-full px-2 py-1 text-xs font-semibold"
                        :class="getTradeStatusBadgeClass(trade.status)"
                      >
                        {{ trade.status }}
                      </span>
                    </td>
                    <td class="p-4 text-slate-300">
                      {{ formatNumber(trade.notional, 5) }}
                    </td>
                    <td class="p-4 text-red-300">
                      {{ trade.fail_reason }}
                    </td>
                    <td class="p-4 text-slate-400">
                      {{ trade.created_at }}
                    </td>
                  </tr>

                  <tr v-if="filteredFailedTrades.length === 0">
                    <td colspan="6" class="p-4 text-slate-400">
                      Không có live trade lỗi trong khoảng ngày đã chọn.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
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

const analyticsFilterFrom = ref('')
const analyticsFilterTo = ref('')
const recentFilterFrom = ref('')
const recentFilterTo = ref('')
const failedFilterFrom = ref('')
const failedFilterTo = ref('')
const winrateRange = ref('7d')

const formatNumber = (value: unknown, digits = 4) => {
  const numberValue = Number(value)

  if (Number.isNaN(numberValue)) {
    return value ?? '-'
  }

  return numberValue.toFixed(digits)
}

const isDateInRange = (dateValue: unknown, fromValue: string, toValue: string) => {
  if (!fromValue && !toValue) {
    return true
  }

  if (!dateValue) {
    return false
  }

  const date = new Date(String(dateValue)).getTime()

  if (Number.isNaN(date)) {
    return false
  }

  const from = fromValue ? new Date(`${fromValue}T00:00:00`).getTime() : -Infinity
  const to = toValue ? new Date(`${toValue}T23:59:59`).getTime() : Infinity

  return date >= from && date <= to
}

const filteredRecentTrades = computed(() => {
  return recentTrades.value.filter((trade) =>
    isDateInRange(trade.created_at, recentFilterFrom.value, recentFilterTo.value)
  )
})

const filteredFailedTrades = computed(() => {
  return failedTrades.value.filter((trade) =>
    isDateInRange(trade.created_at, failedFilterFrom.value, failedFilterTo.value)
  )
})

const hasAnalyticsDateFilter = computed(() => {
  return Boolean(analyticsFilterFrom.value || analyticsFilterTo.value)
})

const filteredTradeAnalytics = computed(() => {
  if (!hasAnalyticsDateFilter.value) {
    return tradeAnalytics.value
  }

  const grouped = new Map<string, { symbol: string; total: number; failed: number; notionalSum: number }>()

  recentTrades.value
    .filter((trade) => isDateInRange(trade.created_at, analyticsFilterFrom.value, analyticsFilterTo.value))
    .forEach((trade) => {
      const symbol = String(trade.symbol || 'UNKNOWN')
      const current = grouped.get(symbol) || {
        symbol,
        total: 0,
        failed: 0,
        notionalSum: 0
      }

      current.total += 1

      if (trade.status === 'FAILED') {
        current.failed += 1
      }

      current.notionalSum += Number(trade.notional || 0)

      grouped.set(symbol, current)
    })

  return Array.from(grouped.values()).map((item) => ({
    symbol: item.symbol,
    total: item.total,
    failed: item.failed,
    avg_notional: item.total > 0 ? item.notionalSum / item.total : 0
  }))
})

const getWinrateStartTime = () => {
  const now = Date.now()

  switch (winrateRange.value) {
    case '7d':
      return now - 7 * 24 * 60 * 60 * 1000
    case '30d':
      return now - 30 * 24 * 60 * 60 * 1000
    case '90d':
      return now - 90 * 24 * 60 * 60 * 1000
    case '365d':
      return now - 365 * 24 * 60 * 60 * 1000
    default:
      return 0
  }
}

const winrateRangeLabel = computed(() => {
  switch (winrateRange.value) {
    case '7d':
      return '7 ngày gần nhất'
    case '30d':
      return 'Tháng gần nhất'
    case '90d':
      return 'Quý gần nhất'
    case '365d':
      return 'Năm gần nhất'
    default:
      return 'Tất cả'
  }
})

const winrateFilteredTrades = computed(() => {
  const start = getWinrateStartTime()

  return recentTrades.value.filter((trade) => {
    const createdAt = new Date(String(trade.created_at)).getTime()

    if (Number.isNaN(createdAt)) {
      return false
    }

    return createdAt >= start
  })
})

const winrateData = computed(() => {
  let win = 0
  let loss = 0
  let fail = 0

  winrateFilteredTrades.value.forEach((trade) => {
    const pnl = Number(trade.realized_pnl)

    if (trade.status === 'FAILED') {
      fail += 1
      return
    }

    if (trade.status === 'CLOSED' && pnl > 0) {
      win += 1
      return
    }

    if (trade.status === 'CLOSED' && pnl < 0) {
      loss += 1
    }
  })

  return {
    win,
    loss,
    fail
  }
})

const winrateTotal = computed(() => {
  return winrateData.value.win + winrateData.value.loss + winrateData.value.fail
})

const winratePercent = computed(() => {
  if (winrateTotal.value === 0) {
    return 0
  }

  return Math.round((winrateData.value.win / winrateTotal.value) * 100)
})

const winrateBreakdown = computed(() => {
  if (winrateTotal.value === 0) {
    return {
      win: 0,
      loss: 0,
      fail: 0
    }
  }

  return {
    win: Math.round((winrateData.value.win / winrateTotal.value) * 100),
    loss: Math.round((winrateData.value.loss / winrateTotal.value) * 100),
    fail: Math.round((winrateData.value.fail / winrateTotal.value) * 100)
  }
})

const winratePieBackground = computed(() => {
  if (winrateTotal.value === 0) {
    return 'conic-gradient(#334155 0deg 360deg)'
  }

  const winDeg = (winrateData.value.win / winrateTotal.value) * 360
  const lossDeg = (winrateData.value.loss / winrateTotal.value) * 360
  const failDeg = 360 - winDeg - lossDeg

  const winEnd = winDeg
  const lossEnd = winDeg + lossDeg
  const failEnd = winDeg + lossDeg + failDeg

  return `conic-gradient(#22c55e 0deg ${winEnd}deg, #ef4444 ${winEnd}deg ${lossEnd}deg, #f59e0b ${lossEnd}deg ${failEnd}deg)`
})

const clearAnalyticsFilter = () => {
  analyticsFilterFrom.value = ''
  analyticsFilterTo.value = ''
}

const clearRecentFilter = () => {
  recentFilterFrom.value = ''
  recentFilterTo.value = ''
}

const clearFailedFilter = () => {
  failedFilterFrom.value = ''
  failedFilterTo.value = ''
}

const getPnlClass = (value: unknown) => {
  const numberValue = Number(value)

  if (numberValue > 0) {
    return 'text-emerald-400'
  }

  if (numberValue < 0) {
    return 'text-red-400'
  }

  return 'text-slate-300'
}

const getRiskTextClass = (value: unknown) => {
  if (value === 'LOW') {
    return 'text-emerald-400'
  }

  if (value === 'MEDIUM') {
    return 'text-amber-400'
  }

  if (value === 'HIGH') {
    return 'text-red-400'
  }

  return 'text-slate-300'
}

const getStrategyTextClass = (value: unknown) => {
  if (value === 'GOOD') {
    return 'text-emerald-400'
  }

  if (value === 'WEAK') {
    return 'text-red-400'
  }

  return 'text-slate-300'
}

const getRiskBadgeClass = (value: unknown) => {
  if (value === 'LOW') {
    return 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
  }

  if (value === 'MEDIUM') {
    return 'border border-amber-500/30 bg-amber-500/10 text-amber-300'
  }

  if (value === 'HIGH') {
    return 'border border-red-500/30 bg-red-500/10 text-red-300'
  }

  return 'border border-slate-700 bg-slate-900 text-slate-300'
}

const getStrategyBadgeClass = (value: unknown) => {
  if (value === 'GOOD') {
    return 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
  }

  if (value === 'WEAK') {
    return 'border border-red-500/30 bg-red-500/10 text-red-300'
  }

  return 'border border-slate-700 bg-slate-900 text-slate-300'
}

const getTradeStatusBadgeClass = (value: unknown) => {
  if (value === 'CLOSED') {
    return 'bg-emerald-500/10 text-emerald-300'
  }

  if (value === 'FAILED') {
    return 'bg-red-500/10 text-red-300'
  }

  if (value === 'OPEN') {
    return 'bg-amber-500/10 text-amber-300'
  }

  return 'bg-slate-700 text-slate-300'
}

const getFailRateBadgeClass = (value: number) => {
  if (value >= 70) {
    return 'bg-red-500/10 text-red-300'
  }

  if (value >= 30) {
    return 'bg-amber-500/10 text-amber-300'
  }

  return 'bg-emerald-500/10 text-emerald-300'
}

const getInsightCardClass = (level: unknown) => {
  if (level === 'danger') {
    return 'border-red-500/30 bg-red-500/10'
  }

  if (level === 'warning') {
    return 'border-amber-500/30 bg-amber-500/10'
  }

  return 'border-slate-800 bg-slate-900'
}

const getInsightBadgeClass = (level: unknown) => {
  if (level === 'danger') {
    return 'bg-red-500/20 text-red-300'
  }

  if (level === 'warning') {
    return 'bg-amber-500/20 text-amber-300'
  }

  return 'bg-blue-500/20 text-blue-300'
}

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
