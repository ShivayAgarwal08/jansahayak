/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: {
          50: '#FAF8F2',
          100: '#F4EFE2',
          200: '#E9E1CE',
          300: '#DDD3BA',
        },
        navy: {
          700: '#2A446F',
          800: '#1F3456',
          900: '#192A46',
          950: '#0F1A2D',
        },
        leaf: {
          50: '#EBF7F0',
          100: '#D6EFE1',
          500: '#249C67',
          600: '#1C8657',
          700: '#18794E',
          800: '#125C3C',
        },
        saffron: {
          50: '#FEF8EE',
          100: '#FDF1DC',
          500: '#E9A23B',
          600: '#D58C23',
          700: '#B06F14',
        },
        softsky: '#DCECF7',
        softmint: '#E1F2E8',
      },
      fontFamily: {
        sans: ['Manrope', 'Noto Sans Devanagari', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'civic': '16px',
        'civic-lg': '20px',
      },
      boxShadow: {
        'civic': '0 4px 20px -2px rgba(25, 42, 70, 0.06), 0 2px 6px -1px rgba(25, 42, 70, 0.04)',
        'civic-hover': '0 10px 25px -3px rgba(25, 42, 70, 0.1), 0 4px 10px -2px rgba(25, 42, 70, 0.05)',
      }
    },
  },
  plugins: [],
}
