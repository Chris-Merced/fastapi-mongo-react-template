import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Any request the frontend makes to /api/* gets forwarded to FastAPI,
      // with /api stripped. So fetch("/api/auth/login") really hits
      // http://localhost:8000/auth/login. The browser only ever sees
      // same-origin requests, so no CORS config is needed at all - this
      // is dev-server-only behavior (Vite proxies it); production would
      // need a real reverse proxy or the API's own CORS headers.
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
})
