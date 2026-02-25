# Football AI Match Report & Player Insights  
### BigQuery • Vertex AI • Streamlit • Cloud Run
Report:

https://docs.google.com/document/d/1Hy8zIvBR4jUCD3KuPIN_g5RhNe5nGvVq0sZSJlKZxVc/edit?usp=sharing

Live App:  
https://football-ai-app-422822231283.us-central1.run.app

<img width="2456" height="1112" alt="image" src="https://github.com/user-attachments/assets/e780b38b-8118-4ca5-98f4-928e9420ab9a" />


---

## Overview

This project demonstrates a full end-to-end football analytics and AI reporting pipeline built on Google Cloud Platform.

The application:

1. Loads public StatsBomb Open Data (JSON match events)
2. Transforms and flattens event data using Python
3. Stores structured tables in BigQuery
4. Computes team and player performance metrics
5. Generates an AI match report using Vertex AI (Gemini)
6. Serves the application via Streamlit on Cloud Run

The focus is on cloud architecture, reproducible data pipelines, and applied AI integration.

---

## Architecture

StatsBomb JSON (local files)  
→ Python ETL (flatten & normalize)  
→ BigQuery tables  
→ Streamlit app queries BigQuery  
→ Vertex AI generates report  
→ Cloud Run serves containerized app  

---

## BigQuery Data Model

Project: `notional-gist-474313-e1`  
Dataset: `football_ai` (EU)

### Tables

**matches**
- match_id
- match_date
- home_team
- away_team
- home_score
- away_score

**events_flat**
- Flattened event-level data

**passes_flat**
- match_id
- team_name
- player_name
- length
- end_x
- under_pressure

**shots_flat**
- match_id
- team_name
- player_name
- shot_xg

---

## Analytics Implemented

### Team Summary
- Total shots
- Total xG
- Goal minus xG (finishing over/underperformance)

### Passing Profile
- Total passes
- Passes under pressure
- Passes into final third
- Average pass length

### Player Metrics
- Top shooters by xG

---

## AI Integration (Vertex AI)

Model: `gemini-2.5-flash-lite`  
Location: `us-central1`

The prompt enforces:

- Use only provided JSON metrics
- Do not fabricate statistics
- Structured output:
  - MATCH REPORT
  - TEAM COMPARISON
  - COACHING INSIGHTS
  - PLAYER NOTES

---

## Local Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
