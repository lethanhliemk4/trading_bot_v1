export const useApi = () => {
  const config = useRuntimeConfig()

  const baseURL =
    config.public.apiBase ||
    "http://127.0.0.1:8000"

  const request = async (url: string, options: any = {}) => {
    try {
      const res = await $fetch(url, {
        baseURL,
        ...options,
      })

      return res
    } catch (err: any) {
      console.error("API ERROR:", err)

      return null
    }
  }

  const get = (url: string) => {
    return request(url, { method: "GET" })
  }

  const post = (url: string, body: any) => {
    return request(url, {
      method: "POST",
      body,
    })
  }

  return {
    get,
    post,
  }
}