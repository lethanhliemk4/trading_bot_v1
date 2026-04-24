<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Settings</h1>

      <button
        class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4">
      <h2 class="text-lg font-semibold mb-4">Bot Runtime</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">Trade Mode</div>
          <div class="text-xl font-bold">
            {{ overview?.bot?.trade_mode || "-" }}
          </div>
        </div>

        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">Auto Trade</div>
          <div class="text-xl font-bold">
            {{ overview?.bot?.auto_trade_enabled ? "ON" : "OFF" }}
          </div>
        </div>

        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">App Env</div>
          <div class="text-xl font-bold">
            {{ overview?.bot?.app_env || "-" }}
          </div>
        </div>

        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">Kill Switch</div>
          <div
            class="text-xl font-bold"
            :class="overview?.bot?.kill_switch ? 'text-red-400' : 'text-green-400'"
          >
            {{ overview?.bot?.kill_switch ? "ON" : "OFF" }}
          </div>
        </div>

        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">Binance Env</div>
          <div class="text-xl font-bold">
            {{ overview?.account?.binance_use_testnet ? "TESTNET" : "MAINNET" }}
          </div>
        </div>

        <div class="p-4 rounded-xl bg-slate-800">
          <div class="text-slate-400">Live Armed</div>
          <div
            class="text-xl font-bold"
            :class="overview?.account?.live_execution_armed ? 'text-green-400' : 'text-red-400'"
          >
            {{ overview?.account?.live_execution_armed ? "YES" : "NO" }}
          </div>
        </div>
      </div>
    </div>

    <div class="mt-6 bg-slate-900 border border-slate-800 rounded-2xl p-4">
      <h2 class="text-lg font-semibold mb-2">Note</h2>
      <p class="text-sm text-slate-400">
        Settings page hiện chỉ để xem trạng thái. Không chỉnh trực tiếp từ dashboard để tránh thao tác nhầm khi bot đang chạy live.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { get } = useApi()

const overview = ref<any>(null)

const load = async () => {
  overview.value = await get("/api/dashboard/overview")
}

onMounted(() => {
  load()
  setInterval(load, 5000)
})
</script>