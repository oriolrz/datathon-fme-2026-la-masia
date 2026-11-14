import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base relativa: el build (dist/) es pot obrir des de qualsevol carpeta o servidor estàtic
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { chunkSizeWarningLimit: 2000 },
});
