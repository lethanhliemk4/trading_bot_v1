<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <p class="text-sm text-slate-500">{{ label }}</p>
    <p class="mt-2 text-2xl font-bold text-slate-900">{{ value }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
}>()
</script>