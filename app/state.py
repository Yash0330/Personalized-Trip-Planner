from typing import TypedDict, List, Annotated
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    destination: str
    origin: str  # Added origin
    dates: str
    preferences: List[str]
    itinerary: str
    budget_feedback: str
    alerts: List[str]
    flight_info: str # Added flight info
    local_tips: List[str]
    packing_list: str
    events: str
    map_markers: List[dict] # [{lat: float, lon: float, name: str, description: str}]
    revision_count: int
