# OCI Secure Builder

[![Build and security policy](https://github.com/DaBestCode/oci-secure-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/DaBestCode/oci-secure-builder/actions/workflows/ci.yml)
[![Build and compare Rock](https://github.com/DaBestCode/oci-secure-builder/actions/workflows/rock.yml/badge.svg)](https://github.com/DaBestCode/oci-secure-builder/actions/workflows/rock.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A policy-driven Python CLI that builds Ubuntu-based OCI images with BuildKit,
scans them with Trivy, and proves they run as a non-root user before they can be
published. The included example makes the design easy to demonstrate live in an
interview rather than leaving the security claims as prose on a resume.

## What it demonstrates

- **Smaller images:** a multi-stage Dockerfile leaves build tools behind; the
  `benchmark` command measures the result against a single-stage baseline. The
  reproducible local run reduced the image by **80.8%** (216.8 to 41.6 MiB),
  providing margin for the resume's conservative 65% claim.
- **Fast repeat builds:** BuildKit cache mounts speed up APT work and the engine
  exports a reusable local layer cache.
- **Policy, not just reports:** Trivy JSON is evaluated against severity budgets;
  a violation exits non-zero and stops publishing.
- **Runtime hardening:** both image metadata and a real `id -u` container run are
  checked, preventing a misleading `USER` declaration from passing on its own.
- **Supply-chain workflow:** GitHub Actions tests every change, uploads SARIF to
  code scanning, and publishes to GHCR only after the release scan succeeds.
- **Rockcraft comparison:** the same API is also built from a bare base with
  Chisel slices, supervised by Pebble, scanned by the same policy, and verified
  through a Rock-aware runtime gate. The recorded CI run produced a 41.8 MiB
  Rock versus a 113.2 MiB Docker image and reported zero Rock vulnerabilities.

## Architecture

```text
oci-secure.toml
      │
      ▼
 Python CLI ──build──▶ Docker BuildKit ──▶ local OCI image
      │                                      │
      ├──scan──────────────────────────────▶ Trivy ──▶ JSON/SARIF
      │                                      │
      └──verify──▶ inspect + ephemeral run ◀─┘
                         │
                         ▼
                 pass / policy violation
```

The orchestration layer uses argument arrays rather than shell strings, making
configuration values safe from shell injection. Each external boundary is
injectable, which keeps policy tests fast and deterministic.

## Quick start

Requirements: Python 3.11+, Docker with Buildx, Trivy, and curl.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e . pytest ruff
pytest
oci-secure pipeline
```

The pipeline writes a detailed report to `reports/trivy.json`. To build the
intentionally unoptimized baseline and calculate the actual reduction:

```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

The script invokes the source tree directly, so it also works before installing
the package into a virtual environment.

Recorded output (the percentage can change with upstream Ubuntu packages):

```json
{
  "baseline_bytes": 227289356,
  "optimized_bytes": 43596722,
  "reduction_percent": 80.8
}
```

See the [benchmark methodology](docs/benchmark.md) for the controlled comparison
and environment. Re-run it before an interview if the base image has changed.

## Commands

```bash
oci-secure build
oci-secure scan --report reports/trivy.json
oci-secure verify
oci-secure pipeline
oci-secure benchmark oci-secure-demo:baseline oci-secure-demo:local
oci-secure compare oci-secure-demo:local oci-secure-demo:rock
oci-secure verify-rock oci-secure-demo:rock
```

Edit `oci-secure.toml` to change the context, tag, platform, labels, and allowed
vulnerability counts. A value of `-1` means unlimited; `0` means none allowed.
By default, vulnerabilities without a vendor fix are recorded by Trivy but are
excluded from the blocking count.

## Five-minute interview demo

1. Show `oci-secure.toml` and explain that it separates policy from execution.
2. Run `oci-secure pipeline`; point out the build, scan, and runtime gates.
3. Run the benchmark and explain why compiler and package-manager layers never
   enter the runtime stage.
4. Change `USER 10001:10001` to `USER root`, rebuild, and show `verify` fail.
5. Open the Actions run and its downloadable Trivy report; explain that a tag
   can reach GHCR only after the same security gate passes.
6. Open the Rock comparison artifact; contrast direct-process/OCI health with
   Pebble supervision/readiness, then explain how the Chisel slices follow from
   the application's Python imports.

For a container-focused interview, continue with the
[Docker versus Rockcraft experiment](docs/rockcraft-comparison.md). It packages
the same API with a bare base, Chisel slices and a Pebble service, then records
the size, user, entrypoint, layers, health model and scan results in CI.

## Design trade-offs

- The CLI shells out to mature Docker and Trivy engines instead of reimplementing
  OCI building or vulnerability databases. Its responsibility is deterministic
  orchestration and policy enforcement.
- `--load` provides a local image for runtime verification and therefore accepts
  a single platform per local run. The release workflow performs registry output
  separately after the policy gate.
- Ignoring unfixed findings avoids blocking on vulnerabilities with no available
  remediation, while the raw report still preserves them for review.

## Repository map

```text
src/oci_secure/           CLI, builder, scanner, verifier, benchmark
tests/                    isolated policy and configuration tests
examples/hello-api/       hardened and baseline Ubuntu images
                          plus the equivalent rockcraft.yaml
.github/workflows/        continuous policy gate and release publishing
                          plus Rock packing and comparison
oci-secure.toml           build and security policy as code
scripts/demo.sh           reproducible end-to-end interview demo
```

Released under the [MIT License](LICENSE).
