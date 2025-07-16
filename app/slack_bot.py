import asyncio
import logging
from typing import Dict, Any

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from . import config
from .agent import create_agents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(token=config.SLACK_BOT_TOKEN)

session_service = InMemorySessionService()
user_sessions: Dict[str, str] = {}
bot_threads: set = set()


async def get_or_create_session(user_id: str) -> str:
    if user_id not in user_sessions:
        session_id = f"slack_{user_id}"
        await session_service.create_session(
            app_name="adk-slack-bot",
            user_id=user_id,
            session_id=session_id
        )
        user_sessions[user_id] = session_id
    return user_sessions[user_id]


async def process_message(user_id: str, message: str) -> str:
    try:
        logger.info(f"[DEBUG] メッセージ処理開始: {message}")
        # リクエストごとに最新のプロンプトでエージェントを作成。
        # agentsのinstructionは更新することができないため、プロンプトを更新しても反映することができないため
        agent = create_agents()
        logger.info(f"[DEBUG] エージェント作成完了, instruction: {agent.instruction[:100]}...")
        
        runner = Runner(
            agent=agent,
            app_name="adk-slack-bot",
            session_service=session_service
        )
        
        session_id = await get_or_create_session(user_id)
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


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.message("")
def handle_message(message: Dict[str, Any], say: Any) -> None:
    if message.get("subtype"):
        return
    
    user_id = message["user"]
    text = message["text"]
    channel_type = message.get("channel_type", "unknown")
    
    # DM
    if channel_type == "im":
        response = run_async(process_message(user_id, text))
        say(response)
    
    # スレッド
    elif message.get("thread_ts") and message["thread_ts"] in bot_threads:
        response = run_async(process_message(user_id, text))
        say(text=response, thread_ts=message["thread_ts"])


@app.event("app_mention")
def handle_app_mention(event: Dict[str, Any], say: Any) -> None:
    user_id = event["user"]
    text = event["text"]
    event_ts = event["ts"]
    
    response = run_async(process_message(user_id, text))
    say(text=response, thread_ts=event_ts)
    bot_threads.add(event_ts)


@app.command("/weather")
def handle_weather_command(ack: Any, command: Dict[str, Any], respond: Any) -> None:
    ack()
    query = f"{command['text'] or 'サンフランシスコ'}の天気を教えて"
    response = run_async(process_message(command["user_id"], query))
    respond(response)


@app.command("/time")
def handle_time_command(ack: Any, command: Dict[str, Any], respond: Any) -> None:
    ack()
    query = f"{command['text'] or 'サンフランシスコ'}の現在時刻を教えて"
    response = run_async(process_message(command["user_id"], query))
    respond(response)


def main():
    logger.info("Slack ボットを開始しています...")
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    handler.start()


if __name__ == "__main__":
    main()
