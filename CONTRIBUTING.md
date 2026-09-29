# Contributing

1. Create a focused branch from `main`.
2. Run `python -m pip install -e . pytest ruff`.
3. Run `ruff check .` and `pytest`.
4. For container changes, run `./scripts/demo.sh` with Docker and Trivy installed.
5. Rock changes must pass the **Build and compare Rock** workflow; macOS users
   can follow `docs/rockcraft-comparison.md` for the Multipass setup.
6. Never commit generated reports, BuildKit caches, rocks, or credentials.
