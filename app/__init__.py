from .agent import create_agents
from .utils.langfuse import LangfuseClient
from . import config

# Langfuseクライアントを作成
langfuse_client = LangfuseClient(
    public_key=config.LANGFUSE_PUBLIC_KEY,
    secret_key=config.LANGFUSE_SECRET_KEY,
    host=config.LANGFUSE_HOST
)

# Playground と Agent Engine用にroot_agentをエクスポート
root_agent = create_agents(langfuse_client)

__all__ = ["root_agent"]
