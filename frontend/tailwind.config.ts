import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0E1117",
        surface: "#1A1E24",
        "surface-border": "#28303C",
        accent: "#00D2FF",
        "accent-hover": "#33DCFF",
        route: "#00FFCC",
        iceberg: "#FFB300",
        hazard: "#FF3B30",
        muted: "#8E9AA8",
      },
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Oxygen",
          "Ubuntu",
          "Cantarell",
          "sans-serif",
        ],
      },
      boxShadow: {
        tactical: "0 0 15px rgba(0, 210, 255, 0.12)",
        glow: "0 0 20px rgba(0, 210, 255, 0.25)",
        hazard: "0 0 15px rgba(255, 59, 48, 0.25)",
      },
    },
  },
  plugins: [],
};
export default config;
