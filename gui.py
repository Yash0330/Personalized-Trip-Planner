import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables before importing the graph to ensure API keys are available
load_dotenv()

# Warn if keys are missing but allow the UI to load (will fail on execution if missing)
if not os.getenv("OPENAI_API_KEY"):
    st.warning("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

try:
    from app.graph import app as graph_app
except Exception as e:
    st.error(f"Failed to import application graph: {e}")
    st.stop()

st.set_page_config(page_title="Multi-Agent Travel Planner", layout="wide")

st.title("Multi-Agent Travel Planner ✈️")
st.markdown("---")

# Sidebar for Agent Outputs
with st.sidebar:
    st.header("🕵️ Agent Team")
    st.markdown("Real-time insights from your travel agents.")
    
    st.divider()
    
    budget_container = st.container()
    alert_container = st.container()
    suggestion_container = st.container()
    flight_container = st.container()

    # Initial states for sidebar
    with budget_container:
        st.subheader("💰 Budget Agent")
        st.info("Waiting for itinerary...")
        
    with alert_container:
        st.subheader("🌦️ Alert Agent")
        st.info("Checking weather/safety...")
        
    with suggestion_container:
        st.subheader("💎 Suggestion Agent")
        st.info("Looking for hidden gems...")
        
    with flight_container:
        st.subheader("✈️ Flight Agent")
        st.info("Searching for flights...")

# Main Input Area
st.header("Plan Your Trip")

col1, col2, col3 = st.columns(3)
with col1:
    origin = st.text_input("Origin", value="New York")
with col2:
    destination = st.text_input("Destination", value="London")
with col3:
    dates = st.text_input("Dates", value="August 10-15, 2024")

interests = st.text_area("Interests (comma separated)", value="History, Pubs, Museums")
try_concierge = st.button("Plan Trip", type="primary")

if try_concierge:
    if not destination or not dates or not origin:
        st.warning("Please provide origin, destination, and dates.")
    else:
        with st.spinner("Coordinating agents... (Builder -> Budget/Alert/Suggestions/Flights -> Summary)"):
            # Prepare initial state
            initial_state = {
                "destination": destination,
                "origin": origin,
                "dates": dates,
                "preferences": [i.strip() for i in interests.split(",")],
                "messages": []
            }
            
            try:
                # Invoke the LangGraph workflow
                final_state = graph_app.invoke(initial_state)
                
                # Extract results
                itinerary = final_state.get("itinerary", "No itinerary generated.")
                budget_feedback = final_state.get("budget_feedback", "")
                alerts = final_state.get("alerts", [])
                alerts = final_state.get("alerts", [])
                local_tips = final_state.get("local_tips", [])
                flight_info = final_state.get("flight_info", "")
                messages = final_state.get("messages", [])
                
                # Get the final summary if available (it might be in the last message content or itinerary)
                # The prompt for summary_node returns a message, but logic puts it in messages list.
                # However, the user asked to display the "Final Itinerary" in the main column.
                # The summary_node aggregates everything into a final Markdown report.
                # Let's check where the summary node output goes. 
                # In summary_node: return {"messages": [response]}
                
                final_report = ""
                if messages and len(messages) > 0:
                    final_report = messages[-1].content
                else:
                    final_report = itinerary # Fallback if summary failed

                # Update Main Column
                st.success("Trip Planning Complete!")
                st.markdown("### 🗺️ Final Itinerary & Report")
                st.markdown(final_report)
                
                # Update Sidebar with Agent Specifics
                with budget_container:
                    budget_container.empty() # Clear previous
                    st.subheader("💰 Budget Agent")
                    if budget_feedback:
                        st.warning(f"**Audit:** {budget_feedback}")
                    else:
                        st.success("Budget looks good!")

                with alert_container:
                    alert_container.empty()
                    st.subheader("🌦️ Alert Agent")
                    if alerts:
                        for alert in alerts:
                            st.error(f"**Alert:** {alert}")
                    else:
                        st.success("No alerts found.")

                with suggestion_container:
                    suggestion_container.empty()
                    st.subheader("💎 Suggestion Agent")
                    if local_tips:
                        for tip in local_tips:
                            st.markdown(f"- {tip}")
                    else:
                        st.info("No specific hidden gems found.")
                        
                with flight_container:
                    flight_container.empty()
                    st.subheader("✈️ Flight Agent")
                    if flight_info:
                        st.success("Flights found!")
                        st.markdown(flight_info)
                    else:
                        st.info("No flight info found.")
                        
            except Exception as e:
                st.error(f"Error running agents: {e}")
                st.info("Check your API Key and connection.")
