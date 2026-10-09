import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The config runs in Node; declared here so the app's tsconfig needn't pull in @types/node.
declare const process: { env: Record<string, string | undefined> }

// Where `npm run dev` sends /api requests: the local engine (server/).
const engine = process.env.ENGINE_URL ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // host: true so a phone on the same Wi-Fi can open the mobile layout.
    host: true,
    proxy: { '/api': { target: engine, changeOrigin: true } },
  },
})
