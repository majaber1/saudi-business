import type { Config } from "tailwindcss";

// Saudi Business design tokens: refined green (Saudi-inspired) + premium gold accent + slate neutrals.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eefaf3",
          100: "#d6f2e1",
          200: "#aee3c3",
          400: "#1a9d5c",
          500: "#0f8a4d",
          600: "#0b6f3e",
          700: "#0a5c34",
          800: "#084a2a",
          900: "#083f24",
        },
        gold: {
          50: "#fdf9ec",
          100: "#faf0cf",
          200: "#f3e0a1",
          300: "#e9cb6b",
          400: "#dcb443",
          500: "#c9a227",
          600: "#a9851d",
          700: "#86691b",
          800: "#6d551d",
        },
        ink: {
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
      },
      fontFamily: {
        // The active locale's <html lang> drives which stack wins -- see
        // the :lang(ar) rule in globals.css. Both are exposed as `font-sans`
        // so existing utility classes need no per-page changes.
        sans: ["var(--font-latin)", "var(--font-arabic)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.04), 0 1px 3px 0 rgb(15 23 42 / 0.06)",
        "card-hover": "0 4px 12px -2px rgb(15 23 42 / 0.08), 0 2px 6px -2px rgb(15 23 42 / 0.05)",
      },
    },
  },
  plugins: [],
};

export default config;
