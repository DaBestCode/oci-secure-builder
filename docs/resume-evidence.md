# Résumé claim evidence

This matrix keeps the project description defensible. Each phrase maps to an
implementation, an automated check, and—where appropriate—a measured result.

| Résumé phrase | Implementation | Automated evidence |
|---|---|---|
| Python-based container image builder | `ImageBuilder` assembles argument-safe `docker buildx build` commands from `oci-secure.toml`, injects OCI labels, and returns BuildKit metadata | `tests/test_builder.py` checks cache import/export, metadata, labels, build arguments, and safe cache rotation |
| Vulnerability scanner for Ubuntu OCI images | `VulnerabilityScanner` invokes Trivy, parses JSON, counts severities, and raises a non-zero policy violation when configured budgets are exceeded | Scanner unit tests plus the `container-policy`, Rockcraft, and release-candidate jobs |
| Automated multi-stage builds | The example Dockerfile creates a Python zipapp in a builder stage and copies only that artifact into the Ubuntu runtime stage | Every container-policy run builds the Dockerfile through the Python `pipeline` command |
| Layer caching | BuildKit exports a `mode=max` local cache, imports it on the next build, and rotates it only after success | Builder unit test plus `actions/cache` persistence between GitHub-hosted CI runs |
| Dependency minimization | Runtime uses `--no-install-recommends`; compiler and build dependencies never enter the final stage. The Rock counterpart selects only import-driven Chisel slices | Baseline benchmark, Docker/Rock profile, and live health checks catch missing runtime dependencies |
| Cut image size by at least 65% | Controlled baseline retains compilers, headers, Git, curl, and APT metadata; optimized runtime omits them | Recorded result: 216.8 MiB to 41.6 MiB, an 80.8% reduction, leaving margin above the conservative 65% résumé claim |
| Automated CI/CD security compliance | Severity budgets, required OCI labels, Linux OS, health metadata, configured user, and actual runtime UID are policy gates | Unit tests, Trivy JSON/SARIF artifacts, and failing exit codes block the workflow |
| Non-root execution | Docker metadata is inspected and `id -u` is executed in a fresh container; Kubernetes also enforces `runAsNonRoot` | Docker verifier and restricted Kubernetes integration test both reject UID 0 |
| Cloud-native runtime compatibility | The exact scanned image is loaded into kind and run through Kubernetes/containerd with probes, resources, Service discovery, read-only rootfs, seccomp, dropped capabilities, and disabled privilege escalation | CI waits for rollout, calls the Service from the pod, and reads `/proc` to verify `CapEff=0`, `NoNewPrivs=1`, and a read-only root mount |
| Gates before registry publishing | The tag workflow builds one local image, runs the scan and both runtime gates, then tags and pushes that same image object | Login and `docker push` occur only after all prior steps return successfully |

## Precise terminology

Use **non-root container execution** in interviews and on the résumé. The
project proves that the workload process is not UID 0 under both Docker and
Kubernetes. “Rootless Docker” has a narrower meaning—the Docker daemon itself
runs without root—and this repository does not claim to configure that daemon.

## Measurements and scope

The 80.8% measurement compares two Ubuntu 24.04 `linux/amd64` images serving
the same API. It is intentionally not a universal performance claim; package
updates, architecture, and application dependencies can change the exact size.
The independent Rockcraft experiment records a 41.8 MiB chiselled Rock versus
the 113.2 MiB Docker image on the same GitHub runner.
