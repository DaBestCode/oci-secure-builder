# Docker and Rockcraft comparison

This experiment packages the same dependency-free Python HTTP service twice:
once with the repository's multi-stage Dockerfile and once as a chiselled Rock.
It is deliberately a comparison of two production models, not an attempt to
make their filesystems byte-for-byte identical.

## Design

| Concern | Docker image | Rockcraft image |
|---|---|---|
| Build declaration | Imperative Dockerfile stages | Declarative `rockcraft.yaml` parts |
| Runtime base | Ubuntu 24.04 | `bare` plus selected Ubuntu Chisel slices |
| Build lifecycle | Ordered BuildKit layers | pull, overlay, build, stage, and prime |
| Process model | Python is the direct container process | Pebble is PID 1 and supervises Python |
| Non-root identity | Explicit UID/GID 10001 | Rockcraft `_daemon_` user |
| Health model | OCI/Docker `HEALTHCHECK` | Pebble readiness check |
| Security gate | Trivy plus generic runtime verifier | Same Trivy policy plus Rock-aware verifier |

The Rock uses `python3_core`, `libpython3.12-stdlib_internet`, and
`libpython3.12-stdlib_net-data` rather than the complete Python Debian package.
The slice choice is traceable to the application imports: `http.server` lives
in the internet slice and `json` lives in net-data. Dependencies of those slices
are resolved transitively by Chisel.

## Reproduce the build

The checked-in GitHub workflow is the reproducible path and avoids requiring a
macOS interviewer machine to have Multipass, LXD, Snap, and Rockcraft installed.
Run **Build and compare Rock** manually from the Actions tab, or change the Rock
or application files to trigger it. The workflow:

1. Packs `examples/hello-api/rockcraft.yaml` with Canonical's official action.
2. Imports the resulting OCI archive into Docker with Rockcraft's Skopeo alias.
3. Scans it through this project's existing Trivy severity policy.
4. Starts the Rock and verifies Pebble, `_daemon_` runtime UID, `/health`, and
   the declared Pebble readiness check.
5. Builds the equivalent Docker image and records comparable OCI facts.
6. Uploads the `.rock`, Trivy JSON, and comparison JSON as workflow artifacts.

For local development on macOS, Canonical's documented path is an Ubuntu VM:

```bash
multipass launch --memory 4G --disk 20G --name rock-dev 24.04
multipass mount "$PWD" rock-dev:/home/ubuntu/oci-secure-builder
multipass exec rock-dev -- sudo snap install lxd
multipass exec rock-dev -- sudo lxd init --auto
multipass exec rock-dev -- sudo snap install rockcraft --classic
multipass exec rock-dev -- bash -lc \
  'cd /home/ubuntu/oci-secure-builder/examples/hello-api && rockcraft pack'
```

## Inspect the result

After importing the `.rock` archive as `oci-secure-demo:rock`:

```bash
oci-secure verify-rock oci-secure-demo:rock
oci-secure scan --image oci-secure-demo:rock --report reports/rock-trivy.json
oci-secure compare oci-secure-demo:docker oci-secure-demo:rock
docker run --rm oci-secure-demo:rock exec python3 -c \
  'import os; print(os.getuid())'
```

## Interview discussion

- A Rock is still an OCI image, so Docker can run it and Trivy can scan it.
- `bare` does not mean empty. Rockcraft injects Pebble and Rock metadata, then
  Chisel supplies selected Ubuntu file slices and their transitive dependencies.
- Pebble deliberately replaces the Dockerfile's direct Python process. It gives
  the image a service plan, restart semantics, readiness checks, and a proper
  init process, at the cost of extra runtime content.
- Docker `HEALTHCHECK` and Pebble checks are not interchangeable metadata. The
  engine therefore has separate verification paths instead of weakening the
  Docker check or pretending a Rock has one.
- Chisel reduces installed content, but selecting too few slices causes runtime
  import failures. The health test is therefore as important as a successful
  `rockcraft pack`.
- The exact size winner is less important than explaining why the images differ:
  base choice, Pebble, metadata, Python slice granularity, and layer construction.

## Scope boundary

This repository consumes Rockcraft; it does not claim to contribute to the
Rockcraft codebase. Upstream contributions should begin with an unclaimed issue,
maintainer coordination, the Canonical contributor agreement, and Rockcraft's
own tests. That process is more credible than submitting a duplicate patch solely
for an interview.

