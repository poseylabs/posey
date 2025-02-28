const baseConfig = require('./tsconfig.base');
const desktopConfig = require('./tsconfig.desktop');
const serverConfig = require('./tsconfig.server');
const reactConfig = require('./tsconfig.react');
const nextConfig = require('./tsconfig.next');

module.exports = {
  base: baseConfig,
  desktop: desktopConfig,
  server: serverConfig,
  react: reactConfig,
  next: nextConfig,
  default: reactConfig,
};
