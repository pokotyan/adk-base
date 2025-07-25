from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

from .tools import get_weather, get_current_time

def create_agents(langfuse_client):
    
    search_instruction, search_prompt_obj = langfuse_client.get_prompt(
        name="search_agent_instruction",
        fallback="""
        You are a diligent and exhaustive researcher. Your task is to perform comprehensive web searches and synthesize the results.
        Use the 'google_search' tool to find relevant information and provide a detailed, well-organized summary of your findings.
        Always search for the most current and relevant information available.
        """
    )    
    search_agent = Agent(
        name="search_agent",
        model="gemini-2.5-flash",
        instruction=search_instruction,
        tools=[google_search],
    )
    
    root_instruction, root_prompt_obj = langfuse_client.get_prompt(
        name="root_agent_instruction",
        fallback="""You are a helpful AI assistant designed to provide accurate and useful information. 
        You can provide weather information and current time for cities using your built-in tools.
        
        For research tasks or when you need to search for information online, use the search_agent tool.
        This tool will perform web searches and provide you with comprehensive information on any topic.
        """
    )    
    root_agent = Agent(
        name="root_agent",
        model="gemini-2.5-flash",
        instruction=root_instruction,
        # TODO search_agentはツールではなく、sub agentとして動かしたい
        tools=[get_weather, get_current_time, AgentTool(search_agent)],
    )
    
    # エージェントにプロンプトオブジェクトを添付（後でトレーシングで使用）
    root_agent._langfuse_prompts = {
        "root": root_prompt_obj,
        "search": search_prompt_obj
    }
    
    return root_agent
