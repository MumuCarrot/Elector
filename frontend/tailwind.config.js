/**
 * Tailwind CSS configuration: scans `src` for class names; default theme with empty extend.
 *
 * @type {import('tailwindcss').Config}
 */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

