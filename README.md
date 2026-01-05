# Personalized Trip Planner

This project is a Personalized Trip Planner built with LangGraph, featuring a Sequential + Parallel architecture. It orchestrates key agents: Itinerary Builder, Budget Agent, Alert Agent, Suggestion Agent, and Flight Search Agent to deliver customized travel plans.

## 🛠️ Environment Setup

**1. Create the Environment**
```bash
python -m venv venv
source venv/bin/activate
```

**2. Set Up API Keys**

Create a `.env` file and add your keys:
```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

**3. Install LangGraph CLI**

```bash
pip install -U "langgraph-cli[inmem]"
```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the Agent**

```bash
langgraph dev
```
This will automatically open up LangSmith Studio.

**5. Run the GUI**

To use the interactive web interface:
```bash
streamlit run gui.py
```

## 📂 Project Structure
app/graph.py: Main graph definition (Fan-Out/Fan-In pattern).

app/agents.py: Logic for the 4 travel agents.

langgraph.json: CLI configuration.
