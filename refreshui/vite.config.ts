import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Vendor chunks
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {
              return 'react-vendor';
            }
            if (id.includes('framer-motion')) {
              return 'framer-motion';
            }
            if (id.includes('zustand')) {
              return 'state-management';
            }
            if (id.includes('lucide-react')) {
              return 'icons';
            }
            if (id.includes('@tanstack/react-virtual')) {
              return 'virtualization';
            }
            // Other node_modules go into vendor chunk
            return 'vendor';
          }
          
          // App chunks by feature
          if (id.includes('/components/atoms/')) {
            return 'components-atoms';
          }
          if (id.includes('/components/molecules/')) {
            return 'components-molecules';
          }
          if (id.includes('/components/organisms/')) {
            return 'components-organisms';
          }
          if (id.includes('/views/')) {
            return 'views';
          }
          if (id.includes('/layouts/')) {
            return 'layouts';
          }
        },
      },
    },
    // Set chunk size warning limit to 850kb to accommodate React 19 vendor bundle
    // React 19 + React DOM + React Router = ~804KB minified, 226KB gzipped
    // The gzipped size is what actually matters for network transfer
    // This is cached by the browser and only downloaded once
    chunkSizeWarningLimit: 850,
  },
})
