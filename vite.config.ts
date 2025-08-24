import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    host: '127.0.0.1',
    strictPort: true
  },
  build: {
    sourcemap: true
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx']
  },
  optimizeDeps: {
    include: ['react', 'react-dom', '@convex-dev/auth/react', 'convex/react']
  }
})
