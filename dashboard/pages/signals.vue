<template>
  <div>
    <div class="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Signals</h1>
        <p class="text-sm text-slate-400">
          Danh sách signal mới nhất, kết quả 5m/15m, max profit và max drawdown.
        </p>
      </div>

      <button
        class="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <section class="rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <h2 class="text-lg font-semibold">Latest Signals</h2>

        <input
          v-model="search"
          placeholder="Search symbol..."
          class="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 outline-none focus:border-cyan-500"
        />
      </div>

      <div v-if="loading" class="py-6 text-sm text-slate-400">
        Loading signals...
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="py-3 pr-4">ID</th>
              <th class="py-3 pr-4">Symbol</th>
              <th class="py-3 pr-4">Side</th>
              <th class="py-3 pr-4">Score</th>
              <th class="py-3 pr-4">5m Change</th>
              <th class="py-3 pr-4">Quote Vol</th>
              <th class="py-3 pr-4">Spike</th>
              <th class="py-3 pr-4">Entry</th>
              <th class="py-3 pr-4">Status</th>
              <th class="py-3 pr-4">Result 5m</th>
              <th class="py-3 pr-4">Result 15m</th>
              <th class="py-3 pr-4">Max Profit</th>
              <th class="py-3 pr-4">Max DD</th>
              <th class="py-3 pr-4">Created</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="signal in filteredItems"
              :key="signal.id"
              class="border-t border-slate-800"
            >
              <td class="py-3 pr-4 text-slate-500">{{ signal.id }}</td>
              <td class="py-3 pr-4 font-semibold">{{ signal.symbol }}</td>
              <td class="py-3 pr-4">{{ signal.side }}</td>
              <td class="py-3 pr-4">
                <span :class="scoreClass(signal.score)">
                  {{ formatNumber(signal.score, 0) }}
                </span>
              </td>
              <td class="py-3 pr-4" :class="numberClass(signal.price_change_5m)">
                {{ formatNumber(signal.price_change_5m, 2) }}%
              </td>
              <td class="py-3 pr-4">
                {{ formatCompact(signal.quote_volume_5m) }}
              </td>
              <td class="py-3 pr-4">
                x{{ formatNumber(signal.volume_spike_ratio, 2) }}
              </td>
              <td class="py-3 pr-4">
                {{ formatNumber(signal.entry_price, 6) }}
              </td>
              <td class="py-3 pr-4">{{ signal.status }}</td>
              <td class="py-3 pr-4" :class="numberClass(signal.result_5m)">
                {{ formatOptionalPercent(signal.result_5m) }}
              </td>
              <td class="py-3 pr-4" :class="numberClass(signal.result_15m)">
                {{ formatOptionalPercent(signal.result_15m) }}
              </td>
              <td class="py-3 pr-4" :class="numberClass(signal.max_profit)">
                {{ formatOptionalPercent(signal.max_profit) }}
              </td>
              <td class="py-3 pr-4" :class="numberClass(signal.max_drawdown)">
                {{ formatOptionalPercent(signal.max_drawdown) }}
              </td>
              <td class="py-3 pr-4 text-slate-400">
                {{ formatDate(signal.created_at) }}
              </td>
            </tr>

            <tr v-if="filteredItems.length === 0">
              <td colspan="14" class="py-6 text-slate-500">
                Không có signal phù hợp.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()

const loading = ref(false)
const search = ref("")
const data = ref<any>({ items: [] })

const items = computed(() => data.value?.items ?? [])

const filteredItems = computed(() => {
  const keyword = search.value.trim().toUpperCase()
  if (!keyword) return items.value

  return items.value.filter((item: any) =>
    String(item.symbol || "").toUpperCase().includes(keyword)
  )
})

const load = async () => {
  loading.value = true

  const res = await get("/api/dashboard/signals?limit=100")
  if (res) data.value = res

  loading.value = false
}

const formatNumber = (value: any, digits = 2) => {
  const n = Number(value ?? 0)
  return Number.isFinite(n) ? n.toFixed(digits) : "0"
}

const formatOptionalPercent = (value: any) => {
  if (value === null || value === undefined) return "-"
  return `${formatNumber(value, 2)}%`
}

const formatCompact = (value: any) => {
  const n = Number(value ?? 0)

  if (!Number.isFinite(n)) return "0"
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(2)}K`

  return n.toFixed(2)
}

const numberClass = (value: any) => {
  const n = Number(value ?? 0)

  if (n > 0) return "text-emerald-400"
  if (n < 0) return "text-red-400"

  return "text-slate-300"
}

const scoreClass = (score: any) => {
  const n = Number(score ?? 0)

  if (n >= 80) return "rounded-lg bg-red-500/10 px-2 py-1 text-red-300"
  if (n >= 60) return "rounded-lg bg-yellow-500/10 px-2 py-1 text-yellow-300"

  return "rounded-lg bg-slate-700 px-2 py-1 text-slate-300"
}

const formatDate = (value: any) => {
  if (!value) return "-"
  return new Date(value).toLocaleString()
}

onMounted(load)
</script>