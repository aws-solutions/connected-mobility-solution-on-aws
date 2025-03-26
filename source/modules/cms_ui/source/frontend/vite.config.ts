// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/// <reference types="vitest" />

import react from "@vitejs/plugin-react";

import * as path from "path";

import { defineConfig } from "vite";
import viteTsconfigPaths from "vite-tsconfig-paths";
import polyfillNode from "rollup-plugin-polyfill-node";

export default defineConfig({
  plugins: [react(), viteTsconfigPaths()],
  build: {
    outDir: "build",
    chunkSizeWarningLimit: 4000,
    rollupOptions: {
      plugins: [polyfillNode()],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      os: "os-browserify/browser",
      process: "process/browser",
      stream: "stream-browserify",
      util: "util/",
      path: "path-browserify",
      buffer: "buffer/",
      crypto: "crypto-browserify",
    },
  },
  define: {
    global: "window",
    "process.env": {},
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./setupTests.ts",
    coverage: {
      provider: "v8",
      reporter: ["lcov", "text"],
      exclude: [
        "**/node_modules/**",
        "**/build/**",
        "**/.{git,tmp}/**",
        "**/interfaces/**",
        "src/__test__/**",
        "coverage/**",
        "test/*.js",
        "src/App.tsx",
        "src/index.tsx",
      ],
    },
    exclude: ["**/node_modules/**", "**/build/**", "**/.{git,tmp}/**"],
  },
  server: {
    port: 5177,
  },
});
