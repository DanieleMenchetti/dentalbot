import os
import json
from dotenv import load_dotenv
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

load_dotenv(dotenv_path=Path("config/.keychain"))


class AgentOrchestrator:
    def __init__(self, specialized_agents=[]):
        self.llm_model = "gemini-2.5-flash"
        self.agent = None
        self.specialized_agents = specialized_agents
        self.system_message = None

    async def initialize(self):
        chat = ChatGoogleGenerativeAI(
            model=self.llm_model,
            google_api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
        )
        self.agent = create_react_agent(
            model=chat,
            tools=[]
        )

        descriptions = []
        for agent in self.specialized_agents:
            descriptions.append(f"- {agent.name}: specialized in {agent.verbose_abilities}")
        available_agents = "\n".join(descriptions)
        self.system_message = SystemMessage(
            content=f"""You are an orchestrator that decides which specialized agents should handle a user request.
            Available agents:
            {available_agents}

            Analyze the user request, decide which agents should be called and give to it only the necessary information for that agent to perform its task.
            Do not include any other text or explanation.
            Respond ONLY with a valid JSON object where each key is "<agent_name>" and the string containing the request.

            If an agent is not needed, set its value to False.

            Example format:
            {{"agent_a": "get available treatments", "agent_b": "find telephone number of the clinic"}}

            Do not include any other text or explanation.""")

    async def run(self, messages: []) -> dict:
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

        # Clean and parse JSON
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.strip("```").strip()
            if text.startswith("json"):
                text = text[4:].strip()
        
        try:
            decisions = json.loads(text)
            
            # Ensure all agents have a decision key
            for agent in self.specialized_agents:
                key = agent.name
                if key not in decisions:
                    decisions[key] = False
            
            return decisions
            
        except json.JSONDecodeError as e:
            print(f"Error parsing orchestrator JSON response: {e}")
            print(f"Raw response: {text}")
            # Fallback: return all agents as false
            return {agent.name: False for agent in self.specialized_agents}