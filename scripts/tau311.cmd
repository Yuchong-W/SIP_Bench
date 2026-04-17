@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
set "LOCAL_DEPS=%ROOT_DIR%\.pydeps311"
set "TAU_REPO=%ROOT_DIR%\benchmarks\tau-bench"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

if defined PYTHONPATH (
  set "PYTHONPATH=%LOCAL_DEPS%;%TAU_REPO%;%PYTHONPATH%"
) else (
  set "PYTHONPATH=%LOCAL_DEPS%;%TAU_REPO%"
)

py -3.11 %*
