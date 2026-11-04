"""Hermes directory-plugin entry point: registers the ``agent_sandbox`` terminal backend."""
from .provider import AgentSandboxProvider


def register(ctx):
    ctx.register_terminal_environment_provider(AgentSandboxProvider())
