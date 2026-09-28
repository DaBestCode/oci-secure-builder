from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .benchmark import compare_images
from .builder import ImageBuilder
from .config import load_config
from .errors import OciSecureError
from .scanner import VulnerabilityScanner
from .verifier import RuntimeVerifier


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="oci-secure", description="Build and enforce policy on OCI images"
    )
    root.add_argument("--config", type=Path, default=Path("oci-secure.toml"))
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "build", help="build the configured image with reusable BuildKit cache"
    )
    scan = commands.add_parser(
        "scan", help="scan an image with Trivy and enforce severity budgets"
    )
    scan.add_argument("--report", type=Path, default=Path("reports/trivy.json"))
    commands.add_parser(
        "verify", help="check OCI metadata, healthcheck, and runtime UID"
    )
    pipeline = commands.add_parser("pipeline", help="build, scan, and verify")
    pipeline.add_argument("--report", type=Path, default=Path("reports/trivy.json"))
    benchmark = commands.add_parser(
        "benchmark", help="compare a baseline and optimized image size"
    )
    benchmark.add_argument("baseline")
    benchmark.add_argument("optimized")
    return root


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "benchmark":
            _print(asdict(compare_images(args.baseline, args.optimized)))
            return 0
        config = load_config(args.config)
        if args.command in ("build", "pipeline"):
            metadata = ImageBuilder().build(config.build)
            _print({"stage": "build", "status": "passed", "metadata": metadata})
        if args.command in ("scan", "pipeline"):
            summary = VulnerabilityScanner().scan(
                config.build.image, config.policy, args.report
            )
            _print({"stage": "scan", "status": "passed", **asdict(summary)})
        if args.command in ("verify", "pipeline"):
            verified = RuntimeVerifier().verify(config.build.image, config.policy)
            _print({"stage": "verify", "status": "passed", **asdict(verified)})
        return 0
    except OciSecureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
