/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Scan only the source files within this UI package
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  // We will configure DaisyUI via the @plugin directive in CSS
  theme: {
    extend: {},
  },
  plugins: [],
};
