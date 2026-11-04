FROM cgr.dev/chainguard/minio-client:latest AS mc-bin

FROM alpine:3.20
RUN apk add --no-cache curl bash
COPY --from=mc-bin /usr/bin/mc /usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

COPY init_buckets.sh /usr/local/bin/init_buckets.sh
RUN chmod +x /usr/local/bin/init_buckets.sh

ENTRYPOINT ["/usr/local/bin/init_buckets.sh"]
