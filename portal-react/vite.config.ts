// portal-react/vite.config.ts (ou .js)
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Redireciona todas as requisições que começam com /api/v1
      // para o seu backend FastAPI
      '/api/v1': {
        target: 'http://127.0.0.1:8000', // A porta do seu FastAPI
        changeOrigin: true,
      },
    },
  },
})