export const useDashboardApi = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  const getOverview = async () => {
    return await $fetch(`${apiBase}/api/dashboard/overview`)
  }

  const getInsights = async () => {
    return await $fetch(`${apiBase}/api/dashboard/insights`)
  }

  const getFailedLiveTrades = async () => {
    return await $fetch(`${apiBase}/api/dashboard/live-trades/errors`)
  }

  const getTradingSummary = async () => {
    return await $fetch(`${apiBase}/api/dashboard/trading-summary`)
  }

  const getTradeAnalytics = async () => {
    return await $fetch(`${apiBase}/api/dashboard/trade-analytics`)
  }

  return {
    getOverview,
    getInsights,
    getFailedLiveTrades,
    getTradingSummary,
    getTradeAnalytics
  }
}