@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "UV_CACHE_DIR=%SCRIPT_DIR%..\.uv-cache"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "NO_COLOR=1"
set "DOCKER_BUILDKIT=0"
set "COMPOSE_DOCKER_CLI_BUILD=0"
set "BUILDKIT_PROGRESS=plain"
set "SIP_HARBOR_CODEX_AUTH_SOURCE=%USERPROFILE%\.codex\auth.json"
if defined PYTHONPATH (
  set "PYTHONPATH=%SCRIPT_DIR%..\tools\harbor_codex_bridge;%SCRIPT_DIR%..\src;%PYTHONPATH%"
) else (
  set "PYTHONPATH=%SCRIPT_DIR%..\tools\harbor_codex_bridge;%SCRIPT_DIR%..\src"
)
uvx --python 3.12 harbor %*
