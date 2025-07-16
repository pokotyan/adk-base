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

import datetime
import os
from zoneinfo import ZoneInfo

import google.auth
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash",
    instruction="""
    You are a diligent and exhaustive researcher. Your task is to perform comprehensive web searches and synthesize the results.
    Use the 'google_search' tool to find relevant information and provide a detailed, well-organized summary of your findings.
    Always search for the most current and relevant information available.
    """,
    tools=[google_search],
)

# search_agentをツールとしてラップ
# TODO ツールである理由がないので、sub agentとして動かしたい
search_tool = AgentTool(search_agent)

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="""You are a helpful AI assistant designed to provide accurate and useful information. 
    You can provide weather information and current time for cities using your built-in tools.
    
    For research tasks or when you need to search for information online, use the search_agent tool.
    This tool will perform web searches and provide you with comprehensive information on any topic.
    """,
    tools=[get_weather, get_current_time, search_tool],
)
