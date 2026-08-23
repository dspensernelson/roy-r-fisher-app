import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
  // The screens are React, so proving they behave means rendering them. The
  // Python suite can read this source and check that a string is present; it
  // cannot press a button and see what happens, and several of the behaviours
  // Spenser approved are exactly that: a control that is off until a count is
  // right, a second button that appears only in one state, a run that redraws
  // as it goes. Those are tested here, against real DOM.
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.js"],
    include: ["src/**/*.test.jsx"],
    restoreMocks: true,
  },
});
