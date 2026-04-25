<template>
  <div class="rounded-xl border border-slate-800 bg-slate-950 p-4">
    <div class="text-xs text-slate-500">{{ label }}</div>
    <div class="mt-1 text-base font-semibold text-slate-100">
      {{ value ?? "-" }}
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: any
}>()
</script>