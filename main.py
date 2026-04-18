import asyncio
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from src.agents.agent_orchestrator import AgentOrchestrator
from src.agents.agent_summarize import AgentSummarize
from src.agents.specialized.agent_info import AgentInfo
from src.agents.specialized.agent_appointments import AgentAppointments


class WorkflowState(TypedDict):
    messages: list
    agent_calls: dict
    agent_responses: dict

info_agent = AgentInfo()
appointments_agent = AgentAppointments()
all_specialized_agent = [info_agent, appointments_agent]

orchestrator = AgentOrchestrator(all_specialized_agent)
summarizer = AgentSummarize()


async def call_orchestrator_agent(state: WorkflowState) -> Literal["execute_agents", "end"]:
    decisions = await orchestrator.run(state["messages"])
    return {
        "agent_calls": decisions
    }


async def call_specialized_agents(state: WorkflowState):
    """Execute all agents that should be executed in parallel."""
    agent_calls = state.get("agent_calls", {})
    messages = state.get("messages", [])
    
    # Execute agents in parallel
    tasks = []
    for agent in all_specialized_agent:
        if agent.name in agent_calls and isinstance(agent_calls[agent.name], str) and agent_calls[agent.name]:
            task = agent.run([agent_calls[agent.name]])
            tasks.append((agent.name, task))

    print("Tasks:", tasks)
    
    # Gather results
    results = await asyncio.gather(*[task for _, task in tasks])
    
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

def check_summarize_node(state: WorkflowState) -> bool:
    return check_summarize(state.get("agent_responses", {}))

def check_summarize(agent_responses: dict) -> bool:
    return len(agent_responses) > 1

async def call_summarize_agent(state: WorkflowState):
    summarize = await summarizer.run(state["agent_responses"])
    return {
        "messages": state["messages"] + [summarize]
    }

async def main():   
    await info_agent.initialize()
    await appointments_agent.initialize()
    await orchestrator.initialize()
    await summarizer.initialize()
    
    # Build the workflow graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("call_orchestrator_agent", call_orchestrator_agent)
    workflow.add_node("call_specialized_agents", call_specialized_agents)
    workflow.add_node("check_summarize_node", check_summarize_node)
    workflow.add_node("call_summarize_agent", call_summarize_agent)
    
    # Set entry point
    workflow.set_entry_point("call_orchestrator_agent")
    
    # Add edges
    workflow.add_edge("call_orchestrator_agent", "call_specialized_agents")
    workflow.add_conditional_edges(
        "call_specialized_agents",
        check_summarize_node,
        {
            True: "call_summarize_agent",
            False: END
        }
    )
    workflow.add_edge("call_summarize_agent", END)
    
    # Compile the graph
    app = workflow.compile()
    
    print("Dentalbot - Type your questions or 'exit' to quit\n")
    
    while True:
        user_input = input("\nUser: ")
        
        if user_input.lower() in ["exit", "quit"]:
            break
        
        # Initialize state
        state = {
            "messages": [user_input],
            "agent_calls": {},
            "agent_responses": {},
            "response": ""
        }
        
        # Run the workflow
        result = await app.ainvoke(state)
        
        # Print the summary
        print(f"\nDentalbot: {result}\n")


if __name__ == "__main__":
    asyncio.run(main())
