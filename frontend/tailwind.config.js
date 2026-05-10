/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: '#0f172a',
          surface: '#111827',
          card: '#1f2937',
          line: '#334155',
          neonBlue: '#38bdf8',
          neonGreen: '#22c55e',
          text: '#e2e8f0',
          muted: '#94a3b8',
        },
      },
      boxShadow: {
        neon: '0 0 25px rgba(56, 189, 248, 0.25)',
      },
      backgroundImage: {
        heroGlow:
          'radial-gradient(circle at 20% 20%, rgba(56,189,248,0.15), transparent 45%), radial-gradient(circle at 80% 0%, rgba(34,197,94,0.12), transparent 35%)',
      },
    },
  },
  plugins: [],
}

