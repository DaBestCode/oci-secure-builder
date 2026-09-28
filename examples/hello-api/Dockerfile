# syntax=docker/dockerfile:1.7
FROM ubuntu:24.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends python3
WORKDIR /opt/app
COPY app.py .
RUN python3 -m zipapp . --main app:main --output hello-api.pyz

FROM ubuntu:24.04 AS runtime
ARG SOURCE_URL="https://github.com/OWNER/oci-secure-builder"
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
WORKDIR /opt/app
COPY --from=builder --chown=app:app /opt/app/hello-api.pyz ./
LABEL org.opencontainers.image.title="OCI Secure Hello API" \
      org.opencontainers.image.description="Hardened demonstration image" \
      org.opencontainers.image.source=$SOURCE_URL \
      org.opencontainers.image.licenses="MIT"
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=3s --retries=3 \
  CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"]
CMD ["python3", "hello-api.pyz"]
