"""agent-sandbox terminal backend for Hermes: a thin adapter over the self-hosted-agent-sandbox core.

Sandbox lifecycle, environment and file sync, code pull-back and host-command routing all live in
the core library (vendored under ``_vendor/``; source: github.com/xiaoyaner0201/self-hosted-agent-sandbox).
This module only maps Hermes's BaseEnvironment contract onto it:

* one Sandbox per Hermes task id, kept between turns, released at session close / idle reap;
* Hermes's session snapshot and cwd tracking run inside the sandbox (``_run_bash``), with the host
  environment sourced after the snapshot so current values win;
* the read-only copy of ``$HERMES_HOME/skills`` is seeded into the sandbox once at start.
"""
from __future__ import annotations

from pathlib import Path

from tools.environments.base import BaseEnvironment

from ._vendor.agent_sandbox.core import Sandbox, _popen_bash, bash_argv


def _skills_seed() -> tuple:
    try:
        from hermes_constants import get_hermes_home
        return ((Path(get_hermes_home()) / "skills", ".hermes/skills"),)
    except Exception:
        return ()


class AgentSandboxEnvironment(BaseEnvironment):
    """One SandboxClaim per Hermes task; persistent mode reuses the claim by task label."""

    _stdin_mode = "pipe"

    def __init__(self, *, cwd: str, timeout: int, task_id: str = "default",
                 container_config: dict | None = None, **_):
        # Own key on purpose (agent_sandbox_persistent): Hermes fills the generic
        # container_persistent with True by default, which made every session claim survive teardown.
        self.sbx = Sandbox(cwd=cwd, timeout=timeout, session=task_id, config=container_config, app="hermes",
                           seed_dirs=_skills_seed(), extra_env_skip=("TERMINAL_ENV",))
        super().__init__(cwd=self.sbx.cwd, timeout=timeout)
        # Survive between turns of a session; removed at session close or by the idle reaper.
        self._session_scoped = True
        self.init_session()

    # ---- BaseEnvironment contract -----------------------------------------
    def _before_execute(self) -> None:
        self.sbx.before_command()

    def _wrap_command(self, command: str, cwd: str) -> str:
        # Source the host env AFTER the session snapshot so current values always win.
        return super()._wrap_command(self.sbx.env_prefix() + command, cwd)

    def execute(self, command: str, cwd: str = "", **kw) -> dict:
        def _in_sandbox(c: str, d: str, t: int) -> dict:  # Hermes's own flow: snapshot, cwd markers, ...
            return BaseEnvironment.execute(self, c, d, **{**kw, "timeout": t})
        return self.sbx.execute(command, cwd or self.cwd, timeout=kw.get("timeout"), run_in_sandbox=_in_sandbox)

    def _run_bash(self, cmd_string: str, *, login: bool = False, timeout: int = 120,
                  stdin_data: str | None = None):
        return _popen_bash(self.sbx.exec_argv(*bash_argv(cmd_string, login), stdin=stdin_data is not None), stdin_data)

    def cleanup(self, *, force_remove: bool = False):
        self.sbx.close(force_remove=force_remove)
