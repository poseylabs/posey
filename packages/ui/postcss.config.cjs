/** @type {import('postcss-load-config').Config} */
module.exports = {
  plugins: {
    'postcss-nested': {},
    '@tailwindcss/postcss': {}, // Restoring plugin to test interaction
    autoprefixer: {},
  },
};
