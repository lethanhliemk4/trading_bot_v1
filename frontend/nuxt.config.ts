export default defineNuxtConfig({
  ssr: false,

  modules: ["@nuxtjs/tailwindcss"],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://127.0.0.1:8001"
    }
  },

  devtools: { enabled: false },
  compatibilityDate: "2026-04-29"
})