# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from .agent import root_agent

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .envファイルを読み込み
load_dotenv()

# 環境変数の取得
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN と SLACK_APP_TOKEN を環境変数に設定してください")

# Slack アプリの初期化
app = App(token=SLACK_BOT_TOKEN)

# ADK Runnerとセッションサービスの初期化
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="adk-slack-bot",
    session_service=session_service
)

# ユーザーごとのセッション管理
user_sessions: Dict[str, str] = {}

# ボットが開始したスレッドを追跡
bot_threads: set = set()


async def get_or_create_session(user_id: str) -> str:
    """ユーザーのセッションIDを取得または作成"""
    if user_id not in user_sessions:
        session_id = f"slack_{user_id}"
        await session_service.create_session(
            app_name="adk-slack-bot",
            user_id=user_id,
            session_id=session_id
        )
        user_sessions[user_id] = session_id
        logger.info(f"新しいセッションを作成: {session_id}")
    
    return user_sessions[user_id]


# シンプルな同期処理関数
async def process_agent_message(user_id: str, message: str) -> str:
    """エージェントにメッセージを送信して応答を取得（非ストリーミング）"""
    try:
        session_id = await get_or_create_session(user_id)
        
        # エージェントを実行
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=message)]
            ),
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        
        return response_text or "申し訳ございませんが、応答を生成できませんでした。"
    
    except Exception as e:
        logger.error(f"エージェント処理エラー: {e}")
        return f"エラーが発生しました: {str(e)}"


@app.message("")
def handle_message(message: Dict[str, Any], say: Any) -> None:
    """全てのメッセージを処理"""
    # message_deletedなどのサブタイプは無視
    if message.get("subtype"):
        return
        
    user_id = message["user"]
    text = message["text"]
    channel_type = message.get("channel_type", "unknown")
    
    logger.info(f"[DEBUG] メッセージ受信 - ユーザー: {user_id}, テキスト: {text}")
    logger.info(f"[DEBUG] メッセージタイプ: {channel_type}")
    
    # ボットのユーザーIDを取得
    bot_user_id = app.client.auth_test()["user_id"]
    logger.info(f"[DEBUG] Bot User ID: {bot_user_id}")
    
    # DMの場合は直接反応
    if channel_type == "im":
        logger.info(f"[DEBUG] DMメッセージを処理します")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(process_agent_message(user_id, text))
            say(response)
        finally:
            loop.close()
    
    # スレッド内のメッセージをチェック
    elif message.get("thread_ts"):
        thread_ts = message["thread_ts"]
        logger.info(f"[DEBUG] スレッドメッセージ検出: {thread_ts}")
        
        # ボットが開始したスレッドかチェック
        if thread_ts in bot_threads:
            logger.info(f"[DEBUG] ボットのスレッド内メッセージを処理します")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(process_agent_message(user_id, text))
                # 同じスレッドで返信
                say(text=response, thread_ts=thread_ts)
            finally:
                loop.close()
    
    # チャンネルでのメンションは@app.event("app_mention")で処理するのでここでは何もしない
    elif f"<@{bot_user_id}>" in text:
        logger.info(f"[DEBUG] チャンネルでのメンション検出、app_mentionイベントで処理されます")
        pass


@app.event("app_mention")
def handle_app_mention(event: Dict[str, Any], say: Any) -> None:
    """アプリへの言及を処理"""
    user_id = event["user"]
    text = event["text"]
    event_ts = event["ts"]
    
    logger.info(f"[DEBUG] アプリ言及受信 - ユーザー: {user_id}, テキスト: {text}")
    logger.info(f"[DEBUG] イベント詳細: {event}")
    
    # 非同期処理を同期的に実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        response = loop.run_until_complete(process_agent_message(user_id, text))
        logger.info(f"[DEBUG] エージェント応答: {response}")
        
        # スレッドで返信
        say(text=response, thread_ts=event_ts)
        
        # このスレッドをボットのスレッドとして追跡
        bot_threads.add(event_ts)
        logger.info(f"[DEBUG] スレッド {event_ts} をボットスレッドとして追加")
        
    finally:
        loop.close()


@app.command("/weather")
def handle_weather_command(ack: Any, command: Dict[str, Any], respond: Any) -> None:
    """天気コマンドを処理"""
    ack()
    user_id = command["user_id"]
    text = command["text"] or "サンフランシスコ"
    
    logger.info(f"天気コマンド - ユーザー: {user_id}, 場所: {text}")
    
    # 非同期処理を同期的に実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        weather_query = f"{text}の天気を教えて"
        response = loop.run_until_complete(process_agent_message(user_id, weather_query))
        respond(response)
    finally:
        loop.close()


@app.command("/time")
def handle_time_command(ack: Any, command: Dict[str, Any], respond: Any) -> None:
    """時間コマンドを処理"""
    ack()
    user_id = command["user_id"]
    text = command["text"] or "サンフランシスコ"
    
    logger.info(f"時間コマンド - ユーザー: {user_id}, 場所: {text}")
    
    # 非同期処理を同期的に実行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        time_query = f"{text}の現在時刻を教えて"
        response = loop.run_until_complete(process_agent_message(user_id, time_query))
        respond(response)
    finally:
        loop.close()


def main() -> None:
    """Slack ボットのメイン関数"""
    logger.info("Slack ボットを開始しています...")
    
    # Socket Mode ハンドラーでアプリを実行
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()


if __name__ == "__main__":
    main()