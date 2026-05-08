import type { Config } from "tailwindcss";
import stratpoolPreset from "@thomasbrunner-spec/design-system/tailwind";

export default {
  presets: [stratpoolPreset],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./node_modules/@thomasbrunner-spec/design-system/dist/**/*.js",
  ],
  darkMode: "class",
} satisfies Config;
