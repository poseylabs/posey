FROM qdrant/qdrant:latest

WORKDIR /qdrant

COPY config.yaml config/production.yaml
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

EXPOSE 6333 6334 1111
ENTRYPOINT ["/docker-entrypoint.sh"]