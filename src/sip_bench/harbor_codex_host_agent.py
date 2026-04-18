from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

try:
    from harbor.agents.installed.codex import Codex
    from harbor.environments.base import BaseEnvironment
    from harbor.models.agent.context import AgentContext
except ModuleNotFoundError:  # pragma: no cover - lets unit tests import helpers without Harbor on PYTHONPATH
    class Codex:  # type: ignore[no-redef]
        pass

    BaseEnvironment = Any  # type: ignore[assignment]
    AgentContext = Any  # type: ignore[assignment]


def rewrite_instruction_for_host_workspace(
    *,
    instruction: str,
    container_workdir: str,
    helper_scripts_available: bool = False,
) -> str:
    prefix = (
        "You are working in a host-side mirror of the task container's working directory.\n"
        f"The current working directory corresponds to `{container_workdir}` inside the container.\n"
        "When the task mentions absolute paths under that directory, use the matching relative paths in the current directory.\n"
        "Edit files in the current working directory only. Your final file changes will be synchronized back into the container before verification.\n\n"
    )
    if helper_scripts_available:
        prefix += (
            "Helper scripts are available in the current directory:\n"
            '- `./task_shell "<command>"` runs a shell command inside the task container working environment.\n'
            "- `./task_put <local_path> <container_path>` copies a local file into the running container.\n"
            "- `./task_get <container_path> <local_path>` copies a file from the running container back into the local workspace.\n"
            "Use these helpers whenever you need container-only dependencies or want to validate behavior inside the task environment.\n\n"
        )
    return prefix + instruction


def infer_workdir_from_dockerfile(dockerfile_path: str | Path) -> str:
    dockerfile = Path(dockerfile_path)
    if not dockerfile.exists():
        return "/"
    workdir = "/"
    pattern = re.compile(r"^\s*WORKDIR\s+(.+?)\s*$", re.IGNORECASE)
    for line in dockerfile.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        candidate = match.group(1).strip()
        if candidate:
            workdir = candidate.strip('"').strip("'")
    return workdir


def extract_usage_from_codex_output(raw_output: str) -> dict[str, int]:
    usage_totals = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
    }
    for line in raw_output.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if payload.get("type") != "turn.completed":
            continue
        usage = payload.get("usage") or {}
        usage_totals["input_tokens"] = int(usage.get("input_tokens") or 0)
        usage_totals["cached_input_tokens"] = int(usage.get("cached_input_tokens") or 0)
        usage_totals["output_tokens"] = int(usage.get("output_tokens") or 0)
    return usage_totals


class CodexLocalAuthAgent(Codex):
    """Run Codex on the host with ChatGPT login auth, then sync outputs into Harbor."""

    def __init__(
        self,
        auth_source: str | None = None,
        config_source: str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._auth_source = (
            Path(auth_source).expanduser()
            if auth_source
            else Path.home() / ".codex" / "auth.json"
        )
        self._config_source = (
            Path(config_source).expanduser()
            if config_source
            else Path.home() / ".codex" / "config.toml"
        )

    @staticmethod
    def name() -> str:
        return "codex-local-auth"

    async def setup(self, environment: BaseEnvironment) -> None:
        # The host already has Codex installed and authenticated. No container setup.
        return None

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        if not self.model_name:
            raise ValueError("Model name is required")

        container_workdir = await self._resolve_container_workdir(environment)
        workspace_dir = self.logs_dir / "host-workspace"
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        task_dir = Path(environment.environment_dir).resolve().parent
        seeded_files = seed_host_workspace_from_task_environment(
            task_dir=task_dir,
            workspace_dir=workspace_dir,
        )
        if not seeded_files:
            await environment.download_dir(container_workdir, workspace_dir)
        helper_script_paths = create_task_helper_scripts(
            workspace_dir=workspace_dir,
            environment=environment,
        )

        rendered_instruction = rewrite_instruction_for_host_workspace(
            instruction=instruction,
            container_workdir=container_workdir,
            helper_scripts_available=bool(helper_script_paths),
        )
        codex_output_path = self.logs_dir / self._OUTPUT_FILENAME

        with tempfile.TemporaryDirectory(prefix="sip-codex-home-") as tmpdir:
            codex_home = Path(tmpdir)
            self._prepare_codex_home(codex_home)
            raw_output, return_code = await self._run_host_codex(
                workspace_dir=workspace_dir,
                codex_home=codex_home,
                instruction=rendered_instruction,
            )
            codex_output_path.write_text(raw_output, encoding="utf-8")
            self._copy_codex_sessions(codex_home)

        usage = extract_usage_from_codex_output(raw_output)
        context.n_input_tokens = usage["input_tokens"] or None
        context.n_cache_tokens = usage["cached_input_tokens"] or None
        context.n_output_tokens = usage["output_tokens"] or None
        context.metadata = {
            "execution_backend": "host_codex_exec",
            "container_workdir": container_workdir,
            "host_workspace": str(workspace_dir),
        }

        if return_code != 0:
            raise RuntimeError(
                f"Host codex exec failed with exit code {return_code}. "
                f"See {codex_output_path}"
            )

        for helper_script_path in helper_script_paths:
            helper_script_path.unlink(missing_ok=True)
        await environment.upload_dir(workspace_dir, container_workdir)

        # Preserve richer ATIF trajectory when Codex emits session logs.
        self.populate_context_post_run(context)
        if context.metadata:
            context.metadata.update(
                {
                    "execution_backend": "host_codex_exec",
                    "container_workdir": container_workdir,
                    "host_workspace": str(workspace_dir),
                }
            )

    async def _resolve_container_workdir(self, environment: BaseEnvironment) -> str:
        pwd_result = await environment.exec("pwd")
        if pwd_result.return_code == 0 and pwd_result.stdout:
            lines = [line.strip() for line in pwd_result.stdout.splitlines() if line.strip()]
            if lines:
                return lines[-1]
        return infer_workdir_from_dockerfile(environment.environment_dir / "Dockerfile")

    def _prepare_codex_home(self, codex_home: Path) -> None:
        if not self._auth_source.exists():
            raise FileNotFoundError(f"Codex auth file not found: {self._auth_source}")
        shutil.copy2(self._auth_source, codex_home / "auth.json")
        if self._config_source.exists():
            shutil.copy2(self._config_source, codex_home / "config.toml")

    async def _run_host_codex(
        self,
        *,
        workspace_dir: Path,
        codex_home: Path,
        instruction: str,
    ) -> tuple[str, int]:
        model = self.model_name.split("/")[-1]
        reasoning_effort = self._reasoning_effort
        command = [
            "codex",
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "--skip-git-repo-check",
            "--model",
            model,
            "--json",
            "--enable",
            "unified_exec",
        ]
        if reasoning_effort:
            command.extend(["-c", f"model_reasoning_effort={reasoning_effort}"])
        command.extend(["--", instruction])

        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
        env.pop("OPENAI_API_KEY", None)
        env.pop("OPENAI_BASE_URL", None)
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env.pop("SIP_HARBOR_CODEX_AUTH_SOURCE", None)

        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(workspace_dir),
            env=env,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout_bytes, _ = await process.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        return stdout, int(process.returncode or 0)

    def _copy_codex_sessions(self, codex_home: Path) -> None:
        source_sessions = codex_home / "sessions"
        if not source_sessions.exists():
            return
        target_sessions = self.logs_dir / "sessions"
        shutil.copytree(source_sessions, target_sessions, dirs_exist_ok=True)


def create_task_helper_scripts(*, workspace_dir: Path, environment: Any) -> list[Path]:
    compose_paths = getattr(environment, "_docker_compose_paths", None)
    session_id = getattr(environment, "session_id", None)
    environment_dir = getattr(environment, "environment_dir", None)
    if not compose_paths or not session_id or environment_dir is None:
        return []

    compose_base = [
        "docker",
        "compose",
        "-p",
        str(session_id).lower().replace(".", "-"),
        "--project-directory",
        str(Path(environment_dir).resolve()),
    ]
    for compose_path in compose_paths:
        compose_base.extend(["-f", str(Path(compose_path).resolve())])
    compose_base_text = " ".join(_shell_quote(part) for part in compose_base)

    scripts = {
        "task_shell": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'if [ "$#" -ne 1 ]; then\n'
            '  echo "usage: ./task_shell \\"<command>\\"" >&2\n'
            "  exit 2\n"
            "fi\n"
            f'{compose_base_text} exec -T main bash -lc "$1"\n'
        ),
        "task_put": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'if [ "$#" -ne 2 ]; then\n'
            '  echo "usage: ./task_put <local_path> <container_path>" >&2\n'
            "  exit 2\n"
            "fi\n"
            f'{compose_base_text} cp "$1" "main:$2"\n'
        ),
        "task_get": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'if [ "$#" -ne 2 ]; then\n'
            '  echo "usage: ./task_get <container_path> <local_path>" >&2\n'
            "  exit 2\n"
            "fi\n"
            'mkdir -p "$(dirname "$2")"\n'
            f'{compose_base_text} cp "main:$1" "$2"\n'
        ),
    }
    written_paths: list[Path] = []
    for name, body in scripts.items():
        script_path = workspace_dir / name
        script_path.write_text(body, encoding="utf-8")
        script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)
        written_paths.append(script_path)
    return written_paths


def seed_host_workspace_from_task_environment(*, task_dir: Path, workspace_dir: Path) -> list[Path]:
    environment_dir = task_dir / "environment"
    if not environment_dir.exists():
        return []
    copied_paths: list[Path] = []
    ignored_names = {"Dockerfile", "docker-compose.yaml", "docker-compose.yml"}
    for source_path in sorted(environment_dir.iterdir()):
        if source_path.name in ignored_names:
            continue
        destination_path = workspace_dir / source_path.name
        if source_path.is_dir():
            shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
        else:
            shutil.copy2(source_path, destination_path)
        copied_paths.append(destination_path)
    return copied_paths


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"
