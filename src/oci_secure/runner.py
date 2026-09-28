from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .errors import OciSecureError, ToolMissingError


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


class CommandRunner:
    """Small injectable process boundary; no shell means no command injection."""

    def require(self, executable: str) -> None:
        if shutil.which(executable) is None:
            raise ToolMissingError(f"required executable not found: {executable}")

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        check: bool = True,
    ) -> CommandResult:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        result = CommandResult(completed.stdout, completed.stderr, completed.returncode)
        if check and result.returncode != 0:
            detail = (
                result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
            )
            raise OciSecureError(
                f"command failed ({result.returncode}): {' '.join(command)}\n{detail}"
            )
        return result
