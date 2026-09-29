from __future__ import annotations

import json
import re
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath

from .errors import OciSecureError, PolicyViolation
from .runner import CommandRunner


@dataclass(frozen=True)
class RockVerificationResult:
    image: str
    configured_user: str
    runtime_uid: int
    pebble_entrypoint: str
    pebble_checks: str
    health_url: str


class RockVerifier:
    """Verify Rock-specific runtime behavior without assuming Docker semantics."""

    def __init__(
        self,
        runner: CommandRunner | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.runner = runner or CommandRunner()
        self.sleep = sleep

    def verify(
        self,
        image: str,
        *,
        health_url: str = "http://127.0.0.1:8080/health",
        attempts: int = 15,
    ) -> RockVerificationResult:
        self.runner.require("docker")
        raw = self.runner.run(["docker", "image", "inspect", image]).stdout
        try:
            info = json.loads(raw)[0]
        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as exc:
            raise OciSecureError(
                f"unexpected docker inspect response for {image}"
            ) from exc

        config = info.get("Config") or {}
        user = str(config.get("User") or "")
        entrypoint = tuple(config.get("Entrypoint") or ())
        failures: list[str] = []
        if user in ("", "0", "root", "0:0", "root:root"):
            failures.append("rock USER is root or unset")
        pebble = next(
            (item for item in entrypoint if PurePosixPath(item).name == "pebble"), ""
        )
        if not pebble:
            failures.append("OCI entrypoint is not Pebble")
        if info.get("Os") != "linux":
            failures.append(f"expected linux image, found {info.get('Os')!r}")
        if failures:
            raise PolicyViolation("rock policy failed: " + "; ".join(failures))

        name = f"oci-secure-rock-{uuid.uuid4().hex[:12]}"
        container_id = self.runner.run(
            ["docker", "run", "--detach", "--name", name, image]
        ).stdout.strip()
        runtime_uid = -1
        checks_output = ""
        try:
            uid = self.runner.run(
                [
                    "docker",
                    "exec",
                    container_id,
                    "/usr/bin/python3",
                    "-c",
                    "import os; print(os.getuid())",
                ],
                check=False,
            )
            try:
                runtime_uid = int(uid.stdout.strip())
            except ValueError:
                failures.append("could not determine the Rock's runtime UID")
            if runtime_uid == 0:
                failures.append("Rock executes as UID 0")

            healthy = False
            for _ in range(attempts):
                probe = self.runner.run(
                    [
                        "docker",
                        "exec",
                        container_id,
                        "/usr/bin/python3",
                        "-c",
                        (
                            "import urllib.request; "
                            f"urllib.request.urlopen('{health_url}', timeout=2).read()"
                        ),
                    ],
                    check=False,
                )
                checks = self.runner.run(
                    ["docker", "exec", container_id, pebble, "checks"], check=False
                )
                checks_output = checks.stdout.strip()
                check_is_up = bool(
                    re.search(r"\bapi-ready\b.*\bup\b", checks_output, re.DOTALL)
                )
                if probe.returncode == 0 and checks.returncode == 0 and check_is_up:
                    healthy = True
                    break
                self.sleep(1)
            if not healthy:
                failures.append(
                    "Pebble service or readiness check did not become healthy"
                )
        finally:
            self.runner.run(["docker", "rm", "--force", container_id], check=False)

        if failures:
            raise PolicyViolation("rock policy failed: " + "; ".join(failures))
        return RockVerificationResult(
            image=image,
            configured_user=user,
            runtime_uid=runtime_uid,
            pebble_entrypoint=pebble,
            pebble_checks=checks_output,
            health_url=health_url,
        )
