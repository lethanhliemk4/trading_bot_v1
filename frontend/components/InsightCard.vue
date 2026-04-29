<template>
  <div class="rounded-2xl border bg-white p-5 shadow-sm">
    <div class="flex items-center justify-between gap-3">
      <h3 class="font-semibold text-slate-900">{{ title }}</h3>
      <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="badgeClass">
        {{ level }}
      </span>
    </div>

    <p class="mt-3 text-sm text-slate-600">
      {{ message }}
    </p>

    <p class="mt-4 text-xs font-semibold text-slate-500">
      Action: {{ action }}
    </p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  level: string
  title: string
  message: string
  action: string
}>()

const badgeClass = computed(() => {
  if (props.level === "warning") return "bg-yellow-100 text-yellow-700"
  if (props.level === "danger") return "bg-red-100 text-red-700"
  return "bg-blue-100 text-blue-700"
})
</script>