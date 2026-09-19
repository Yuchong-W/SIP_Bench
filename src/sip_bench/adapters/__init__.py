from importlib import import_module
from typing import Any

from sip_bench.adapters.base import BenchmarkAdapter, SplitManifest, TaskDescriptor
from sip_bench.adapters.skillsbench import SkillsBenchAdapter
from sip_bench.adapters.mock_bench import MockBenchAdapter
from sip_bench.adapters.tau_bench import TauBenchAdapter

def _load_evoagentbench_adapter() -> type[BenchmarkAdapter] | None:
    """Load the optional adapter without masking its own missing dependencies."""
    module_name = "sip_bench.adapters.evoagentbench"
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise
        return None
    return module.EvoAgentBenchAdapter


EvoAgentBenchAdapter = _load_evoagentbench_adapter()
EVOAGENTBENCH_AVAILABLE = EvoAgentBenchAdapter is not None
from sip_bench.adapters.medical import MedicalAdapter


def require_evoagentbench_adapter() -> type[BenchmarkAdapter]:
    """Return the optional adapter or raise an actionable installation error."""
    if EvoAgentBenchAdapter is None:
        raise RuntimeError(
            "EvoAgentBench support is not installed in this SIP-Bench release. "
            "Install the optional adapter package before using evoagentbench suites."
        )
    return EvoAgentBenchAdapter

def _public_adapter_exports(evoagentbench_available: bool) -> list[str]:
    names = [
        "BenchmarkAdapter",
        "SplitManifest",
        "TaskDescriptor",
        "MockBenchAdapter",
        "SkillsBenchAdapter",
        "TauBenchAdapter",
        "MedicalAdapter",
        "EVOAGENTBENCH_AVAILABLE",
        "require_evoagentbench_adapter",
    ]
    if evoagentbench_available:
        names.append("EvoAgentBenchAdapter")
    return names


__all__ = _public_adapter_exports(EVOAGENTBENCH_AVAILABLE)
