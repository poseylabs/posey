FROM qdrant/qdrant:v1.13.3

USER root
RUN apt-get update && apt-get install -y curl netcat-openbsd iputils-ping --no-install-recommends && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /qdrant

COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

EXPOSE 6333 1111
ENTRYPOINT ["/docker-entrypoint.sh"]