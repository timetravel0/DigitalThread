import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b1020",
        panel: "#11182d",
        panel2: "#18213a",
        line: "#223053",
        accent: "#7cdbff",
        accent2: "#a78bfa",
        text: "#e6edf7",
        muted: "#95a4bf",
        danger: "#ff6b8b",
        success: "#5ee7a5",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(124,219,255,0.15), 0 12px 40px rgba(0,0,0,0.35)",
      },
    },
  },
  plugins: [],
};

export default config;
