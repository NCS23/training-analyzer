/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@nordlig/components/dist/**/*.{js,mjs}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        workout: {
          quality: '#8b5cf6',
          recovery: '#10b981',
          longrun: '#3b82f6',
          strength: '#f97316',
        },
        hr: {
          zone1: '#10b981',
          zone2: '#f59e0b',
          zone3: '#ef4444',
        },
      },
      keyframes: {
        'caret-blink': {
          '0%, 70%, 100%': { opacity: '1' },
          '20%, 50%': { opacity: '0' },
        },
      },
      animation: {
        'caret-blink': 'caret-blink 1.2s ease-out infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
