# Football AI Match Report & Player Insights  
BigQuery • Vertex AI • Streamlit • Cloud Run

---

## Project Links

**Full Technical Report:**  
https://docs.google.com/document/d/1Hy8zIvBR4jUCD3KuPIN_g5RhNe5nGvVq0sZSJlKZxVc/edit?usp=sharing

**Live Application:**  
https://football-ai-app-422822231283.us-central1.run.app

<img src="https://github.com/user-attachments/assets/e780b38b-8118-4ca5-98f4-928e9420ab9a" alt="Application Screenshot" />

---

## Overview

This project implements an end-to-end football analytics and AI reporting pipeline built on Google Cloud Platform.

The application:

1. Loads public StatsBomb Open Data (JSON match events)  
2. Transforms and flattens event data using Python  
3. Stores structured tables in BigQuery  
4. Computes team and player performance metrics  
5. Generates an AI match report using Vertex AI (Gemini)  
6. Serves the application via Streamlit on Cloud Run  

The focus is on cloud-native architecture, reproducible data pipelines, and applied AI integration.

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

**Project:** `notional-gist-474313-e1`  
**Dataset:** `football_ai` (EU region)

### Core Tables

#### `matches`
- match_id  
- match_date  
- home_team  
- away_team  
- home_score  
- away_score  

#### `events_flat`
- Flattened event-level dataset  

#### `passes_flat`
- match_id  
- team_name  
- player_name  
- length  
- end_x  
- under_pressure  

#### `shots_flat`
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
- Top shooters by xG contribution  

---

## AI Integration (Vertex AI)

**Model:** `gemini-2.5-flash-lite`  
**Location:** `us-central1`

Prompt constraints:

- Use only provided JSON metrics  
- Do not fabricate statistics  
- Structured output sections:
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
```

Open in browser:
http://localhost:8501

## Containerization

The application is containerized using Docker and deployed through Google Cloud Build and Artifact Registry.

Base image:  
`python:3.11-slim`

Streamlit is configured for Cloud Run headless mode with dynamic `$PORT` injection.

---

## Deployment

### Build Container Image

```bash
gcloud builds submit --tag us-central1-docker.pkg.dev/notional-gist-474313-e1/football-ai-repo/football-ai:latest .
```

### Deploy to Cloud Run

```bash
gcloud run deploy football-ai-app \
  --image us-central1-docker.pkg.dev/notional-gist-474313-e1/football-ai-repo/football-ai:latest \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Required IAM Roles

The Cloud Run runtime service account requires:

- BigQuery Data Viewer  
- BigQuery Job User  
- Vertex AI User  

---

## Technical Design Decisions

- Flattened JSON before BigQuery load to avoid nested schema complexity  
- Separate `passes_flat` and `shots_flat` tables for cleaner aggregations  
- Parameterized BigQuery queries for secure data access  
- Guardrail validation for match selection integrity  
- Fully containerized and reproducible deployment  
- Cloud-native AI integration using Vertex AI  

---

## Future Improvements

- Expand to full competition season ingestion  
- Add xG flow and timeline visualizations  
- Introduce caching via BigQuery views  
- Add authentication layer  
- Implement CI/CD trigger-based pipeline  
- Add monitoring and logging  

---

## Tech Stack

- Python  
- Pandas  
- Google Cloud BigQuery  
- Google Vertex AI (Gemini)  
- Streamlit  
- Docker  
- Cloud Build  
- Cloud Run  

---

## Status

Publicly deployed and fully operational on Google Cloud Run.

Demonstrates end-to-end data engineering, cloud infrastructure management, analytics design, and AI system integration.
