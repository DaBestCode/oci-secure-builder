from __future__ import annotations

import json
from dataclasses import dataclass

from .errors import OciSecureError
from .runner import CommandRunner


@dataclass(frozen=True)
class SizeComparison:
    baseline_bytes: int
    optimized_bytes: int
    reduction_percent: float


def compare_images(
    baseline: str, optimized: str, runner: CommandRunner | None = None
) -> SizeComparison:
    runner = runner or CommandRunner()
    runner.require("docker")
    raw = runner.run(["docker", "image", "inspect", baseline, optimized]).stdout
    images = json.loads(raw)
    if len(images) != 2:
        raise OciSecureError("docker inspect did not return both requested images")
    baseline_size = int(images[0]["Size"])
    optimized_size = int(images[1]["Size"])
    reduction = ((baseline_size - optimized_size) / baseline_size) * 100
    return SizeComparison(baseline_size, optimized_size, round(reduction, 1))
