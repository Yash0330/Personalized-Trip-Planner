from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.agents import (
    itinerary_builder, 
    budget_agent, 
    alert_agent, 
    suggestion_agent, 
    flight_search_agent, 
    packing_agent,
    event_agent,
    mapping_agent,
    summary_node
)

# Graph Definition
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("builder", itinerary_builder)
workflow.add_node("budget", budget_agent)
workflow.add_node("alert", alert_agent)
workflow.add_node("suggestion", suggestion_agent)
workflow.add_node("flights", flight_search_agent)
workflow.add_node("packing", packing_agent)
workflow.add_node("events", event_agent)
workflow.add_node("mapping", mapping_agent)
workflow.add_node("summary", summary_node)

# Set Entry Point
workflow.set_entry_point("builder")

# Add Edges (Fan-out from builder)
workflow.add_edge("builder", "budget")
workflow.add_edge("builder", "alert")
workflow.add_edge("builder", "suggestion")
workflow.add_edge("builder", "flights")
workflow.add_edge("builder", "packing")
workflow.add_edge("builder", "events")
workflow.add_edge("builder", "mapping")

# Fan-in to summary
workflow.add_edge("budget", "summary")
workflow.add_edge("alert", "summary")
workflow.add_edge("suggestion", "summary")
workflow.add_edge("flights", "summary")
workflow.add_edge("packing", "summary")
workflow.add_edge("events", "summary")
workflow.add_edge("mapping", "summary")

# Finish
workflow.add_edge("summary", END)

# Compile
app = workflow.compile()
