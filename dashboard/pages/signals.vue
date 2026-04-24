<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Signals</h1>

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
            <th class="p-3 text-right">Score</th>
            <th class="p-3 text-right">5m %</th>
            <th class="p-3 text-right">Volume</th>
            <th class="p-3 text-right">Spike</th>
            <th class="p-3 text-right">Entry</th>
            <th class="p-3 text-left">Status</th>
            <th class="p-3 text-left">Created</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="signal in signals"
            :key="signal.id"
            class="border-t border-slate-800 hover:bg-slate-800/50"
          >
            <td class="p-3">{{ signal.id }}</td>
            <td class="p-3 font-semibold">{{ signal.symbol }}</td>
            <td class="p-3">
              <span
                class="px-2 py-1 rounded text-xs"
                :class="signal.side === 'LONG' ? 'bg-green-700' : 'bg-red-700'"
              >
                {{ signal.side }}
              </span>
            </td>
            <td class="p-3 text-right">{{ formatNum(signal.score, 0) }}</td>
            <td
              class="p-3 text-right"
              :class="pnlClass(signal.price_change_5m)"
            >
              {{ formatNum(signal.price_change_5m, 2) }}%
            </td>
            <td class="p-3 text-right">
              {{ formatVolume(signal.quote_volume_5m) }}
            </td>
            <td class="p-3 text-right">
              x{{ formatNum(signal.volume_spike_ratio, 2) }}
            </td>
            <td class="p-3 text-right">
              {{ formatNum(signal.entry_price, 6) }}
            </td>
            <td class="p-3">
              <span class="px-2 py-1 rounded text-xs bg-slate-700">
                {{ signal.status }}
              </span>
            </td>
            <td class="p-3 text-slate-400">
              {{ signal.created_at || "-" }}
            </td>
          </tr>

          <tr v-if="!signals.length">
            <td colspan="10" class="p-6 text-center text-slate-400">
              No signals yet
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()

const signals = ref<any[]>([])

const load = async () => {
  const data: any = await get("/api/dashboard/signals")
  signals.value = data?.items || []
}

const formatNum = (value: any, digits = 2) => {
  const n = Number(value || 0)
  return n.toFixed(digits)
}

const formatVolume = (value: any) => {
  const n = Number(value || 0)
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(2)}K`
  return n.toFixed(2)
}

const pnlClass = (value: any) => {
  const n = Number(value || 0)
  if (n > 0) return "text-green-400"
  if (n < 0) return "text-red-400"
  return "text-slate-300"
}

onMounted(() => {
  load()
  setInterval(load, 5000)
})
</script>