FROM qdrant/qdrant:v1.9.0

USER root
RUN apt-get update && apt-get install -y curl --no-install-recommends && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /qdrant

COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

EXPOSE 6333 1111
ENTRYPOINT ["/docker-entrypoint.sh"]