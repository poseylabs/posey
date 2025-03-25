## Overview

Posey is envisioned as a lifelong personalized AI companion capable of managing diverse aspects such as scheduling, financial planning, document analysis, smart home control, and more. The new system will be built as a monorepo that leverages NX for efficient configuration sharing and dependency management. Our agentic system (powered by pydantic.ai) will serve as the core engine behind a Python-based API server that exposes our agents' functionality to front-end applications. 

## High-Level Requirements

- **Modular Design:** Separation of concerns across front-end applications, shared packages, and backend services.
- **Scalability:** Ability to evolve and integrate new capabilities; incorporate a robust memory system and multi-agent orchestration as needed.
- **Containerization:** Use Docker (and docker-compose) to containerize all services, ensuring consistency across development and production environments.
- **Code-First Approach:** Maintain a lean, flexible architecture allowing customization of agent behavior without being locked into heavyweight frameworks.
- **Future-Proofing:** Minimize ecosystem lock-in, enabling future migration or expansion, while supporting integration with vector databases (e.g., Qdrant) and relational databases (PostgreSQL).

## Proposed Monorepo Structure

The monorepo will be organized as follows:

```
├── apps
│   ├── web         # Next.js application for web clients
│   ├── mobile      # React Native app for mobile platforms
│   └── desktop     # Electron app for desktop clients
│
├── packages
│   ├── core        # Shared React components, state management, and common utilities
│   ├── eslint-config  # Shared ESLint configurations
│   ├── plugins     # Shared plugin system for extending agent capabilities
│   ├── ui          # Shared UI components (using daisyUI and Tailwind CSS)
│   ├── ts-config   # Shared TypeScript configuration
│   └── utils       # Shared utility functions
│
├── services
│   ├── agents      # Python-based API server powered by pydantic.ai to handle agentic workflows
│   ├── cron        # Node.js-based cron job service for scheduled tasks
│   └── data        # Data services including PostgreSQL, GraphQL engine, and Qdrant (vector DB)
│       ├── postgres
│       └── vector-db
│
├── package.json    # Root package file managing workspaces and dependencies
├── README.md       # Project overview and documentation
├── nx.json         # NX configuration file
└── tsconfig.json   # Root TypeScript configuration
```

## Architectural Recommendations

1. **NX Monorepo:**
   - Use NX to manage the different applications and shared packages, ensuring consistency in configuration and enabling efficient builds across packages.
   - Encourage code reuse by placing common logic and UI components into the shared packages.

2. **Containerization with Docker Compose:**
   - Maintain docker-compose configurations for all services. Separate docker-compose files can be used for different environments (development, staging, production).
   - Recommended to define healthchecks, environment variables, and resource limits as per the complexity of each service.
   - Integrate our agents service (Python/pydantic.ai), cron jobs, and data services (Postgres, GraphQL, Qdrant) into a unified docker-compose deployment.

3. **Service Isolation and Communication:**
   - Each service (agents, cron, data) should run in its own container. This promotes scalability and fault isolation.
   - Use an internal Docker network ('posey.network') for inter-service communication.

4. **Agents Service (pydantic.ai):**
   - The agents service will be built in Python and leverage pydantic.ai as the core agent building block.
   - Customize agent behavior via a modular architecture, using your own plugins and memory systems based on your evolving requirements.

5. **Data Services:**
   - Integration of a relational database (PostgreSQL) and a vector search engine (Qdrant) for persistent memory and rapid retrieval.
   - Use Hasura or a similar GraphQL engine to provide a convenient API layer over Postgres.

6. **Continuous Integration/Deployment:**
   - Use GitHub Actions (or similar CI/CD pipelines) to build, test, and deploy your containers.
   - Reproducible builds and ease of deployment can be achieved by using Dockerfiles for each service.

## Authentication Service

The authentication service will be implemented as a standalone service in our monorepo:

```
services/
└── auth/                 # Authentication service
    ├── Dockerfile
    ├── src/
    │   ├── controllers/  # Auth logic controllers
    │   ├── models/       # User and session models
    │   ├── routes/       # API routes
    │   └── config/       # Auth configuration
    └── docker-compose.yml
```

### Authentication Strategy

1. **Core Technology Stack:**
   - Supabase Auth (open-source) or Keycloak for the authentication server
   - JWT for token-based authentication
   - PostgreSQL for user data storage
   - Redis for session management (optional)

2. **Key Features:**
   - OAuth 2.0 and OpenID Connect support
   - Social authentication providers
   - Email/password authentication
   - Magic link authentication
   - JWT token management with refresh tokens
   - Role-based access control (RBAC)
   - Session management
   - Password reset flows
   - Email verification
   - 2FA support

3. **Client Integration:**
   - Shared authentication SDK in packages/auth-sdk
   - Common auth hooks and components in packages/core
   - Platform-specific auth adapters for each client:
     - Next.js: API routes + middleware
     - React Native: Secure storage + auth flow
     - Electron: Secure storage + IPC bridge

4. **Security Considerations:**
   - CSRF protection
   - Rate limiting
   - JWT encryption
   - Secure cookie handling
   - XSS protection
   - Audit logging

### Docker Configuration

Add to docker-compose.yml:
```yaml
services:
  auth:
    build:
      context: ./services/auth
      dockerfile: Dockerfile
    container_name: auth
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://auth_user:${AUTH_DB_PASSWORD}@postgres:3333/auth_db
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    ports:
      - "9000:9000"
    networks:
      - posey.network

  redis:
    image: redis:alpine
    container_name: redis
    ports:
      - "6379:6379"
    networks:
      - posey.network
```

### Client SDK Usage Example

```typescript
// packages/auth-sdk/src/index.ts
export class AuthClient {
  constructor(config: AuthConfig) {
    this.baseUrl = config.authServiceUrl;
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Implementation
  }

  async logout(): Promise<void> {
    // Implementation
  }

  async refreshToken(): Promise<string> {
    // Implementation
  }
}

// Usage in Next.js
import { AuthClient } from '@your-org/auth-sdk';

const authClient = new AuthClient({
  authServiceUrl: process.env.NEXT_PUBLIC_AUTH_SERVICE_URL
});

// Usage in React Native
import { AuthClient } from '@your-org/auth-sdk';
import { SecureStore } from 'expo-secure-store';

const authClient = new AuthClient({
  authServiceUrl: Config.AUTH_SERVICE_URL,
  storage: SecureStore
});

// Usage in Electron
import { AuthClient } from '@your-org/auth-sdk';
import { ipcRenderer } from 'electron';

const authClient = new AuthClient({
  authServiceUrl: process.env.AUTH_SERVICE_URL,
  storage: {
    // Implement secure storage using electron's safeStorage
  }
});
```

## Software and Tooling Recommendations

- **NX:** For monorepo management and build optimization.
- **Docker & Docker Compose:** For consistent containerized environments.
- **pydantic.ai:** As your core agent framework for a code-first, lightweight, and modular agentic system.
- **Next.js, React Native, Electron:** For cross-platform front-end applications.
- **PostgreSQL, Hasura (GraphQL), Qdrant:** For robust data persistence, API layer, and vector-based memory retrieval.
- **GitHub Actions:** For CI/CD integration.
- **TypeScript & ESLint:** For type safety and code quality across the monorepo.
- **DaisyUI/TailwindCSS:** For consistently styled UI components.

## Resources and Documentation

### Core Technologies
- NX Documentation: https://nx.dev/getting-started/intro
- Smolagents Guide: https://huggingface.co/docs/pydantic.ai/en/guided_tour
- Docker Compose Guide: https://docs.docker.com/compose/gettingstarted/

### Frontend Technologies
- Next.js Documentation: https://nextjs.org/docs
- React Native Setup Guide: https://reactnative.dev/docs/environment-setup
- Electron Quick Start: https://www.electronjs.org/docs/latest/tutorial/quick-start
- DaisyUI Components: https://daisyui.com/components/
- TailwindCSS Documentation: https://tailwindcss.com/docs

### Backend and Data Storage
- FastAPI (for Python API): https://fastapi.tiangolo.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Qdrant Vector Database: https://qdrant.tech/documentation/

### Authentication Resources
- Supabase Auth Documentation: https://supabase.com/docs/guides/auth
- Keycloak Documentation: https://www.keycloak.org/documentation
- JWT Implementation Guide: https://jwt.io/introduction
- OAuth 2.0 Specifications: https://oauth.net/2/
- OpenID Connect Guide: https://openid.net/developers/how-connect-works/
- Redis Security Guide: https://redis.io/topics/security

### Development Tools
- TypeScript Handbook: https://www.typescriptlang.org/docs/
- ESLint Configuration: https://eslint.org/docs/latest/use/configure/
- GitHub Actions: https://docs.github.com/en/actions


### AI & Agentic Tools & Resources
- Smolagents: https://huggingface.co/docs/pydantic.ai/en/guided_tour
  - https://huggingface.co/docs/pydantic.ai/en/tutorials/building_good_agents
- Open Deep Research: https://huggingface.co/blog/open-deep-research
- Deep Research: https://github.com/dzhng/deep-research


### Recommended VS Code Extensions
- NX Console: https://marketplace.visualstudio.com/items?itemName=nrwl.angular-console
- Docker: https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker
- ESLint: https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint
- Tailwind CSS IntelliSense: https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss
- Python: https://marketplace.visualstudio.com/items?itemName=ms-python.python
