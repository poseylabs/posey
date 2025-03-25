FROM registry.supertokens.io/supertokens/supertokens-postgresql:latest

# Add environment variables - will be provided by Kubernetes secrets
ENV POSTGRESQL_USER=${POSTGRES_USER:-postgres}
ENV POSTGRESQL_PASSWORD=${POSTGRES_PASSWORD}
ENV POSTGRESQL_DB=${POSTGRES_DB_SUPERTOKENS:-supertokens}
ENV POSTGRESQL_HOST=${POSTGRES_HOST:-posey-postgres}
ENV POSTGRESQL_PORT=${POSTGRES_PORT:-3333}
ENV API_KEYS=${SUPERTOKENS_API_KEY}

# Configure SuperTokens for production
ENV DISABLE_TELEMETRY=true

# Volume for persistent data
VOLUME /app/data

# Expose SuperTokens port
EXPOSE 3567

# Set healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD [ "wget", "-q", "http://localhost:3567/hello", "-O", "/dev/null", "||", "exit", "1" ]

# SuperTokens runs with the default command from the base image 