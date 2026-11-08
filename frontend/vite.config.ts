import { defineConfig } from 'vite'
import path from 'node:path'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  // O .env fica na raiz do repositório, compartilhado com o backend.
  // Só as variáveis com prefixo VITE_ são expostas ao navegador.
  envDir: path.resolve(__dirname, '..'),
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@':  path.resolve(__dirname, 'src'),
    },
  },
})