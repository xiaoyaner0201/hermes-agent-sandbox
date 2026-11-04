from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Optional

from agent.terminal_env_provider import TerminalEnvironmentProvider


def _kubeconfig(cc: dict | None = None) -> Path:
    return Path((cc or {}).get("agent_sandbox_kubeconfig") or os.environ.get("AGENT_SANDBOX_KUBECONFIG")
                or Path.home() / ".kube" / "agent-sandbox.yaml")


class AgentSandboxProvider(TerminalEnvironmentProvider):
    name = "agent_sandbox"
    display_name = "agent-sandbox (Kubernetes)"
    is_remote = True
    is_container = True
    session_isolated_when_nonpersistent = True

    @property
    def cache_path_base(self) -> Optional[str]:
        return None  # cache files are NOT synced into the sandbox

    @property
    def strip_env_keys(self) -> frozenset:
        return frozenset({"AGENT_SANDBOX_KUBECONFIG", "KUBECONFIG"})

    @property
    def env_description(self) -> str:
        return "an isolated agent-sandbox pod (Linux, gVisor)"

    def is_available(self) -> bool:
        return bool(shutil.which(os.environ.get("AGENT_SANDBOX_KUBECTL", "kubectl"))) and _kubeconfig().is_file()

    def check_requirements(self, config: dict[str, Any]) -> bool:
        return self.is_available()

    def create_environment(self, *, cwd: str, timeout: int, task_id: str = "default", image: Optional[str] = None,
                           container_config: Optional[dict[str, Any]] = None, **kwargs: Any):
        from .environment import AgentSandboxEnvironment
        return AgentSandboxEnvironment(cwd=cwd, timeout=timeout, task_id=task_id, container_config=container_config)
