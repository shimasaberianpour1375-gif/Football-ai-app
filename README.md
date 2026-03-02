\# Football AI Match Report (BigQuery + Vertex AI + Cloud Run)



Deployed app: https://football-ai-app-422822231283.us-central1.run.app



\## What it does

This app loads StatsBomb Open Data match events into BigQuery, computes match/team/player metrics (shots, xG, passing profile, goal\_minus\_xg), and generates an AI-written match report using Vertex AI (Gemini). The UI is built with Streamlit and deployed on Cloud Run.



\## Architecture

StatsBomb JSON (local) → BigQuery tables (`matches`, `events\_flat`, `passes\_flat`, `shots\_flat`) → Streamlit app queries BigQuery → Vertex AI generates report → Cloud Run serves the app.



\## BigQuery dataset

Project: `notional-gist-474313-e1`  

Dataset: `football\_ai` (EU)



Tables:

\- `matches` (match metadata)

\- `events\_flat` (flattened events)

\- `passes\_flat` (pass-only table)

\- `shots\_flat` (shot-only table)



\## Local run

```bash

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

streamlit run streamlit\_app.py

