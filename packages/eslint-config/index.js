const baseConfig = require('./eslint.base');
const desktopConfig = require('./eslint.desktop');
const serverConfig = require('./eslint.server');
const webConfig = require('./eslint.web');
const nextConfig = require('./eslint.next');

module.exports = {
  base: baseConfig,
  desktop: desktopConfig,
  server: serverConfig,
  web: webConfig,
  next: nextConfig,
  default: webConfig,
};
