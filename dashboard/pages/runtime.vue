<template>
  <div>
    <div class="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Runtime</h1>
        <p class="text-sm text-slate-400">
          Theo dõi watchdog loop: scanner, paper, live và performance.
        </p>
      </div>

      <button
        class="rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <section class="mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <h2 class="mb-4 text-lg font-semibold">Watchdog Threshold</h2>
      <InfoRow label="Stale Threshold" :value="`${runtime?.threshold_seconds ?? 0}s`" />
    </section>

    <section class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div
        v-for="item in loopItems"
        :key="item.name"
        class="rounded-2xl border p-4"
        :class="item.stale ? 'border-red-500/40 bg-red-500/10' : 'border-slate-800 bg-slate-900'"
      >
        <div class="mb-2 flex items-center justify-between">
          <h2 class="font-semibold">{{ item.name }}</h2>
          <span :class="item.stale ? 'text-red-300' : 'text-emerald-300'">
            {{ item.stale ? "STALE" : "OK" }}
          </span>
        </div>

        <div class="space-y-2 text-sm text-slate-300">
          <div>Age: {{ item.age_seconds ?? "-" }}s</div>
          <div>Last seen: {{ formatTime(item.last_seen) }}</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()

const runtime = ref<any>(null)

const load = async () => {
  const res = await get("/api/dashboard/runtime")
  if (res) runtime.value = res
}

const loopItems = computed(() => {
  return [
    {
      name: "Scanner",
      ...(runtime.value?.scanner_loop ?? {}),
    },
    {
      name: "Paper Trade",
      ...(runtime.value?.paper_trade_loop ?? {}),
    },
    {
      name: "Live Trade",
      ...(runtime.value?.live_trade_loop ?? {}),
    },
    {
      name: "Performance",
      ...(runtime.value?.performance_loop ?? {}),
    },
  ]
})

const formatTime = (value: any) => {
  if (!value) return "-"
  return new Date(Number(value) * 1000).toLocaleString()
}

onMounted(() => {
  load()
})
</script>