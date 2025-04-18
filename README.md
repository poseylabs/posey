[![CircleCI](https://dl.circleci.com/status-badge/img/circleci/9RCMZs5ANpSsRLtbL9Nfkd/7dtVXKL2S6onY3KxYQ7NjX/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/circleci/9RCMZs5ANpSsRLtbL9Nfkd/7dtVXKL2S6onY3KxYQ7NjX/tree/main)
# Posey Monorepo

This repository contains the source code for Posey – a lifelong personalized AI agent companion system.

-----

## Project Structure

- **apps/**  
  - **web/**: Next.js application for web clients  
  - **mobile/**: React Native application for mobile platforms  
  - **desktop/**: Electron application for desktop clients

- **packages/**  
  - **core/**: Shared React components, state management, and utilities  
  - **eslint-config/**: Shared ESLint configurations  
  - **plugins/**: Shared plugin system for agent extensions  
  - **ui/**: Reusable UI components (daisyUI / Tailwind CSS)  
  - **ts-config/**: Shared TypeScript configuration  
  - **utils/**: Common utility functions  

- **services/**  
  - **cron/**: Node.js-based cron job service  
  - **data/**: Data services  
  - **agents/**: Python-based API server powering our agentic system

## Getting Started

1. Install dependencies:

   ```bash
   npm install
   ```

2. Use NX generators to build out your applications and packages. For example, to generate a Next.js app in the `apps/web` directory:

   ```bash
   npx nx g @nrwl/next:app web
   ```

3. Refer to the [Nx Documentation](https://nx.dev) for more details on building, testing, and generating code.

Happy coding! 
