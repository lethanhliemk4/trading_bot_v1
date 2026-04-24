<template>
  <div class="min-h-screen flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-slate-900 border-r border-slate-800 p-4">
      <h1 class="text-xl font-bold mb-6">🚀 Trading Bot</h1>

      <nav class="space-y-2">
        <NuxtLink to="/" class="block p-2 rounded hover:bg-slate-800">
          Overview
        </NuxtLink>
        <NuxtLink to="/live-trades" class="block p-2 rounded hover:bg-slate-800">
          Live Trades
        </NuxtLink>
        <NuxtLink to="/signals" class="block p-2 rounded hover:bg-slate-800">
          Signals
        </NuxtLink>
        <NuxtLink to="/risk" class="block p-2 rounded hover:bg-slate-800">
          Risk
        </NuxtLink>
        <NuxtLink to="/logs" class="block p-2 rounded hover:bg-slate-800">
          Logs
        </NuxtLink>
        <NuxtLink to="/settings" class="block p-2 rounded hover:bg-slate-800">
          Settings
        </NuxtLink>
      </nav>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col">
      <!-- Header -->
      <header class="h-16 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-900">
        <div class="text-sm text-slate-400">
          Trading Dashboard
        </div>

        <div class="flex items-center gap-4 text-sm">
          <span class="px-2 py-1 rounded bg-green-600">LIVE</span>
          <span class="px-2 py-1 rounded bg-slate-700">USDT</span>
        </div>
      </header>

      <!-- Content -->
      <main class="p-6">
        <NuxtPage />
      </main>
    </div>
  </div>
</template>