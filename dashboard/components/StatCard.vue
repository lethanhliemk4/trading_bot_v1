<template>
  <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4">
    <div class="text-sm text-slate-400 mb-1">
      {{ label }}
    </div>

    <div class="text-2xl font-bold">
      {{ value }}
    </div>

    <div v-if="sub" class="text-xs text-slate-500 mt-1">
      {{ sub }}
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  sub?: string
}>()
</script>