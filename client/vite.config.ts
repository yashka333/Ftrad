import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8787' },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'build',
    // keep pixel sprites as files so they can be swapped and cached
    assetsInlineLimit: 0,
  },
});
