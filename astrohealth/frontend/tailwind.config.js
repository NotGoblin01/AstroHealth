/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        space: {
          950: '#050811',
          900: '#080d1a',
          850: '#0c1427',
          800: '#111d38',
          700: '#1a2c54',
          600: '#27427d',
        },
        cyan: {
          glow: '#00f2fe',
          accent: '#06b6d4',
        },
        violet: {
          subtle: '#7c3aed',
          glow: '#a855f7',
        },
        status: {
          nominal: '#10b981',
          attention: '#38bdf8',
          urgent: '#f59e0b',
          emergency: '#ef4444',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'panel': '0 4px 20px -2px rgba(0, 0, 0, 0.5), 0 0 1px 1px rgba(255, 255, 255, 0.05)',
        'cyan-glow': '0 0 15px -3px rgba(6, 182, 212, 0.3)',
        'alert-glow': '0 0 20px -2px rgba(239, 68, 68, 0.4)',
      }
    },
  },
  plugins: [],
}

