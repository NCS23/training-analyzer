import { defineConfig } from 'vite';
import type { Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

/**
 * Converts render-blocking CSS <link> tags to non-blocking preload/onload
 * pattern. The browser can paint the inline critical CSS (in index.html)
 * immediately for a fast FCP, while the full stylesheet loads in parallel.
 */
function asyncCssPlugin(): Plugin {
  return {
    name: 'async-css',
    enforce: 'post',
    transformIndexHtml(html) {
      return html.replace(
        /<link rel="stylesheet" crossorigin href="(\/assets\/[^"]+\.css)">/g,
        (_match, href: string) =>
          `<link rel="preload" as="style" href="${href}" onload="this.onload=null;this.rel='stylesheet'" />\n    <noscript><link rel="stylesheet" href="${href}" /></noscript>`,
      );
    },
  };
}

export default defineConfig({
  plugins: [react(), asyncCssPlugin()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Vendor: React ecosystem (cached long-term)
          if (
            id.includes('node_modules/react') ||
            id.includes('node_modules/react-dom') ||
            id.includes('node_modules/react-router') ||
            id.includes('node_modules/scheduler')
          ) {
            return 'vendor-react';
          }
          // Vendor: Recharts + d3 (only loaded on chart pages)
          if (
            id.includes('node_modules/recharts') ||
            id.includes('node_modules/d3-') ||
            id.includes('node_modules/victory-vendor')
          ) {
            return 'vendor-recharts';
          }
          // Vendor: Radix UI primitives (used by Nordlig DS)
          if (id.includes('node_modules/@radix-ui')) {
            return 'vendor-radix';
          }
          // Vendor: Leaflet (only loaded on map pages)
          if (id.includes('node_modules/leaflet')) {
            return 'vendor-leaflet';
          }
          // Vendor: TanStack (React Query + Table)
          if (id.includes('node_modules/@tanstack')) {
            return 'vendor-tanstack';
          }
          // Vendor: DnD Kit (only used in plan/template editors)
          if (id.includes('node_modules/@dnd-kit')) {
            return 'vendor-dndkit';
          }
          // Vendor: Nordlig Design System
          if (id.includes('@nordlig/')) {
            return 'vendor-nordlig';
          }
          // Vendor: lucide-react icons
          if (id.includes('node_modules/lucide-react')) {
            return 'vendor-icons';
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
});
