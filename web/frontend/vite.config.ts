import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `npm run dev` (cổng 5173) chuyển tiếp /ws và /api sang backend ở cổng 8000.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      "/ws": { target: "ws://localhost:8000", ws: true },
      "/api": "http://localhost:8000",
    },
  },
});
