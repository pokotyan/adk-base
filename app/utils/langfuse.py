import logging
from typing import Optional, Tuple, Any
from langfuse import Langfuse as LangfuseSDK
from langfuse.decorators import langfuse_context, observe

logger = logging.getLogger(__name__)


class LangfuseClient:
    def __init__(self, public_key: str, secret_key: str, host: str):
        self._client = None
        
        if not public_key or not secret_key:
            logger.warning("[Langfuse] 認証情報がありません")
            return
        
        try:
            self._client = LangfuseSDK(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            # デコレーター用にグローバル設定も初期化
            langfuse_context.configure(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
            logger.info(f"[Langfuse] クライアントを初期化しました: {host}")
        except Exception as e:
            logger.error(f"[Langfuse] 初期化エラー: {e}")
    
    def get_prompt(self, name: str, fallback: str, label: str = "production") -> Tuple[str, Optional[Any]]:
        if not self._client:
            return fallback, None
            
        try:
            # プロンプトキャッシュをクリア（存在する場合）これがないと、なぜかプロンプトが動的に切り替わらない
            if hasattr(self._client, 'prompt_cache') and hasattr(self._client.prompt_cache, 'clear'):
                self._client.prompt_cache.clear()
            
            # 毎回最新のプロンプトを取得（キャッシュを使わない）
            prompt = self._client.get_prompt(name=name, label=label, cache_ttl_seconds=0)            
            if prompt:
                compiled = prompt.compile()
                return compiled, prompt
            else:
                logger.debug(f"[Langfuse] プロンプト '{name}' が見つかりません")
                
        except Exception as e:
            logger.debug(f"[Langfuse] プロンプト取得エラー ({name}): {e}")
        
        return fallback, None
