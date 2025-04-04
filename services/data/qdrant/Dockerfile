# Pin to a specific version for stability, e.g., v1.9.0
FROM qdrant/qdrant:v1.9.0

WORKDIR /qdrant

# Configuration is now handled via Helm/env vars, no need to copy local config.yaml
# COPY config.yaml config/production.yaml
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

# EXPOSE is informational. Ports exposed via Service: 6333 (gRPC), 1111 (HTTP) by default.
EXPOSE 6333 1111
ENTRYPOINT ["/docker-entrypoint.sh"]