# Build stage
FROM node:20-slim AS builder

# Install postgres client and other tools
RUN apt-get update \
  && apt-get install -y postgresql-client curl \
  && rm -rf /var/lib/apt/lists/*

# Set base working directory
WORKDIR /app

# Copy only the necessary files for the auth service
COPY services/auth/package*.json ./services/auth/
COPY services/auth/tsconfig.json ./services/auth/
COPY services/auth/src ./services/auth/src

# Move to the auth service directory
WORKDIR /app/services/auth

# Install dependencies with npm
RUN npm install

# Build the service
RUN npm run build

# Production image
FROM node:20-slim

# Install postgres client
RUN apt-get update \
  && apt-get install -y postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# Copy built app from builder (correct paths for monorepo structure)
WORKDIR /app
COPY --from=builder /app/services/auth/dist ./dist
COPY --from=builder /app/services/auth/node_modules ./node_modules
COPY --from=builder /app/services/auth/package.json ./

# Environment variables
ENV NODE_ENV=production

EXPOSE 9999
CMD ["node", "dist/main.js"]
