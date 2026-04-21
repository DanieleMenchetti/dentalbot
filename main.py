import asyncio
from typing import TypedDict, Literal
from langchain_core.prompts import string
from langgraph.graph import StateGraph, END
from src.agents.agent_orchestrator import AgentOrchestrator
from src.agents.agent_summarize import AgentSummarize
from src.agents.agent_fallback import AgentFallback
from src.agents.specialized.agent_info import AgentInfo
from src.agents.specialized.agent_appointments import AgentAppointments
from src.memory.conversation_memory import ConversationMemory


class WorkflowState(TypedDict):
    messages: list
    agent_calls: dict
    agent_responses: dict
    error: str

info_agent = AgentInfo()
appointments_agent = AgentAppointments()
all_specialized_agent = [info_agent, appointments_agent]

orchestrator = AgentOrchestrator(all_specialized_agent)
summarizer = AgentSummarize()
fallback = AgentFallback()
conversation_memory = ConversationMemory()


async def call_orchestrator_agent(state: WorkflowState):
    decisions = await orchestrator.run(state["messages"])
    return {
        "agent_calls": decisions
    }
    
async def call_fallback_agent(state: WorkflowState):
    response = await fallback.run(state["messages"])
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

    # Execute agents in parallel
    try:
        tasks = []
        for agent in all_specialized_agent:
            if agent.name in agent_calls and isinstance(agent_calls[agent.name], str) and agent_calls[agent.name]:
                task = agent.run([agent_calls[agent.name]])
                tasks.append((agent.name, task))

        # Gather results
        results = await asyncio.gather(*[task for _, task in tasks])
    except Exception as e:
        return {
            "error": f"Error executing agents: {e}"
        }

    # Build agent_responses dict
    agent_responses = {}
    for (agent_name, _), response in zip(tasks, results):
        agent_responses[agent_name] = response

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

async def main():   
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
    app = workflow.compile()

    # Print the graph structure
    print(app.get_graph().print_ascii())

    print("Dentalbot - Type your questions or 'exit' to quit\n")
    
    while True:
        user_input = input("\nUser: ")
        
        if user_input.lower() in ["exit", "quit"]:
            break
        
        # Add user message to conversation memory
        conversation_memory.add_message("human", user_input)
        
        # Initialize state with full conversation history + current message
        state = {
            "messages": conversation_memory.get_messages_for_agent(),
            "agent_calls": {},
            "agent_responses": {},
            "error": ""
        }
        
        # Run the workflow
        result = await app.ainvoke(state)

        print("########## Result:", result)
        
        # Get the final response
        final_response = result.get("messages", [])[-1] if result.get("messages") else "No response"
        
        # Add AI response to conversation memory
        conversation_memory.add_message("assistant", final_response)
        
        # Print the summary
        print(f"\nDentalbot: {final_response}\n")


if __name__ == "__main__":
    asyncio.run(main())
