from __future__ import annotations

import json
from dataclasses import dataclass

from .config import PolicyConfig
from .errors import OciSecureError, PolicyViolation
from .runner import CommandRunner


@dataclass(frozen=True)
class VerificationResult:
    image: str
    configured_user: str
    runtime_uid: int
    os: str
    architecture: str


class RuntimeVerifier:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self.runner = runner or CommandRunner()

    def verify(self, image: str, policy: PolicyConfig) -> VerificationResult:
        self.runner.require("docker")
        raw = self.runner.run(["docker", "image", "inspect", image]).stdout
        try:
            info = json.loads(raw)[0]
        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as exc:
            raise OciSecureError(
                f"unexpected docker inspect response for {image}"
            ) from exc

        image_config = info.get("Config") or {}
        user = str(image_config.get("User") or "")
        healthcheck = image_config.get("Healthcheck")
        labels = image_config.get("Labels") or {}
        failures: list[str] = []
        if policy.require_non_root and user in ("", "0", "root", "0:0", "root:root"):
            failures.append("image USER is root or unset")
        if policy.require_healthcheck and not healthcheck:
            failures.append("image has no HEALTHCHECK")
        missing = [label for label in policy.required_labels if not labels.get(label)]
        if missing:
            failures.append("missing OCI labels: " + ", ".join(missing))
        if info.get("Os") != "linux":
            failures.append(f"expected linux image, found {info.get('Os')!r}")

        uid_result = self.runner.run(
            ["docker", "run", "--rm", "--entrypoint", "id", image, "-u"], check=False
        )
        try:
            runtime_uid = int(uid_result.stdout.strip())
        except ValueError:
            failures.append("could not execute `id -u` in the container")
            runtime_uid = -1
        if policy.require_non_root and runtime_uid == 0:
            failures.append("container executes as UID 0")
        if failures:
            raise PolicyViolation("runtime policy failed: " + "; ".join(failures))
        return VerificationResult(
            image, user, runtime_uid, str(info.get("Os")), str(info.get("Architecture"))
        )
