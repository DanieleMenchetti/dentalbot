import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, TypedDict, Literal
from langgraph.graph import StateGraph, END
from src.agents.agent_orchestrator import AgentOrchestrator
from src.agents.agent_summarize import AgentSummarize
from src.agents.agent_fallback import AgentFallback
from src.agents.specialized.agent_info import AgentInfo
from src.agents.specialized.agent_appointments import AgentAppointments

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class CreateConversationRequest(BaseModel):
    name: str

class AddMessageRequest(BaseModel):
    name: str
    message: str

class Conversation(BaseModel):
    name: str
    messages: List[str]

class WorkflowState(TypedDict):
    messages: list
    agent_calls: dict
    agent_responses: dict
    error: str



# Functions
async def call_orchestrator_agent(state: WorkflowState):
    decisions = await orchestrator.run(state["messages"])
    print("Orchestrator - Decisions:", decisions)
    return {
        "agent_calls": decisions
    }
    
async def call_fallback_agent(state: WorkflowState):
    response = await fallback.run(state["messages"])
    print("Fallback - Response:", response)
    return {
        "messages": state["messages"] + [response],
        "agent_responses": {
            "agent_fallback": response
        }
    }

async def call_specialized_agents(state: WorkflowState):
    """Execute all agents that should be executed in parallel."""
    agent_calls = state.get("agent_calls", {})
    messages = state.get("messages", [])
    print("Specialized Agents - Agent Calls:", agent_calls)
    

    # Execute agents in parallel
    try:
        tasks = []
        for agent in all_specialized_agent:
            if agent.name in agent_calls and isinstance(agent_calls[agent.name], str) and agent_calls[agent.name]:
                print("Specialized Agents - Running agent:", agent.name)
                task = agent.run([agent_calls[agent.name]])
                tasks.append((agent.name, task))

        # Gather results
        results = await asyncio.gather(*[task for _, task in tasks])
    except Exception as e:
        print("Specialized Agents - Error executing agents:", e)
        return {
            "error": f"Error executing agents: {e}"
        }

    # Build agent_responses dict
    agent_responses = {}
    for (agent_name, _), response in zip(tasks, results):
        agent_responses[agent_name] = response

    print("Specialized Agents - Agent Responses:", agent_responses)

    if check_summarize(agent_responses):
        return {
            "agent_responses": agent_responses
        }
    else:
        return {
            "agent_responses": agent_responses,
            "messages": messages + [response for response in agent_responses.values()]
        }

def check_summarize(agent_responses: dict) -> bool:
    return len(agent_responses) > 1

def check_error_and_summarize(state: WorkflowState) -> Literal["handle_error", "call_summarize_agent", "end"]:
    if state.get("error", "") != "":
        return "handle_error"
    if check_summarize(state.get("agent_responses", {})):
        return "call_summarize_agent"
    return "end"

def check_fallback_node(state: WorkflowState) -> bool:
    agent_calls = state.get("agent_calls", {})
    for agent in all_specialized_agent:
        if agent.name in agent_calls and isinstance(agent_calls[agent.name], str) and agent_calls[agent.name]:
            return False
    return True

async def call_summarize_agent(state: WorkflowState):
    summarize = await summarizer.run(state["agent_responses"])
    print("Summarize - Response:", summarize)
    return {
        "messages": state["messages"] + [summarize]
    }

async def handle_error(state: WorkflowState):
    response = await fallback.run([state["error"]])
    return {
        "messages": state["messages"] + [response],
        "agent_responses": {
            "agent_fallback": response
        }
    }




# Data structures
info_agent = AgentInfo()
appointments_agent = AgentAppointments()
all_specialized_agent = [info_agent, appointments_agent]

orchestrator = AgentOrchestrator(all_specialized_agent)
summarizer = AgentSummarize()
fallback = AgentFallback()
conversations = {}


# App startup
@app.on_event("startup")
async def startup_event():
    await info_agent.initialize()
    await appointments_agent.initialize()
    await orchestrator.initialize()
    await summarizer.initialize()
    await fallback.initialize()

    # Build the workflow graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("call_orchestrator_agent", call_orchestrator_agent)
    workflow.add_node("call_specialized_agents", call_specialized_agents)
    workflow.add_node("call_summarize_agent", call_summarize_agent)
    workflow.add_node("call_fallback_agent", call_fallback_agent)
    workflow.add_node("handle_error", handle_error)
    
    # Set entry point
    workflow.set_entry_point("call_orchestrator_agent")
    
    # Add edges
    workflow.add_conditional_edges(
        "call_orchestrator_agent",
        check_fallback_node,
        {
            True: "call_fallback_agent",
            False: "call_specialized_agents"
        }
    )
    workflow.add_conditional_edges(
        "call_specialized_agents",
        check_error_and_summarize,
        {
            "handle_error": "handle_error",
            "call_summarize_agent": "call_summarize_agent",
            "end": END
        }
    )
    workflow.add_edge("call_summarize_agent", END)
    workflow.add_edge("handle_error", END)
    
    # Compile the graph
    global app_workflow
    app_workflow = workflow.compile()

    print("Initialization completed!")


# API endpoints
@app.get("/conversations")
def get_conversations():
    return {"conversations": list(conversations.keys())}

@app.post("/conversations")
def create_conversation(req: CreateConversationRequest):
    if req.name in conversations:
        raise HTTPException(status_code=400, detail="Conversation with this name already exists")
    conversations[req.name] = []
    return {"name": req.name}

@app.get("/conversations/{name}")
def get_conversation_messages(name: str):
    if name not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"name": name, "messages": conversations[name]}

@app.post("/conversations/messages")
async def add_message_to_conversation(req: AddMessageRequest):
    if req.name not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Add user message
    conversations[req.name].append(req.message)

    state = {
        "messages": conversations[req.name],
        "agent_calls": {},
        "agent_responses": {},
        "error": ""
    }

    reply = await app_workflow.ainvoke(state)
    final_response = reply.get("messages", [])[-1] if reply.get("messages") else "No response"
    conversations[req.name].append(final_response)

    return {"name": req.name, "reply": final_response}