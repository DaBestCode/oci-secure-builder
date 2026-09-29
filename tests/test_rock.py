import json

from oci_secure.rock import RockVerifier
from oci_secure.runner import CommandResult


class FakeRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def require(self, executable: str) -> None:
        pass

    def run(self, command: list[str], **kwargs: object) -> CommandResult:
        self.commands.append(command)
        if "inspect" in command:
            payload = [
                {
                    "Os": "linux",
                    "Config": {"User": "584792", "Entrypoint": ["/bin/pebble"]},
                }
            ]
            return CommandResult(json.dumps(payload), "", 0)
        if command[1:3] == ["run", "--detach"]:
            return CommandResult("container-id\n", "", 0)
        if "import os; print(os.getuid())" in command:
            return CommandResult("584792\n", "", 0)
        if "urllib.request" in " ".join(command):
            return CommandResult("", "", 0)
        if command[-1] == "checks":
            return CommandResult("api-ready ready up", "", 0)
        return CommandResult("", "", 0)


def test_rock_verifier_checks_pebble_uid_health_and_cleans_up() -> None:
    runner = FakeRunner()
    result = RockVerifier(runner, sleep=lambda _: None).verify("example:rock")
    assert result.runtime_uid == 584792
    assert result.pebble_entrypoint == "/bin/pebble"
    assert any(command[1:3] == ["rm", "--force"] for command in runner.commands)
