import json

import pytest

from oci_secure.config import PolicyConfig
from oci_secure.errors import PolicyViolation
from oci_secure.runner import CommandResult
from oci_secure.verifier import RuntimeVerifier


class FakeRunner:
    def __init__(self, user: str, uid: int) -> None:
        self.user = user
        self.uid = uid

    def require(self, executable: str) -> None:
        pass

    def run(self, command: list[str], **kwargs: object) -> CommandResult:
        if "inspect" in command:
            payload = [
                {
                    "Os": "linux",
                    "Architecture": "amd64",
                    "Config": {
                        "User": self.user,
                        "Healthcheck": {"Test": ["CMD", "true"]},
                        "Labels": {"org.opencontainers.image.source": "repo"},
                    },
                }
            ]
            return CommandResult(json.dumps(payload), "", 0)
        return CommandResult(str(self.uid), "", 0)


def test_verifies_runtime_uid() -> None:
    policy = PolicyConfig(
        maximum={}, required_labels=("org.opencontainers.image.source",)
    )
    result = RuntimeVerifier(FakeRunner("10001:10001", 10001)).verify(
        "demo:latest", policy
    )
    assert result.runtime_uid == 10001


def test_rejects_root_image() -> None:
    policy = PolicyConfig(
        maximum={}, required_labels=("org.opencontainers.image.source",)
    )
    with pytest.raises(PolicyViolation, match="root"):
        RuntimeVerifier(FakeRunner("root", 0)).verify("demo:latest", policy)
