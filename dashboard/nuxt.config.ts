export default defineNuxtConfig({
  compatibilityDate: "2026-04-25",

  modules: ["@nuxtjs/tailwindcss"],

  css: ["~/assets/css/main.css"],

  tailwindcss: {
    cssPath: "~/assets/css/main.css",
    configPath: "tailwind.config.js",
  },

  runtimeConfig: {
    public: {
      apiBase:
        process.env.NUXT_PUBLIC_API_BASE ||
        "http://127.0.0.1:8000",
    },
  },

  devtools: {
    enabled: true,
  },

  // 🔥 QUAN TRỌNG khi deploy VPS
  app: {
    head: {
      title: "Trading Bot Dashboard",
      meta: [
        { name: "viewport", content: "width=device-width, initial-scale=1" },
      ],
    },
  },

  // 🔥 Fix lỗi CORS / fetch khi deploy
  nitro: {
    devProxy: {
      "/api": {
        target:
          process.env.NUXT_PUBLIC_API_BASE ||
          "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
})