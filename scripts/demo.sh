#!/usr/bin/env bash
set -euo pipefail

run_cli() {
  PYTHONPATH=src python3 -m oci_secure.cli "$@"
}

run_cli pipeline

docker buildx build examples/hello-api \
  --file examples/hello-api/Dockerfile.baseline \
  --tag oci-secure-demo:baseline \
  --platform linux/amd64 \
  --load

run_cli benchmark oci-secure-demo:baseline oci-secure-demo:local

container_id="$(docker run --detach --publish 8080:8080 oci-secure-demo:local)"
cleanup() { docker rm --force "$container_id" >/dev/null 2>&1 || true; }
trap cleanup EXIT

for _ in {1..15}; do
  if curl --fail --silent http://127.0.0.1:8080/health; then
    printf '\nDemo passed: image is healthy and running without root.\n'
    exit 0
  fi
  sleep 1
done

printf 'Container did not become healthy.\n' >&2
exit 1
