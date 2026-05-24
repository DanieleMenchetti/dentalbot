import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import uuid
from src.agents.specialized.specialized_agent import SpecializedAgent

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from langchain.tools import tool

load_dotenv(dotenv_path=Path("config/.keychain"))


@tool
async def urgent_human_escalation(issue: str) -> str:
    """
    Opens an urgent escalation ticket for a human operator.
    Use this tool when the patient has:
    - severe pain
    - bleeding
    - infection
    - swelling
    - trauma
    - emergency situations
    """

    ticket_id = str(uuid.uuid4())[:8]

    print("\n=== HUMAN ESCALATION ===")
    print(f"Ticket ID: {ticket_id}")
    print(f"Timestamp: {datetime.now()}")
    print(f"Issue: {issue}")
    print("========================\n")

    return f"""
    Urgent ticket opened successfully.

    Ticket ID: {ticket_id}

    A human operator from Your Smile will contact the patient as soon as possible.
    """


class AgentEmergency(SpecializedAgent):
    def __init__(self):
        super().__init__("agent_emergency", "managing emergency dental situations")
        self.llm_model = "gemini-2.5-flash"
        self.agent = None

    async def initialize(self):

        chat = ChatGoogleGenerativeAI(
            model=self.llm_model,
            google_api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
        )

        self.agent = create_react_agent(
            model=chat,
            tools=[urgent_human_escalation]
        )

    async def run(self, messages: list):

        system_message = SystemMessage(
            content="""
            You are the emergency dental assistant for Your Smile dental office.

            Your responsibilities:
            - Detect urgent dental situations
            - Reassure the patient
            - Use the urgent_human_escalation tool whenever appropriate

            Urgent situations include:
            - severe pain
            - swelling
            - infection
            - trauma
            - bleeding
            - broken tooth with pain
            - fever related to dental issues

            Always prioritize patient safety.
            """
        )

        response = await self.agent.ainvoke({
            "messages": [system_message] + messages
        })

        return response["messages"][-1].content