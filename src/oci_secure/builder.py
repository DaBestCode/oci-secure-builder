from __future__ import annotations

import json
import os
import shutil
from datetime import UTC, datetime

from .config import BuildConfig
from .runner import CommandRunner


class ImageBuilder:
    def __init__(self, runner: CommandRunner | None = None) -> None:
        self.runner = runner or CommandRunner()

    def build(
        self, config: BuildConfig, *, revision: str | None = None
    ) -> dict[str, object]:
        self.runner.require("docker")
        config.cache_dir.parent.mkdir(parents=True, exist_ok=True)
        metadata_file = config.cache_dir.parent / "build-metadata.json"
        next_cache = config.cache_dir.with_name(config.cache_dir.name + "-next")
        if next_cache.exists():
            shutil.rmtree(next_cache)
        command = [
            "docker",
            "buildx",
            "build",
            str(config.context),
            "--file",
            str(config.dockerfile),
            "--tag",
            config.image,
            "--platform",
            ",".join(config.platforms),
            "--load",
            "--provenance=false",
            "--metadata-file",
            str(metadata_file),
            "--label",
            f"org.opencontainers.image.created={datetime.now(UTC).isoformat()}",
            "--label",
            f"org.opencontainers.image.revision={revision or os.getenv('GITHUB_SHA', 'local')}",
        ]
        if config.cache_dir.exists():
            command.extend(["--cache-from", f"type=local,src={config.cache_dir}"])
        command.extend(["--cache-to", f"type=local,dest={next_cache},mode=max"])
        if config.target:
            command.extend(["--target", config.target])
        for key, value in sorted(config.build_args.items()):
            command.extend(["--build-arg", f"{key}={value}"])
        self.runner.run(command)

        # BuildKit cannot update a local cache in place, so rotate it only after
        # a successful build. load_config confines this deletion to the project.
        if next_cache.exists():
            if config.cache_dir.exists():
                shutil.rmtree(config.cache_dir)
            next_cache.rename(config.cache_dir)
        if metadata_file.exists():
            return json.loads(metadata_file.read_text(encoding="utf-8"))
        return {"image": config.image}
