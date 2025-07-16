import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


SLACK_BOT_TOKEN = get_env("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = get_env("SLACK_APP_TOKEN")

LANGFUSE_PUBLIC_KEY = get_env("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = get_env("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = get_env("LANGFUSE_HOST", "http://localhost:3000")

GOOGLE_CLOUD_PROJECT = get_env("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = get_env("GOOGLE_CLOUD_LOCATION", "global")
GOOGLE_GENAI_USE_VERTEXAI = get_env("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() == "true"
