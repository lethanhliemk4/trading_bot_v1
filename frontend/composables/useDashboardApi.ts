export const useDashboardApi = () => {
  const config = useRuntimeConfig()

  const apiBase = config.public.apiBase

  const getOverview = async () => {
    return await $fetch(`${apiBase}/api/dashboard/overview`)
  }

  const getInsights = async () => {
    return await $fetch(`${apiBase}/api/dashboard/insights`)
  }

  return {
    getOverview,
    getInsights
  }
}