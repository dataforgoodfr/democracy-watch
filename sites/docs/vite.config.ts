import { defineConfig } from "vite";

export default defineConfig({
  ssr: { noExternal: ["mermaid"] },
  optimizeDeps: { include: ["mermaid"] },
});
