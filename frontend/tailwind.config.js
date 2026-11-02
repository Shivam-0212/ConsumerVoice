/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f5ff',
          100: '#e0ecff',
          200: '#c7dcff',
          300: '#9ec4ff',
          400: '#6ea3ff',
          500: '#3d7cff',
          600: '#1b56f5',
          700: '#123ed8',
          800: '#1335af',
          900: '#15318a',
          950: '#0c1b52',
        },
        slate: {
          850: '#151e2e',
          950: '#080d1a',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      }
    },
  },
  plugins: [],
}

