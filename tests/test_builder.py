import json
from pathlib import Path

from oci_secure.builder import ImageBuilder
from oci_secure.config import BuildConfig
from oci_secure.runner import CommandResult


class FakeRunner:
    def __init__(self) -> None:
        self.command: list[str] = []

    def require(self, executable: str) -> None:
        assert executable == "docker"

    def run(self, command: list[str]) -> CommandResult:
        self.command = command
        cache_to = command[command.index("--cache-to") + 1]
        next_cache = Path(cache_to.split("dest=", 1)[1].split(",", 1)[0])
        next_cache.mkdir()
        (next_cache / "new-layer").write_text("cached")

        metadata = Path(command[command.index("--metadata-file") + 1])
        metadata.write_text(json.dumps({"containerimage.digest": "sha256:test"}))
        return CommandResult("", "", 0)


def test_builder_uses_and_rotates_local_buildkit_cache(tmp_path: Path) -> None:
    cache = tmp_path / ".buildx-cache"
    cache.mkdir()
    (cache / "old-layer").write_text("stale")
    runner = FakeRunner()
    config = BuildConfig(
        image="example:test",
        context=tmp_path,
        dockerfile=tmp_path / "Dockerfile",
        build_args={"EXAMPLE": "value"},
        cache_dir=cache,
    )

    result = ImageBuilder(runner).build(config, revision="abc123")

    assert result["containerimage.digest"] == "sha256:test"
    assert ["--cache-from", f"type=local,src={cache}"] == runner.command[
        runner.command.index("--cache-from") : runner.command.index("--cache-from") + 2
    ]
    assert "type=local" in runner.command[runner.command.index("--cache-to") + 1]
    assert "mode=max" in runner.command[runner.command.index("--cache-to") + 1]
    assert (cache / "new-layer").is_file()
    assert not (cache / "old-layer").exists()
    assert "org.opencontainers.image.revision=abc123" in runner.command
    assert "EXAMPLE=value" in runner.command
