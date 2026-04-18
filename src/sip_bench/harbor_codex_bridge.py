from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Any


def build_codex_auth_setup_command(
    *,
    auth_source: str | Path | None = None,
    api_key_env_var: str = "OPENAI_API_KEY",
) -> str:
    source_path = Path(auth_source).expanduser() if auth_source else Path.home() / ".codex" / "auth.json"
    escaped_source = shlex.quote(str(source_path))
    python_source = repr(str(source_path))
    return (
        "mkdir -p /tmp/codex-secrets\n"
        f'if [ -n "${{{api_key_env_var}}}" ]; then\n'
        "cat >/tmp/codex-secrets/auth.json <<EOF\n"
        "{\n"
        f'  "{api_key_env_var}": "${{{api_key_env_var}}}"\n'
        "}\n"
        "EOF\n"
        f"elif [ -f {escaped_source} ]; then\n"
        "python3 - <<'PY'\n"
        "import json\n"
        "from pathlib import Path\n"
        f"src = Path({python_source})\n"
        "dst = Path('/tmp/codex-secrets/auth.json')\n"
        "data = json.loads(src.read_text(encoding='utf-8'))\n"
        "if not data.get('OPENAI_API_KEY'):\n"
        "    data.pop('OPENAI_API_KEY', None)\n"
        "dst.write_text(json.dumps(data), encoding='utf-8')\n"
        "PY\n"
        "else\n"
        "cat >/tmp/codex-secrets/auth.json <<EOF\n"
        "{\n"
        f'  "{api_key_env_var}": "${{{api_key_env_var}}}"\n'
        "}\n"
        "EOF\n"
        "fi\n"
        'ln -sf /tmp/codex-secrets/auth.json "$CODEX_HOME/auth.json"'
    )


def build_codex_agent_env(
    *,
    codex_home: str,
    openai_api_key: str | None = None,
    openai_base_url: str | None = None,
) -> dict[str, str]:
    env = {"CODEX_HOME": codex_home}
    if openai_api_key:
        env["OPENAI_API_KEY"] = openai_api_key
    if openai_base_url:
        env["OPENAI_BASE_URL"] = openai_base_url
    return env


def patch_harbor_codex_auth_bridge() -> None:
    from harbor.agents.installed.base import ExecInput
    from harbor.agents.installed.codex import Codex
    from harbor.models.trial.paths import EnvironmentPaths

    if getattr(Codex.create_run_agent_commands, "_sip_bridge_patched", False):
        return

    def patched_create_run_agent_commands(self: Any, instruction: str) -> list[ExecInput]:
        escaped_instruction = shlex.quote(instruction)

        if not self.model_name:
            raise ValueError("Model name is required")

        model = self.model_name.split("/")[-1]
        env = build_codex_agent_env(
            codex_home=EnvironmentPaths.agent_dir.as_posix(),
            openai_api_key=os.environ.get("OPENAI_API_KEY") or None,
            openai_base_url=os.environ.get("OPENAI_BASE_URL") or None,
        )

        reasoning_effort = self._reasoning_effort
        reasoning_flag = f"-c model_reasoning_effort={reasoning_effort} " if reasoning_effort else ""
        auth_source = os.environ.get("SIP_HARBOR_CODEX_AUTH_SOURCE")
        setup_command = build_codex_auth_setup_command(auth_source=auth_source)

        mcp_command = self._build_register_mcp_servers_command()
        if mcp_command:
            setup_command += f"\n{mcp_command}"

        return [
            ExecInput(
                command=setup_command,
                env=env,
            ),
            ExecInput(
                command=(
                    "trap 'rm -rf /tmp/codex-secrets \"$CODEX_HOME/auth.json\"' EXIT TERM INT; "
                    ". ~/.nvm/nvm.sh; "
                    "codex exec "
                    "--dangerously-bypass-approvals-and-sandbox "
                    "--skip-git-repo-check "
                    f"--model {model} "
                    "--json "
                    "--enable unified_exec "
                    f"{reasoning_flag}"
                    "-- "
                    f"{escaped_instruction} "
                    f'2>&1 </dev/null | stdbuf -oL tee {EnvironmentPaths.agent_dir / self._OUTPUT_FILENAME}'
                ),
                env=env,
            ),
        ]

    patched_create_run_agent_commands._sip_bridge_patched = True  # type: ignore[attr-defined]
    Codex.create_run_agent_commands = patched_create_run_agent_commands
