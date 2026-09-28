import json

from oci_secure.benchmark import compare_images
from oci_secure.runner import CommandResult


class FakeRunner:
    def require(self, executable: str) -> None:
        pass

    def run(self, command: list[str]) -> CommandResult:
        # RepoTags intentionally do not match the requested aliases: Docker
        # inspect guarantees result order, not that an alias is RepoTags[0].
        payload = [
            {"RepoTags": ["other:tag"], "Size": 400},
            {"RepoTags": ["another:tag"], "Size": 100},
        ]
        return CommandResult(json.dumps(payload), "", 0)


def test_compare_images_uses_inspect_order() -> None:
    result = compare_images("baseline:test", "optimized:test", FakeRunner())
    assert result.reduction_percent == 75.0
