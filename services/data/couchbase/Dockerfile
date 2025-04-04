# Pin to a specific version, e.g., community-7.2.4 or enterprise-7.2.4
FROM couchbase:community-7.2.4

# Set labels
LABEL maintainer="Posey.ai <support@posey.ai>"
LABEL description="Couchbase database for Posey.ai"
LABEL version="1.0"

# Expose Couchbase ports
EXPOSE 8091-8094 11210

# Add healthcheck
# Consider a more robust check if available/needed
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8091/pools || exit 1 