#!/usr/bin/env bash
set -euo pipefail

image="${1:-oci-secure-demo:local}"
cluster="${2:-oci-secure}"

kind load docker-image "$image" --name "$cluster"
kubectl apply -f deploy/kubernetes.yaml
kubectl set image deployment/hello-api hello-api="$image"
kubectl rollout status deployment/hello-api --timeout=120s

runtime_uid="$(kubectl exec deployment/hello-api -- python3 -c 'import os; print(os.getuid())')"
if [[ "$runtime_uid" == "0" ]]; then
  printf 'Kubernetes workload unexpectedly runs as root.\n' >&2
  exit 1
fi

kubectl exec deployment/hello-api -- python3 -c '
import time
import urllib.error
import urllib.request

for attempt in range(30):
    try:
        urllib.request.urlopen("http://hello-api/health", timeout=2).read()
        break
    except urllib.error.URLError:
        if attempt == 29:
            raise
        time.sleep(1)
'

kubectl exec deployment/hello-api -- python3 -c '
from pathlib import Path

status = Path("/proc/self/status").read_text().splitlines()
fields = dict(line.split(":", 1) for line in status if ":" in line)
assert int(fields["CapEff"].strip(), 16) == 0, fields["CapEff"]
assert fields["NoNewPrivs"].strip() == "1", fields["NoNewPrivs"]

root = next(line for line in Path("/proc/mounts").read_text().splitlines()
            if line.split()[1] == "/")
assert "ro" in root.split()[3].split(","), root
'

kubectl get deployment,service,pod -l app.kubernetes.io/name=hello-api
printf 'Kubernetes verification passed: UID=%s, probes ready, service reachable, rootfs read-only, privileges restricted.\n' "$runtime_uid"
