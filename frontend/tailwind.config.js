/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@nordlig/components/dist/**/*.{js,mjs}",
    // pnpm stores packages in .pnpm — include real path for reliable class detection
    "./node_modules/.pnpm/**/node_modules/@nordlig/components/dist/**/*.{js,mjs}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: "var(--font-family-sans)",
        mono: "var(--font-base-family-mono)",
      },
      colors: {},
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
