import json

from oci_secure.profile import profile_images
from oci_secure.runner import CommandResult


class FakeRunner:
    def require(self, executable: str) -> None:
        pass

    def run(self, command: list[str]) -> CommandResult:
        payload = [
            {
                "Size": 10485760,
                "Os": "linux",
                "Architecture": "amd64",
                "Config": {
                    "User": "10001:10001",
                    "Entrypoint": ["/bin/pebble"],
                    "Cmd": ["run"],
                    "Healthcheck": None,
                },
                "RootFS": {"Layers": ["one", "two"]},
            }
        ]
        return CommandResult(json.dumps(payload), "", 0)


def test_profile_reports_runtime_shape() -> None:
    profile = profile_images(["example:rock"], FakeRunner())[0]
    assert profile.size_mib == 10.0
    assert profile.entrypoint == ("/bin/pebble",)
    assert profile.layers == 2
    assert not profile.oci_healthcheck
