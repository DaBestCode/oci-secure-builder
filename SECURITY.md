# Security policy

Please do not open a public issue for a suspected vulnerability. Use GitHub's
private vulnerability reporting for this repository instead.

The CI policy blocks publish when Trivy finds a fixable HIGH or CRITICAL image
vulnerability. Runtime checks also require a non-root user, a health check,
Linux compatibility, and the configured OCI metadata labels.

The Kubernetes compatibility gate adds `runAsNonRoot`, a read-only root
filesystem, `RuntimeDefault` seccomp, disabled privilege escalation, and an
empty effective capability set. Registry publication uses the same local image
that passed the Trivy, Docker-runtime, and Kubernetes-runtime gates.
