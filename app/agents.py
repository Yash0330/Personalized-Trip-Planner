from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from app.state import AgentState
from tavily import TavilyClient
import os

# Initialize LLM
llm = ChatOpenAI(model="gpt-5-mini", temperature=0.7)

def itinerary_builder(state: AgentState):
    """
    Looks at destination, dates, and budget_feedback. 
    Generates a day-by-day itinerary.
    """
    system_message = (
        "You are an expert travel planner. Create a detailed day-by-day itinerary based on the user's destination, "
        "dates, and preferences. Consider any budget feedback provided."
    )
    
    user_content = f"Destination: {state['destination']}\nDates: {state['dates']}\nPreferences: {state.get('preferences', [])}\n"
    if state.get("budget_feedback"):
        user_content += f"Budget Feedback to address: {state['budget_feedback']}"

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_content)
    ]
    
    response = llm.invoke(messages)
    return {"itinerary": response.content}

def budget_agent(state: AgentState):
    """
    Audits the itinerary and checks if it seems expensive.
    If it finds luxury items, it adds a comment to budget_feedback.
    """
    system_message = (
        "You are a strict budget auditor. Review the provided itinerary. "
        "If you find luxury items, expensive activities, or potential overspending, "
        "provide concise feedback to reduce costs. If it looks fine, say 'Budget looks good'."
    )
    
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=f"Itinerary to audit:\n{state.get('itinerary', '')}")
    ]
    
    response = llm.invoke(messages)
    return {"budget_feedback": response.content}

def alert_agent(state: AgentState):
    """
    Mock a weather check. 
    If the destination is 'London' or 'Seattle', add a 'Rain Alert' to the alerts list.
    """
    destination = state.get("destination", "").lower()
    alerts = state.get("alerts", []) or []
    
    if destination in ["london", "seattle"]:
        if "Rain Alert" not in alerts:
            alerts.append("Rain Alert")
            
    return {"alerts": alerts}

def suggestion_agent(state: AgentState):
    """
    Adds 3 'Hidden Gem' tips to the local_tips list based on the destination.
    """
    system_message = (
        "You are a local expert. Provide exactly 3 'Hidden Gem' tips for the specified destination. "
        "Return them as a concise list (bullet points), focusing on off-the-beaten-path experiences."
    )
    
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=f"Destination: {state['destination']}")
    ]
    
    response = llm.invoke(messages)
    
    # Simple parsing to get a list, though we'll just store the text bloc or split lines
    # The requirement says "add 3... tips to the local_tips list". 
    # Current State calls for local_tips: List[str]. 
    # We'll try to split by newlines or just store the whole block if parsing is complex.
    # Let's try to make it a list.
    
    content = response.content
    # Naive splitting on newlines and cleaning
    tips = [line.strip().lstrip("- ").lstrip("* ") for line in content.split('\n') if line.strip()]
    # Ensure we limit or format correctly? For now, just taking the non-empty lines.
    
    current_tips = state.get("local_tips", []) or []
    current_tips.extend(tips)
    
    return {"local_tips": current_tips}

def flight_search_agent(state: AgentState):
    """
    Search for flights using Tavily.
    """
    origin = state.get("origin", "")
    destination = state.get("destination", "")
    dates = state.get("dates", "")
    
    if not origin:
        return {"flight_info": "No origin city provided, cannot search for flights."}
        
    query = f"flights from {origin} to {destination} on {dates}"
    
    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = tavily.search(query=query, topic="general", max_results=3)
        
        # Format results
        results_text = "Flight Options Found:\n"
        for result in response.get("results", []):
            results_text += f"- [{result['title']}]({result['url']})\n  {result['content'][:200]}...\n"
            
        return {"flight_info": results_text}
    except Exception as e:
        return {"flight_info": f"Error searching for flights: {str(e)}"}


def summary_node(state: AgentState):
    """
    Aggregates everything into a final Markdown report.
    """
    system_message = (
        "You are a travel concierge. Create a final travel plan in Markdown. "
        "Include the itinerary, any budget notes, weather alerts, flight options, and local hidden gems."
    )
    
    content = f"Destination: {state['destination']}\nDates: {state['dates']}\n"
    content += f"Itinerary:\n{state.get('itinerary', 'No itinerary generated.')}\n\n"
    
    if state.get("budget_feedback"):
        content += f"Budget Notes:\n{state['budget_feedback']}\n\n"
        
    if state.get("alerts"):
        content += f"Alerts:\n" + "\n".join(f"- {a}" for a in state["alerts"]) + "\n\n"
        
    if state.get("local_tips"):
        content += f"Local Hidden Gems:\n" + "\n".join(f"- {t}" for t in state["local_tips"]) + "\n\n"

    if state.get("flight_info"):
        content += f"Flight Info:\n{state['flight_info']}\n\n"
        
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=content)
    ]
    
    response = llm.invoke(messages)
    
    # Returning as a message in the state for the final output
    return {"messages": [response]}
