<template>
  <div>
    <div class="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Live Trades</h1>
        <p class="text-sm text-slate-400">
          Theo dõi lệnh live/testnet, trạng thái TP1, trailing, PnL và lỗi khớp lệnh.
        </p>
      </div>

      <button
        class="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-4">
      <StatCard label="Total" :value="items.length" />
      <StatCard label="Open" :value="countByStatus('OPEN')" />
      <StatCard label="Closed" :value="countByStatus('CLOSED')" />
      <StatCard label="Failed" :value="countByStatus('FAILED')" />
    </div>

    <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <h2 class="text-lg font-semibold">Latest Live Trades</h2>

        <select
          v-model="statusFilter"
          class="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
        >
          <option value="">All status</option>
          <option value="OPEN">OPEN</option>
          <option value="CLOSED">CLOSED</option>
          <option value="FAILED">FAILED</option>
        </select>
      </div>

      <div v-if="loading" class="py-6 text-sm text-slate-400">
        Loading live trades...
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="py-3 pr-4">ID</th>
              <th class="py-3 pr-4">Symbol</th>
              <th class="py-3 pr-4">Side</th>
              <th class="py-3 pr-4">Status</th>
              <th class="py-3 pr-4">Env</th>
              <th class="py-3 pr-4">Entry</th>
              <th class="py-3 pr-4">Exit</th>
              <th class="py-3 pr-4">Qty</th>
              <th class="py-3 pr-4">Remaining</th>
              <th class="py-3 pr-4">PnL</th>
              <th class="py-3 pr-4">Result %</th>
              <th class="py-3 pr-4">TP1</th>
              <th class="py-3 pr-4">Trailing</th>
              <th class="py-3 pr-4">Trailing SL</th>
              <th class="py-3 pr-4">Close Reason</th>
              <th class="py-3 pr-4">Fail Reason</th>
              <th class="py-3 pr-4">Created</th>
              <th class="py-3 pr-4">Closed</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="trade in filteredItems"
              :key="trade.id"
              class="border-t border-slate-800 align-top"
            >
              <td class="py-3 pr-4 text-slate-500">{{ trade.id }}</td>
              <td class="py-3 pr-4 font-semibold">{{ trade.symbol }}</td>
              <td class="py-3 pr-4">{{ trade.side }}</td>
              <td class="py-3 pr-4">
                <span :class="statusClass(trade.status)">
                  {{ trade.status }}
                </span>
              </td>
              <td class="py-3 pr-4">{{ trade.environment }}</td>
              <td class="py-3 pr-4">{{ formatNumber(trade.entry_price, 6) }}</td>
              <td class="py-3 pr-4">{{ formatNumber(trade.exit_price, 6) }}</td>
              <td class="py-3 pr-4">{{ formatNumber(trade.executed_qty, 8) }}</td>
              <td class="py-3 pr-4">{{ formatNumber(trade.remaining_qty, 8) }}</td>
              <td class="py-3 pr-4" :class="numberClass(trade.realized_pnl)">
                {{ formatNumber(trade.realized_pnl, 4) }}
              </td>
              <td class="py-3 pr-4" :class="numberClass(trade.result_percent)">
                {{ formatNumber(trade.result_percent, 2) }}%
              </td>
              <td class="py-3 pr-4">{{ boolText(trade.tp1_hit) }}</td>
              <td class="py-3 pr-4">{{ boolText(trade.trailing_active) }}</td>
              <td class="py-3 pr-4">{{ formatNumber(trade.trailing_sl, 6) }}</td>
              <td class="py-3 pr-4 text-slate-300">{{ trade.close_reason || "-" }}</td>
              <td class="max-w-[320px] py-3 pr-4 text-red-300">
                {{ trade.fail_reason || "-" }}
              </td>
              <td class="py-3 pr-4 text-slate-400">{{ formatDate(trade.created_at) }}</td>
              <td class="py-3 pr-4 text-slate-400">{{ formatDate(trade.closed_at) }}</td>
            </tr>

            <tr v-if="filteredItems.length === 0">
              <td colspan="18" class="py-6 text-slate-500">
                Không có live trade phù hợp.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import StatCard from "~/components/StatCard.vue"

const { get } = useApi()

const loading = ref(false)
const statusFilter = ref("")
const data = ref<any>({ items: [] })

const items = computed(() => data.value?.items ?? [])

const filteredItems = computed(() => {
  if (!statusFilter.value) return items.value
  return items.value.filter((item: any) => item.status === statusFilter.value)
})

const load = async () => {
  loading.value = true

  const res = await get("/api/dashboard/live-trades?limit=100")
  if (res) data.value = res

  loading.value = false
}

const countByStatus = (status: string) => {
  return items.value.filter((item: any) => item.status === status).length
}

const formatNumber = (value: any, digits = 2) => {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n.toFixed(digits) : "0"
}

const boolText = (value: any) => {
  return value ? "YES" : "NO"
}

const numberClass = (value: any) => {
  const n = Number(value ?? 0)
  if (n > 0) return "text-emerald-400"
  if (n < 0) return "text-red-400"
  return "text-slate-300"
}

const statusClass = (status: string) => {
  if (status === "OPEN") return "rounded-lg bg-cyan-500/10 px-2 py-1 text-cyan-300"
  if (status === "CLOSED") return "rounded-lg bg-emerald-500/10 px-2 py-1 text-emerald-300"
  if (status === "FAILED") return "rounded-lg bg-red-500/10 px-2 py-1 text-red-300"
  return "rounded-lg bg-slate-700 px-2 py-1 text-slate-300"
}

const formatDate = (value: any) => {
  if (!value) return "-"
  return new Date(value).toLocaleString()
}

onMounted(load)
</script>