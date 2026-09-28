from pathlib import Path

from oci_secure.config import load_config


def test_load_project_config(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM scratch\n")
    (tmp_path / "oci-secure.toml").write_text(
        """[build]
image = "example:test"
[policy.maximum]
critical = 0
high = 2
"""
    )
    config = load_config(tmp_path / "oci-secure.toml")
    assert config.build.image == "example:test"
    assert config.policy.maximum["CRITICAL"] == 0
    assert config.policy.maximum["HIGH"] == 2
