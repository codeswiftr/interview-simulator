import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  use: {
    baseURL: "http://127.0.0.1:5173",
  },
  projects: [
    {
      name: "Mobile Safari",
      use: devices["iPhone SE"],
    },
    {
      name: "Mobile Chrome",
      use: devices["Pixel 5"],
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: !process.env.CI,
  },
});
