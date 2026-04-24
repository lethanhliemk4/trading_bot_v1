<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Live Trades</h1>

      <button
        class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-slate-800 text-slate-300">
          <tr>
            <th class="p-3 text-left">ID</th>
            <th class="p-3 text-left">Symbol</th>
            <th class="p-3 text-left">Side</th>
            <th class="p-3 text-left">Status</th>
            <th class="p-3 text-right">Entry</th>
            <th class="p-3 text-right">Exit</th>
            <th class="p-3 text-right">Qty</th>
            <th class="p-3 text-right">PnL</th>
            <th class="p-3 text-right">Result</th>
            <th class="p-3 text-left">Reason</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="trade in trades"
            :key="trade.id"
            class="border-t border-slate-800 hover:bg-slate-800/50"
          >
            <td class="p-3">{{ trade.id }}</td>
            <td class="p-3 font-semibold">{{ trade.symbol }}</td>
            <td class="p-3">
              <span
                class="px-2 py-1 rounded text-xs"
                :class="trade.side === 'LONG' ? 'bg-green-700' : 'bg-red-700'"
              >
                {{ trade.side }}
              </span>
            </td>
            <td class="p-3">
              <span
                class="px-2 py-1 rounded text-xs"
                :class="statusClass(trade.status)"
              >
                {{ trade.status }}
              </span>
            </td>
            <td class="p-3 text-right">{{ formatNum(trade.entry_price) }}</td>
            <td class="p-3 text-right">{{ formatNum(trade.exit_price) }}</td>
            <td class="p-3 text-right">{{ formatNum(trade.executed_qty) }}</td>
            <td
              class="p-3 text-right font-semibold"
              :class="pnlClass(trade.realized_pnl)"
            >
              {{ formatNum(trade.realized_pnl) }}
            </td>
            <td
              class="p-3 text-right font-semibold"
              :class="pnlClass(trade.result_percent)"
            >
              {{ formatNum(trade.result_percent) }}%
            </td>
            <td class="p-3 text-slate-300">
              {{ trade.close_reason || trade.fail_reason || "-" }}
            </td>
          </tr>

          <tr v-if="!trades.length">
            <td colspan="10" class="p-6 text-center text-slate-400">
              No live trades yet
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()

const trades = ref<any[]>([])

const load = async () => {
  const data: any = await get("/api/dashboard/live-trades")
  trades.value = data?.items || []
}

const formatNum = (value: any) => {
  const n = Number(value || 0)
  return n.toFixed(6)
}

const pnlClass = (value: any) => {
  const n = Number(value || 0)
  if (n > 0) return "text-green-400"
  if (n < 0) return "text-red-400"
  return "text-slate-300"
}

const statusClass = (status: string) => {
  if (status === "OPEN") return "bg-blue-700"
  if (status === "CLOSED") return "bg-green-700"
  if (status === "FAILED") return "bg-red-700"
  return "bg-slate-700"
}

onMounted(() => {
  load()
  setInterval(load, 5000)
})
</script>