from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from app.state import AgentState
from tavily import TavilyClient
import os
import logging

import json
from geopy.geocoders import Nominatim

# Setup Logger
logger = logging.getLogger("agent_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Initialize LLM
llm = ChatOpenAI(model="gpt-5-mini", temperature=0.7)

def itinerary_builder(state: AgentState):
    """
    Looks at destination, dates, and budget_feedback. 
    Generates a day-by-day itinerary.
    """
    logger.info(f"📍 STARTED: Itinerary Builder for {state['destination']}")
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
    logger.info("✅ COMPLETED: Itinerary Builder")
    return {"itinerary": response.content}

def budget_agent(state: AgentState):
    """
    Audits the itinerary and checks if it seems expensive.
    If it finds luxury items, it adds a comment to budget_feedback.
    """
    logger.info("💰 STARTED: Budget Agent")
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
    logger.info("✅ COMPLETED: Budget Agent")
    return {"budget_feedback": response.content}

def alert_agent(state: AgentState):
    """
    Mock a weather check. 
    If the destination is 'London' or 'Seattle', add a 'Rain Alert' to the alerts list.
    """
    logger.info("🌦️ STARTED: Alert Agent")
    destination = state.get("destination", "").lower()
    alerts = state.get("alerts", []) or []
    
    if destination in ["london", "seattle"]:
        if "Rain Alert" not in alerts:
            alerts.append("Rain Alert")
            
    logger.info(f"✅ COMPLETED: Alert Agent (Found {len(alerts)} alerts)")
    return {"alerts": alerts}

def suggestion_agent(state: AgentState):
    """
    Adds 3 'Hidden Gem' tips to the local_tips list based on the destination.
    """
    logger.info("💎 STARTED: Suggestion Agent")
    system_message = (
        "You are a local expert. Provide exactly 3 'Hidden Gem' tips for the specified destination. "
        "Return them as a concise list (bullet points), focusing on off-the-beaten-path experiences."
    )
    
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=f"Destination: {state['destination']}")
    ]
    
    response = llm.invoke(messages)
    
    content = response.content
    tips = [line.strip().lstrip("- ").lstrip("* ") for line in content.split('\n') if line.strip()]
    
    current_tips = state.get("local_tips", []) or []
    current_tips.extend(tips)
    
    logger.info("✅ COMPLETED: Suggestion Agent")
    return {"local_tips": current_tips}

def flight_search_agent(state: AgentState):
    """
    Search for flights using Tavily.
    """
    logger.info("✈️ STARTED: Flight Search Agent")
    origin = state.get("origin", "")
    destination = state.get("destination", "")
    dates = state.get("dates", "")
    
    if not origin:
        logger.warning("⚠️ Flight Agent: Info missing")
        return {"flight_info": "No origin city provided, cannot search for flights."}
        
    query = f"flights from {origin} to {destination} on {dates}"
    
    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = tavily.search(query=query, topic="general", max_results=3)
        
        results_text = "Flight Options Found:\n"
        for result in response.get("results", []):
            results_text += f"- [{result['title']}]({result['url']})\n  {result['content'][:200]}...\n"
            
        logger.info("✅ COMPLETED: Flight Search Agent (Found results)")
        return {"flight_info": results_text}
    except Exception as e:
        logger.error(f"❌ ERROR: Flight Search Failed: {e}")
        return {"flight_info": f"Error searching for flights: {str(e)}"}

def packing_agent(state: AgentState):
    """
    Generates a packing list based on destination, dates, and itinerary.
    """
    logger.info("🎒 STARTED: Packing Agent")
    system_message = (
        "You are a smart travel assistant. specific packing list based on the destination weather, "
        "duration, and specific activities mentioned in the itinerary. "
        "Group items by category (Clothing, Electronics, Toiletries, Documents)."
    )
    
    user_content = f"Destination: {state['destination']}\nDates: {state['dates']}\nItinerary Summary: {state.get('itinerary', '')[:500]}..."
    
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_content)
    ]
    
    response = llm.invoke(messages)
    logger.info("✅ COMPLETED: Packing Agent")
    return {"packing_list": response.content}

def event_agent(state: AgentState):
    """
    Searches for live events happening during the trip.
    """
    logger.info("🎟️ STARTED: Event Agent")
    destination = state.get("destination", "")
    dates = state.get("dates", "")
    
    query = f"events concerts festivals in {destination} {dates}"
    
    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = tavily.search(query=query, topic="news", max_results=5)
        
        events_text = ""
        for result in response.get("results", []):
            events_text += f"- **{result['title']}**: {result['content'][:150]}... [Link]({result['url']})\n"
            
        if not events_text:
            events_text = "No specific events found for these dates."
            
        logger.info("✅ COMPLETED: Event Agent (Found events)")
        return {"events": events_text}
    except Exception as e:
        logger.error(f"❌ ERROR: Event Search Failed: {e}")
        return {"events": f"Error searching for events: {str(e)}"}

def mapping_agent(state: AgentState):
    """
    Extracts locations from the itinerary and returns coordinates for the map.
    Uses LLM to extract city/place names, then geocodes them.
    """
    logger.info("🗺️ STARTED: Mapping Agent")
    itinerary = state.get("itinerary", "")
    # 1. Extract potential locations using LLM
    extraction_prompt = (
        "Identify 3-5 main specific landmarks, cities, or attractions mentioned in this itinerary. "
        "Return strictly a JSON list of strings, e.g., [\"Eiffel Tower\", \"Louvre Museum\"]. "
        "Do not include generic terms like 'Hotel' or 'Airport' unless named."
    )
    
    messages = [
        SystemMessage(content=extraction_prompt),
        HumanMessage(content=itinerary)
    ]
    
    try:
        response = llm.invoke(messages)
        # Clean up code blocks if checking
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        locations = json.loads(content)
        logger.info(f"📍 Mapping Agent: Extracted locations {locations}")
    except:
        locations = [state['destination']] # Fallback
        logger.warning(f"⚠️ Mapping Agent: Fallback to {locations}")
        
    # 2. Geocode
    geolocator = Nominatim(user_agent="trip_planner_agent")
    markers = []
    
    for loc in locations:
        try:
            location = geolocator.geocode(loc)
            if location:
                markers.append({
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "name": loc,
                    "description": f"Visit {loc}"
                })
        except:
            continue
            
    logger.info(f"✅ COMPLETED: Mapping Agent (Generated {len(markers)} markers)")
    return {"map_markers": markers}

def summary_node(state: AgentState):
    """
    Aggregates everything into a final Markdown report.
    """
    logger.info("📝 STARTED: Summary Node")
    system_message = (
        "You are a travel concierge. Create a final travel plan in Markdown. "
        "Include the itinerary, budget notes, weather alerts, flight options, local hidden gems, "
        "a packing checklist, and a list of cool live events nearby."
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
        
    if state.get("packing_list"):
        content += f"Packing List:\n{state['packing_list']}\n\n"

    if state.get("events"):
        content += f"Live Events:\n{state['events']}\n\n"
        
    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=content)
    ]
    
    response = llm.invoke(messages)
    
    logger.info("✅ COMPLETED: Summary Node")
    # Returning as a message in the state for the final output
    return {"messages": [response]}
