import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(page_title="Trip Planner | AI Travel Assistant", page_icon="🌍", layout="wide")

# Custom CSS for modern look
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    .stTextArea textarea {
        border-radius: 10px;
    }
    .stTextInput input {
        border-radius: 10px;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    h1, h2, h3 {
        color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

if not os.getenv("OPENAI_API_KEY"):
    st.error("🔑 OPENAI_API_KEY missing. Please check your .env file.")
    st.stop()

try:
    from app.graph import app as graph_app
except Exception as e:
    st.error(f"Failed to import graph: {e}")
    st.stop()

# Header
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("# 🌍") 
with col_title:
    st.title("AI Personal Trip Planner")
    st.markdown("Your personalized schedule, budget auditor, event scout, and packing assistant.")

st.divider()

# Left Sidebar for Inputs
with st.sidebar:
    st.header("✈️ Trip Details")
    origin = st.text_input("From", value="New York")
    destination = st.text_input("To", value="London")
    dates = st.text_input("Dates", value="August 10-15, 2024")
    interests = st.text_area("Preferences & Interests", value="History, Pubs, Museums, Jazz Music", height=100)
    
    st.markdown("### 🔧 Settings")
    budget_level = st.select_slider("Budget Level", options=["Budget", "Moderate", "Luxury"], value="Moderate")
    
    generate_btn = st.button("🚀 Generate Trip Plan", type="primary")

# Main Content Area - Placeholder before generation
if not generate_btn and "final_state" not in st.session_state:
    st.info("👈 Enter your trip details in the sidebar and click 'Generate Trip Plan' to start!")
    
    # Showcase features
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🗺️ Smart Mapping")
        st.caption("Auto-plots your itinerary on an interactive map.")
    with c2:
        st.markdown("### 🎒 Packing Lists")
        st.caption("Weather-aware packing checklists generated for you.")
    with c3:
        st.markdown("### 🎟️ Live Events")
        st.caption("Finds real concerts and events happening during your trip.")


# State Management for App execution
if generate_btn:
    with st.spinner("🤖 Agents working: Builder -> Packing/Events/Map -> Summary..."):
        initial_state = {
            "destination": destination,
            "origin": origin,
            "dates": dates,
            "preferences": [i.strip() for i in interests.split(",")],
             "messages": []
        }
        try:
            final_state = graph_app.invoke(initial_state)
            st.session_state["final_state"] = final_state
        except Exception as e:
            st.error(f"Error running agents: {e}")

# Display Results if state exists
if "final_state" in st.session_state:
    state = st.session_state["final_state"]
    
    # Organize into Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Itinerary & Plan", "🗺️ Map View", "🎟️ Live Events", "🎒 Logistics & Packing"])
    
    with tab1:
        st.subheader(f"Trip to {state.get('destination')}")
        
        # Pull final report message or generic itinerary
        msgs = state.get("messages", [])
        if msgs and len(msgs) > 0:
            final_report = msgs[-1].content
        else:
            final_report = state.get("itinerary", "No details generated.")
            
        st.markdown(final_report)
        
        # Agent Insights in Expanders
        with st.expander("💰 Budget Audit"):
            st.write(state.get("budget_feedback", "No budget concerns."))
        
        with st.expander("💎 User Suggestions"):
            for tip in state.get("local_tips", []):
                st.write(f"- {tip}")

    with tab2:
        st.subheader("Interactive Map")
        markers = state.get("map_markers", [])
        if markers:
            # Create a DF for st.map
            map_data = pd.DataFrame(markers)
            # rename for Streamlit (requires lat/lon or latitude/longitude columns)
            # Our state has 'lat', 'lon'
            st.map(map_data, zoom=12, use_container_width=True)
            
            # Show legend/details below
            st.write("### Key Locations:")
            cols = st.columns(3)
            for idx, marker in enumerate(markers):
                with cols[idx % 3]:
                    st.info(f"**{marker['name']}**")
        else:
            st.warning("No map markers could be generated for this location.")

    with tab3:
        st.subheader("Live Events & Concerts")
        st.markdown(state.get("events", "No specific events found."))

    with tab4:
        col_pack, col_flights = st.columns(2)
        
        with col_pack:
            st.subheader("Smart Packing List")
            st.markdown(state.get("packing_list", "No packing list generated."))
            
        with col_flights:
            st.subheader("Flight Options")
            st.markdown(state.get("flight_info", "No flights found."))
            
            st.subheader("Safety Alerts")
            alerts = state.get("alerts", [])
            if alerts:
                for a in alerts:
                    st.error(a)
            else:
                st.success("No major alerts for this destination.")
