import logging
from typing import Optional
from langfuse import Langfuse as LangfuseSDK

logger = logging.getLogger(__name__)


class LangfuseClient:
    def __init__(self, public_key: str, secret_key: str, host: str):
        if not public_key or not secret_key:
            logger.warning("[Langfuse] 認証情報がありません")
            return
        
        try:
            self._client = LangfuseSDK(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            logger.info(f"[Langfuse] クライアントを初期化しました: {host}")
        except Exception as e:
            logger.error(f"[Langfuse] 初期化エラー: {e}")
    
    def get_prompt(self, name: str, fallback: str, label: str = "production") -> str:
        try:
            # 毎回最新のプロンプトを取得（キャッシュを使わない）
            logger.debug(f"[Langfuse] プロンプト '{name}' を取得中...")
            prompt = self._client.get_prompt(name=name, label=label, cache_ttl_seconds=0)
            
            if prompt:
                compiled = prompt.compile()
                logger.debug(f"[Langfuse] プロンプト '{name}' 取得成功")
                return compiled
            else:
                logger.debug(f"[Langfuse] プロンプト '{name}' が見つかりません")
                
        except Exception as e:
            logger.debug(f"[Langfuse] プロンプト取得エラー ({name}): {e}")
        
        return fallback
