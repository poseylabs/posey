const path = require('path');

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // App directory paths ONLY - UI package handles its own styles
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  // No theme or plugins needed here for v4 if using @plugin in CSS
}; 