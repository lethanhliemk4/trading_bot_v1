export const useApi = () => {
  const config = useRuntimeConfig()
  const base = config.public.apiBase

  const get = async (path: string) => {
    try {
      const res = await $fetch(`${base}${path}`)
      return res
    } catch (err: any) {
      console.error("API GET ERROR:", err)
      return null
    }
  }

  const post = async (path: string, body?: any) => {
    try {
      const res = await $fetch(`${base}${path}`, {
        method: "POST",
        body,
      })
      return res
    } catch (err: any) {
      console.error("API POST ERROR:", err)
      return null
    }
  }

  return {
    get,
    post,
  }
}