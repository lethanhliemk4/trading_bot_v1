<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Logs / Events</h1>

      <button
        class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4">
      <h2 class="text-lg font-semibold mb-4">Recent Trade Events</h2>

      <div v-if="events.length" class="space-y-3">
        <div
          v-for="event in events"
          :key="event.id"
          class="p-4 rounded-xl bg-slate-800 border border-slate-700"
        >
          <div class="flex items-center justify-between">
            <div class="font-semibold">
              {{ event.symbol }} | {{ event.status }}
            </div>

            <div class="text-xs text-slate-400">
              {{ event.created_at || "-" }}
            </div>
          </div>

          <div class="mt-2 text-sm text-slate-300">
            Side: {{ event.side }} |
            Result: {{ formatNum(event.result_percent) }}% |
            PnL: {{ formatNum(event.realized_pnl) }} USDT
          </div>

          <div class="mt-1 text-sm text-slate-400">
            Reason:
            {{ event.close_reason || event.fail_reason || "N/A" }}
          </div>
        </div>
      </div>

      <div v-else class="text-slate-400 text-center py-8">
        No events yet
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()

const events = ref<any[]>([])

const load = async () => {
  const data: any = await get("/api/dashboard/live-trades")
  events.value = data?.items || []
}

const formatNum = (value: any) => {
  const n = Number(value || 0)
  return n.toFixed(4)
}

onMounted(() => {
  load()
  setInterval(load, 5000)
})
</script>