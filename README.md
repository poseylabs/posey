# Posey Monorepo

This repository contains the source code for Posey – a lifelong personalized AI agent companion system.

-----

## Posey Status

#### Infrastructure
[![Posey Deploy Manager](https://github.com/poseylabs/posey/actions/workflows/deploy.yml/badge.svg)](https://github.com/poseylabs/posey/actions/workflows/deploy.yml)

#### Data Services
[![Postgres](https://github.com/poseylabs/posey/actions/workflows/data-postgres.yml/badge.svg)](https://github.com/poseylabs/posey/actions/workflows/data-postgres.yml)
[![Couchbase](https://github.com/poseylabs/posey/actions/workflows/data-couchbase.yml/badge.svg)](https://github.com/poseylabs/posey/actions/workflows/data-couchbase.yml)
[![Qdrant](https://github.com/poseylabs/posey/actions/workflows/data-vector-db.yml/badge.svg)](https://github.com/poseylabs/posey/actions/workflows/data-vector-db.yml)

#### Core Services
[![Agents API](https://github.com/poseylabs/posey/actions/workflows/service-agents.yml/badge.svg)](https://github.com/poseylabs/posey/actions/workflows/service-agents.yml)
[![Authentication Service](https://github.com/poseylabs/posey/actions/workflows/service-auth.yml/badge.svg)](https://github.com/poseylabs/posey/actions/workflows/service-auth.yml)
[![Cron Server](https://github.com/poseylabs/posey/actions/workflows/service-cron.yml/badge.svg)](https://github.com/poseylabs/posey/actions/workflows/service-cron.yml)
[![MCP Server](https://github.com/poseylabs/posey/actions/workflows/service-mcp.yml/badge.svg)](https://github.com/poseylabs/posey/actions/workflows/service-mcp.yml)
[![Posey Voyager](https://github.com/poseylabs/posey/actions/workflows/service-voyager.yml/badge.svg)](https://github.com/poseylabs/posey/actions/workflows/service-voyager.yml)

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
