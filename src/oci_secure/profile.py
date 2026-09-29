from __future__ import annotations

import json
from dataclasses import dataclass

from .errors import OciSecureError
from .runner import CommandRunner


@dataclass(frozen=True)
class ImageProfile:
    image: str
    size_bytes: int
    size_mib: float
    user: str
    entrypoint: tuple[str, ...]
    command: tuple[str, ...]
    layers: int
    os: str
    architecture: str
    oci_healthcheck: bool


def profile_images(
    images: list[str], runner: CommandRunner | None = None
) -> list[ImageProfile]:
    if not images:
        raise OciSecureError("at least one image is required")
    runner = runner or CommandRunner()
    runner.require("docker")
    raw = runner.run(["docker", "image", "inspect", *images]).stdout
    try:
        inspected = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OciSecureError("docker inspect returned invalid JSON") from exc
    if len(inspected) != len(images):
        raise OciSecureError("docker inspect did not return every requested image")

    profiles = []
    for image, info in zip(images, inspected, strict=True):
        config = info.get("Config") or {}
        size = int(info.get("Size") or 0)
        profiles.append(
            ImageProfile(
                image=image,
                size_bytes=size,
                size_mib=round(size / (1024 * 1024), 1),
                user=str(config.get("User") or "root (implicit)"),
                entrypoint=tuple(config.get("Entrypoint") or ()),
                command=tuple(config.get("Cmd") or ()),
                layers=len((info.get("RootFS") or {}).get("Layers") or ()),
                os=str(info.get("Os") or "unknown"),
                architecture=str(info.get("Architecture") or "unknown"),
                oci_healthcheck=bool(config.get("Healthcheck")),
            )
        )
    return profiles
