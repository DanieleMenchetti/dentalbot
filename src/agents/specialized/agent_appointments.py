from src.agents.specialized.specialized_agent import SpecializedAgent
import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

load_dotenv(dotenv_path=Path("config/.keychain"))


class AgentAppointments(SpecializedAgent):
    def __init__(self):
        super().__init__("agent_appointments", "managing appointment requests")
        self.llm_model = "gemini-2.5-flash"
        self.agent = None
        self.system_message = SystemMessage(content="""
        You are an assistant at a dental office called Your Smile.
        You take care of managing appointments.

        Always use Google Calendar tools to handle appointments requests.
        """)

    async def initialize(self):
        """Initialize the agent with async operations."""
        chat = ChatGoogleGenerativeAI(
            model=self.llm_model,
            google_api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
        )
        mcp_client = MultiServerMCPClient(
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
        calendar_tools = await mcp_client.get_tools()
        self.agent = create_react_agent(
            model=chat,
            tools=calendar_tools,
        )

    async def run(self, messages: []) -> str:
        response = await self.agent.ainvoke({
            "messages": [self.system_message] + messages
        })

        content = response["messages"][-1].content

        if isinstance(content, list):
            text = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        else:
            text = content

        return text