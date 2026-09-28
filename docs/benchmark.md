# Reproducible size benchmark

The repository includes two Ubuntu 24.04 images that serve the same HTTP API:

- `Dockerfile.baseline` is a conventional single-stage build that retains its
  compiler, headers, Git client, package indexes, and other build dependencies.
- `Dockerfile` creates the Python zip application in a builder stage and copies
  only that artifact into a runtime stage with the minimum runtime packages.

Run `./scripts/demo.sh` to rebuild both images for `linux/amd64`, enforce the
security policy, compare their Docker-reported sizes, and exercise the health
endpoint as a non-root user.

## Recorded result

Measured on 2026-09-28 using Ubuntu 24.04 package repositories and Docker 29.4.0:

| Image | Size |
|---|---:|
| Single-stage baseline | 227,289,356 bytes (216.8 MiB) |
| Multi-stage runtime | 43,596,722 bytes (41.6 MiB) |
| Reduction | **80.8%** |

The resume uses the more conservative **65%** figure because upstream package
contents and compression can change. This recorded run demonstrates that the
claim is reproducible with margin, not that every application will shrink by
the same percentage.

For a fair comparison, both images use the same Ubuntu release, application,
and `linux/amd64` target. The size command reads the `Size` fields returned by
`docker image inspect` in request order.
