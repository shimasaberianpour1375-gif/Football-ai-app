import json
from google.cloud import bigquery
from google import genai

PROJECT_ID = "notional-gist-474313-e1"
DATASET = "football_ai"
VERTEX_LOCATION = "us-central1"
MODEL_NAME = "gemini-2.5-flash-lite"

def fetch_match_context(match_id: int) -> dict:
    bq = bigquery.Client(project=PROJECT_ID)

    # Match info
    q_match = f"""
    SELECT match_id, match_date, home_team, away_team, home_score, away_score
    FROM `{PROJECT_ID}.{DATASET}.matches`
    WHERE match_id = {match_id}
    """
    match_df = bq.query(q_match).to_dataframe()
    if match_df.empty:
        raise ValueError(f"match_id {match_id} not found in {PROJECT_ID}.{DATASET}.matches")
    match_info = match_df.iloc[0].to_dict()

    # Passing profile by team
    q_pass = f"""
    SELECT
      team_name,
      COUNT(*) AS passes,
      SUM(CASE WHEN under_pressure THEN 1 ELSE 0 END) AS passes_under_pressure,
      SUM(CASE WHEN end_x >= 80 THEN 1 ELSE 0 END) AS passes_into_final_third,
      ROUND(AVG(length), 2) AS avg_pass_length
    FROM `{PROJECT_ID}.{DATASET}.passes_flat`
    WHERE match_id = {match_id}
    GROUP BY team_name
    ORDER BY team_name
    """
    pass_df = bq.query(q_pass).to_dataframe()

    # Shots + xG by team
    q_shots = f"""
    SELECT
      team_name,
      COUNT(*) AS shots,
      ROUND(SUM(shot_xg), 3) AS total_xg
    FROM `{PROJECT_ID}.{DATASET}.shots_flat`
    WHERE match_id = {match_id}
    GROUP BY team_name
    ORDER BY team_name
    """
    shots_df = bq.query(q_shots).to_dataframe()

    # Top shooters (player)
    q_top = f"""
    SELECT
      team_name,
      player_name,
      COUNT(*) AS shots,
      ROUND(SUM(shot_xg), 3) AS xg
    FROM `{PROJECT_ID}.{DATASET}.shots_flat`
    WHERE match_id = {match_id}
    GROUP BY team_name, player_name
    ORDER BY xg DESC
    LIMIT 8
    """
    top_df = bq.query(q_top).to_dataframe()

    return {
        "match": match_info,
        "passing": pass_df.to_dict(orient="records"),
        "shooting": shots_df.to_dict(orient="records"),
        "top_shooters": top_df.to_dict(orient="records"),
    }

def generate_report(context: dict) -> str:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=VERTEX_LOCATION,
    )

    prompt = f"""
You are an assistant performance analyst for a professional football club.

Rules:
- Use ONLY the numbers and facts in the JSON input.
- Do NOT invent players, events, or statistics.
- If a metric is missing, say it is not available.

Output format (use these headers exactly):

MATCH REPORT
- 6 to 10 sentences summarising the match.

TEAM COMPARISON
- Bullet points comparing shots, xG, passes, passes under pressure, passes into final third.

COACHING INSIGHTS
- 3 bullets. Tactical and actionable.

PLAYER NOTES
- 3 bullets. Use the top_shooters list and reference shots + xG.

JSON INPUT:
{json.dumps(context, indent=2)}
""".strip()

    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return resp.text

def main():
    # Pick one of your match ids: 19736, 19769, 19770, 19772, 19789
    match_id = 19769

    context = fetch_match_context(match_id)
    report = generate_report(context)

    print("\n================ AI MATCH REPORT ================\n")
    print(report)
    print("\n=================================================\n")

if __name__ == "__main__":
    main()