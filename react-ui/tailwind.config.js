/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#0B0E14",
        darkCard: "#151923",
        neonGreen: "#00fca8",
        neonYellow: "#fbbf24",
        neonRed: "#ff3366",
        neonCyan: "#00e5ff"
      },
      boxShadow: {
        'neon-green': '0 0 10px #00fca8, 0 0 20px rgba(0,252,168,0.2)',
        'neon-yellow': '0 0 10px #fbbf24, 0 0 20px rgba(251,191,36,0.2)',
        'neon-red': '0 0 10px #ff3366, 0 0 20px rgba(255,51,102,0.2)',
        'neon-cyan': '0 0 10px #00e5ff, 0 0 20px rgba(0,229,255,0.2)',
      }
    },
  },
  plugins: [],
}
