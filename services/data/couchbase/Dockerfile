FROM couchbase:community-7.2.4

LABEL maintainer="Posey.ai <support@posey.ai>"
LABEL description="Couchbase database for Posey.ai"
LABEL version="1.0"

EXPOSE 8091-8094 11210

COPY couchbase-init.sh /couchbase-init.sh
RUN chmod +x /couchbase-init.sh

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8091/pools || exit 1

ENTRYPOINT ["/couchbase-init.sh"]
