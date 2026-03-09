import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return;

          // React core + routing (stable, cache-friendly)
          if (
            id.includes('/react/') ||
            id.includes('/react-dom/') ||
            id.includes('/react-router') ||
            id.includes('/scheduler/')
          ) {
            return 'vendor-react';
          }

          // UI framework: Nordlig DS + Radix primitives + all transitive deps.
          // @nordlig/components is a single-file ESM monolith that statically
          // imports Radix UI, TipTap, recharts v3 etc. — tree-shaking cannot
          // remove unused components because the bundle is pre-compiled.
          // We group everything the UI framework pulls in together so it caches
          // as one unit and updates only when the DS version changes.
          if (
            id.includes('/@nordlig/') ||
            id.includes('/@radix-ui/') ||
            id.includes('/@tiptap/') ||
            id.includes('/prosemirror-') ||
            id.includes('/clsx/') ||
            id.includes('/tailwind-merge/') ||
            id.includes('/class-variance-authority/') ||
            id.includes('/cmdk/') ||
            id.includes('/vaul/') ||
            id.includes('/input-otp/') ||
            id.includes('/react-resizable-panels/') ||
            id.includes('/react-hook-form/') ||
            id.includes('/@hookform/')
          ) {
            return 'vendor-ui';
          }
        },
      },
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
