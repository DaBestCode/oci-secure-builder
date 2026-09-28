from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .config import SEVERITIES, PolicyConfig
from .errors import OciSecureError, PolicyViolation
from .runner import CommandRunner


@dataclass(frozen=True)
class ScanSummary:
    counts: dict[str, int]
    vulnerabilities: int


def summarize_trivy(payload: dict[str, object], *, ignore_unfixed: bool) -> ScanSummary:
    counts: Counter[str] = Counter()
    total = 0
    for result in payload.get("Results", []):
        if not isinstance(result, dict):
            continue
        for vuln in result.get("Vulnerabilities") or []:
            if not isinstance(vuln, dict):
                continue
            if ignore_unfixed and not vuln.get("FixedVersion"):
                continue
            severity = str(vuln.get("Severity", "UNKNOWN")).upper()
            counts[severity if severity in SEVERITIES else "UNKNOWN"] += 1
            total += 1
    return ScanSummary({severity: counts[severity] for severity in SEVERITIES}, total)


def enforce_policy(summary: ScanSummary, policy: PolicyConfig) -> None:
    failures = []
    for severity in SEVERITIES:
        limit = policy.maximum.get(severity, -1)
        actual = summary.counts.get(severity, 0)
        if limit >= 0 and actual > limit:
            failures.append(f"{severity}: {actual} found, maximum {limit}")
    if failures:
        raise PolicyViolation("vulnerability policy failed: " + "; ".join(failures))


class VulnerabilityScanner:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self.runner = runner or CommandRunner()

    def scan(self, image: str, policy: PolicyConfig, report: Path) -> ScanSummary:
        self.runner.require("trivy")
        report.parent.mkdir(parents=True, exist_ok=True)
        command = ["trivy", "image", "--format", "json", "--output", str(report)]
        if policy.ignore_unfixed:
            command.append("--ignore-unfixed")
        command.append(image)
        self.runner.run(command)
        try:
            payload = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OciSecureError(
                f"could not read Trivy report {report}: {exc}"
            ) from exc
        summary = summarize_trivy(payload, ignore_unfixed=policy.ignore_unfixed)
        enforce_policy(summary, policy)
        return summary
