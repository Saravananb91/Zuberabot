import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from zuberabot.providers.openai_provider import OpenAIProvider

async def main():
    print("Testing OpenAIProvider with tools...")
    provider = OpenAIProvider(default_model="ollama/qwen2.5:3b")
    
    messages = [
        {"role": "user", "content": "What is the gold rate in India today?"}
    ]
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    }
                }
            }
        }
    ]
    
    try:
        response = await provider.chat(messages=messages, tools=tools)
        print(f"\nResponse Content:\n{response.content}")
        print(f"\nTool Calls:\n{response.tool_calls}")
        print(f"\nFinish Reason: {response.finish_reason}")
    except Exception as e:
        print(f"\nCaught Exception: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
