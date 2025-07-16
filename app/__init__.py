from .agent import create_agents

# Playground と Agent Engine用にroot_agentをエクスポート
root_agent = create_agents()

__all__ = ["root_agent"]
