import os
import json
from dotenv import load_dotenv
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

load_dotenv(dotenv_path=Path("config/.keychain"))

class AgentSummarize:
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

    async def run(self, agent_responses: dict) -> dict:

        responses_text = ""
        i=1
        for _, response in agent_responses.items():
            responses_text += f"Sentence {i}: {response}\n"
            i+=1

        system_message = SystemMessage(
            content=f"""You are an assistant that helps summarize sentences.
            Sentences:
            {agent_responses}

            Do not include any other text or explanation.""")

        response = await self.agent.ainvoke({
            "messages": [system_message] + ["Summarize the sentences above. Do not miss any information. Use the same language as the sentences."]
        })

        content = response["messages"][-1].content
        return content
