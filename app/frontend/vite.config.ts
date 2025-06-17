// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),          // ← First-party Tailwind Vite plugin :contentReference[oaicite:0]{index=0}
  ],
});
