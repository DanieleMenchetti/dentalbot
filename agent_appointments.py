import os
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path("config/.keychain"))


LLM = "gemini-2.5-flash"


async def main():
    llm = ChatGoogleGenerativeAI(
        model=LLM,
        google_api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
    )

    client = MultiServerMCPClient(
        {
            "google-calendar": {
                "command": "npx.cmd",
                "args": ["@cocal/google-calendar-mcp"],
                "env": {
                    **os.environ,
                    "GOOGLE_OAUTH_CREDENTIALS": os.getenv("GOOGLE_OAUTH_CREDENTIALS", ""),
                },
                "transport": "stdio",
            }
        }
    )

    calendar_tools = await client.get_tools()
    print(f"Tool caricati: {[t.name for t in calendar_tools]}")

    agent = create_react_agent(
        model=llm,
        tools=calendar_tools,
    )

    system_message = SystemMessage(content="""
    You are an assistant at a dental office called Your Smile.
    You take care of managing appointments.
                                   
    Always use Google Calendar tools to handle appointments requests.
                                   
    
    """)

    while True:
        user_input = input("\nUser: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        response = await agent.ainvoke({
            "messages": [system_message] + [user_input]
        })

        assistant_reply = response["messages"][-1].content


        if isinstance(assistant_reply, list):
            text = "".join(
                part.get("text", "") for part in assistant_reply if isinstance(part, dict)
            )
        else:
            text = assistant_reply

        print(f"\nDentalbot: {text}\n")


if __name__ == "__main__":
    asyncio.run(main())