# Contributing

1. Create a focused branch from `main`.
2. Run `python -m pip install -e . pytest ruff`.
3. Run `ruff check .` and `pytest`.
4. For container changes, run `./scripts/demo.sh` with Docker and Trivy installed.
5. Never commit generated reports, BuildKit caches, or credentials.

