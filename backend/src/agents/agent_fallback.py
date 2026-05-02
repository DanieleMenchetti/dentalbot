import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

load_dotenv(dotenv_path=Path("config/.keychain"))

class AgentFallback:
    def __init__(self, specialized_agents=[]):
        self.llm_model = "gemini-2.5-flash"
        self.agent = None

    async def initialize(self):
        chat = ChatGoogleGenerativeAI(
            model=self.llm_model,
            google_api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
        )
        self.agent = create_react_agent(
            model=chat,
            tools=[]
        )

    async def run(self, messages: []) -> dict:
        system_message = SystemMessage(
            content=f"""You are an assistant at a dental office called Your Smile.
            Be helpful and friendly with our guests.""")

        response = await self.agent.ainvoke({
            "messages": [system_message] + messages
        })

        content = response["messages"][-1].content
        return content
