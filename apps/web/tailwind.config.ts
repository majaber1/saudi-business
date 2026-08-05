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
          500: "#0f8a4d",
          600: "#0b6f3e",
          700: "#0a5c34",
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
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
