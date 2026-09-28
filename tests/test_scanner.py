import pytest

from oci_secure.config import PolicyConfig
from oci_secure.errors import PolicyViolation
from oci_secure.scanner import enforce_policy, summarize_trivy

PAYLOAD = {
    "Results": [
        {
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-1",
                    "Severity": "CRITICAL",
                    "FixedVersion": "1.2",
                },
                {"VulnerabilityID": "CVE-2", "Severity": "HIGH", "FixedVersion": ""},
                {"VulnerabilityID": "CVE-3", "Severity": "LOW", "FixedVersion": "1.1"},
            ]
        }
    ]
}


def policy(**limits: int) -> PolicyConfig:
    maximum = {
        severity: -1 for severity in ("UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL")
    }
    maximum.update(limits)
    return PolicyConfig(maximum=maximum)


def test_summary_ignores_unfixed_vulnerabilities() -> None:
    result = summarize_trivy(PAYLOAD, ignore_unfixed=True)
    assert result.vulnerabilities == 2
    assert result.counts["CRITICAL"] == 1
    assert result.counts["HIGH"] == 0


def test_policy_reports_threshold_violation() -> None:
    result = summarize_trivy(PAYLOAD, ignore_unfixed=True)
    with pytest.raises(PolicyViolation, match="CRITICAL: 1 found, maximum 0"):
        enforce_policy(result, policy(CRITICAL=0))
