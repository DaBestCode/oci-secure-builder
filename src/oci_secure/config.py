from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import OciSecureError

SEVERITIES = ("UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL")
DEFAULT_REQUIRED_LABELS = (
    "org.opencontainers.image.source",
    "org.opencontainers.image.revision",
    "org.opencontainers.image.created",
)


@dataclass(frozen=True)
class BuildConfig:
    image: str
    context: Path
    dockerfile: Path
    target: str | None = None
    platforms: tuple[str, ...] = ("linux/amd64",)
    build_args: dict[str, str] = field(default_factory=dict)
    cache_dir: Path = Path(".buildx-cache")


@dataclass(frozen=True)
class PolicyConfig:
    maximum: dict[str, int]
    ignore_unfixed: bool = True
    require_non_root: bool = True
    require_healthcheck: bool = True
    required_labels: tuple[str, ...] = DEFAULT_REQUIRED_LABELS


@dataclass(frozen=True)
class ProjectConfig:
    path: Path
    build: BuildConfig
    policy: PolicyConfig


def load_config(path: Path) -> ProjectConfig:
    path = path.resolve()
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        image = raw["build"]["image"]
    except (OSError, tomllib.TOMLDecodeError, KeyError) as exc:
        raise OciSecureError(f"invalid configuration {path}: {exc}") from exc

    root = path.parent
    build_raw = raw["build"]
    policy_raw = raw.get("policy", {})
    maximum = {
        severity: int(policy_raw.get("maximum", {}).get(severity.lower(), -1))
        for severity in SEVERITIES
    }
    build = BuildConfig(
        image=str(image),
        context=(root / build_raw.get("context", ".")).resolve(),
        dockerfile=(root / build_raw.get("dockerfile", "Dockerfile")).resolve(),
        target=build_raw.get("target"),
        platforms=tuple(build_raw.get("platforms", ["linux/amd64"])),
        build_args={
            str(key): str(value) for key, value in build_raw.get("args", {}).items()
        },
        cache_dir=(root / build_raw.get("cache_dir", ".buildx-cache")).resolve(),
    )
    policy = PolicyConfig(
        maximum=maximum,
        ignore_unfixed=bool(policy_raw.get("ignore_unfixed", True)),
        require_non_root=bool(policy_raw.get("require_non_root", True)),
        require_healthcheck=bool(policy_raw.get("require_healthcheck", True)),
        required_labels=tuple(
            policy_raw.get("required_labels", DEFAULT_REQUIRED_LABELS)
        ),
    )
    if not build.context.is_dir():
        raise OciSecureError(f"build context does not exist: {build.context}")
    if not build.dockerfile.is_file():
        raise OciSecureError(f"Dockerfile does not exist: {build.dockerfile}")
    if not build.cache_dir.is_relative_to(root):
        raise OciSecureError("cache_dir must remain inside the project directory")
    return ProjectConfig(path=path, build=build, policy=policy)
