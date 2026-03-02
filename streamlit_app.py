import json
import streamlit as st
from google.cloud import bigquery
from google import genai

PROJECT_ID = "notional-gist-474313-e1"
DATASET = "football_ai"
VERTEX_LOCATION = "us-central1"
MODEL_NAME = "gemini-2.5-flash-lite"

# ----------------------------
# BigQuery helpers
# ----------------------------

MATCH_LIST_SQL = f"""
WITH p AS (
  SELECT DISTINCT match_id
  FROM `{PROJECT_ID}.{DATASET}.passes_flat`
),
s AS (
  SELECT DISTINCT match_id
  FROM `{PROJECT_ID}.{DATASET}.shots_flat`
)
SELECT
  m.match_id,
  m.match_date,
  m.home_team,
  m.away_team,
  m.home_score,
  m.away_score
FROM `{PROJECT_ID}.{DATASET}.matches` m
JOIN p USING (match_id)
JOIN s USING (match_id)
ORDER BY m.match_date DESC, m.match_id DESC
"""

@st.cache_data(ttl=300)
def get_loaded_matches():
    """Return only matches that actually exist in passes_flat AND shots_flat."""
    bq = bigquery.Client(project=PROJECT_ID)
    df = bq.query(MATCH_LIST_SQL).to_dataframe()

    if not df.empty:
        df["label"] = (
            df["match_date"].astype(str)
            + " | "
            + df["home_team"] + " " + df["home_score"].astype(str)
            + "-" + df["away_score"].astype(str) + " " + df["away_team"]
            + " | (match_id=" + df["match_id"].astype(str) + ")"
        )
    return df

def _job_config_mid(match_id: int) -> bigquery.QueryJobConfig:
    return bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("mid", "INT64", match_id)]
    )

def _scalar_count(bq: bigquery.Client, sql: str, match_id: int) -> int:
    df = bq.query(sql, job_config=_job_config_mid(match_id)).to_dataframe()
    return int(df.iloc[0, 0]) if not df.empty else 0

@st.cache_data(ttl=300)
def get_match_meta(match_id: int) -> dict:
    """Fetch match teams + score for goal_minus_xg calculation and display."""
    bq = bigquery.Client(project=PROJECT_ID)
    sql = f"""
        SELECT match_id, match_date, home_team, away_team, home_score, away_score
        FROM `{PROJECT_ID}.{DATASET}.matches`
        WHERE match_id = @mid
        LIMIT 1
    """
    df = bq.query(sql, job_config=_job_config_mid(match_id)).to_dataframe()
    if df.empty:
        return {}
    return df.iloc[0].to_dict()

@st.cache_data(ttl=300)
def get_team_shots_xg(match_id: int):
    """
    Team summary table.
    Adds goal_minus_xg = goals - total_xg (positive => overperformed xG).
    """
    bq = bigquery.Client(project=PROJECT_ID)

    shots_sql = f"""
        SELECT team_name,
               COUNT(*) AS shots,
               ROUND(SUM(shot_xg), 3) AS total_xg
        FROM `{PROJECT_ID}.{DATASET}.shots_flat`
        WHERE match_id = @mid
        GROUP BY team_name
    """
    shots_df = bq.query(shots_sql, job_config=_job_config_mid(match_id)).to_dataframe()

    meta = get_match_meta(match_id)
    if meta and not shots_df.empty:
        home_team = meta.get("home_team")
        away_team = meta.get("away_team")
        home_score = meta.get("home_score")
        away_score = meta.get("away_score")

        def calc_goal_minus_xg(row):
            # Only compute if team names match expected home/away
            if row["team_name"] == home_team:
                return round(float(home_score) - float(row["total_xg"]), 2)
            if row["team_name"] == away_team:
                return round(float(away_score) - float(row["total_xg"]), 2)
            return None

        shots_df["goal_minus_xg"] = shots_df.apply(calc_goal_minus_xg, axis=1)

        # Optional: sort by xG desc now that we added column
        shots_df = shots_df.sort_values(by="total_xg", ascending=False, ignore_index=True)

    return shots_df

@st.cache_data(ttl=300)
def get_team_passing(match_id: int):
    bq = bigquery.Client(project=PROJECT_ID)
    sql = f"""
        SELECT team_name,
               COUNT(*) AS passes,
               SUM(CASE WHEN under_pressure THEN 1 ELSE 0 END) AS passes_under_pressure,
               SUM(CASE WHEN end_x >= 80 THEN 1 ELSE 0 END) AS passes_into_final_third,
               ROUND(AVG(length), 2) AS avg_pass_length
        FROM `{PROJECT_ID}.{DATASET}.passes_flat`
        WHERE match_id = @mid
        GROUP BY team_name
        ORDER BY team_name
    """
    return bq.query(sql, job_config=_job_config_mid(match_id)).to_dataframe()

@st.cache_data(ttl=300)
def get_top_shooters(match_id: int):
    bq = bigquery.Client(project=PROJECT_ID)
    sql = f"""
        SELECT team_name, player_name,
               COUNT(*) AS shots,
               ROUND(SUM(shot_xg), 3) AS xg
        FROM `{PROJECT_ID}.{DATASET}.shots_flat`
        WHERE match_id = @mid
        GROUP BY team_name, player_name
        ORDER BY xg DESC
        LIMIT 10
    """
    return bq.query(sql, job_config=_job_config_mid(match_id)).to_dataframe()

def ensure_match_has_data(match_id: int):
    """Fail fast with an explicit message if tables don’t contain the selected match."""
    bq = bigquery.Client(project=PROJECT_ID)

    passes_count = _scalar_count(
        bq,
        f"SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET}.passes_flat` WHERE match_id = @mid",
        match_id,
    )
    shots_count = _scalar_count(
        bq,
        f"SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET}.shots_flat` WHERE match_id = @mid",
        match_id,
    )

    if passes_count == 0 or shots_count == 0:
        st.error(
            "Selected match has incomplete data in BigQuery.\n\n"
            f"- match_id: {match_id}\n"
            f"- passes_flat rows: {passes_count}\n"
            f"- shots_flat rows: {shots_count}\n\n"
            "Fix: load this match into passes_flat/shots_flat, or restrict the dropdown to loaded matches."
        )
        st.stop()

# ----------------------------
# Vertex / report generation
# ----------------------------

def build_context(match_row: dict, passing_df, shots_df, top_df) -> dict:
    return {
        "match": match_row,
        "passing": passing_df.to_dict(orient="records"),
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
- Bullet points comparing shots, xG, goal_minus_xg, passes, passes under pressure, passes into final third.

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

# ----------------------------
# Streamlit app
# ----------------------------

def main():
    st.set_page_config(page_title="Football AI Match Report", layout="wide")
    st.title("Football AI Match Report & Player Insights (BigQuery + Vertex AI)")

    matches_df = get_loaded_matches()
    if matches_df.empty:
        st.error(
            "No matches available with BOTH passes and shots data.\n\n"
            "This means your passes_flat/shots_flat tables don’t overlap with matches.\n"
            "Load events for a match and rebuild passes_flat/shots_flat, or verify you’re in the right project."
        )
        return

    choice = st.selectbox("Select a match", matches_df["label"].tolist())
    row = matches_df[matches_df["label"] == choice].iloc[0].to_dict()
    match_id = int(row["match_id"])

    ensure_match_has_data(match_id)

    # Pull metrics
    shots_df = get_team_shots_xg(match_id)
    passing_df = get_team_passing(match_id)
    top_df = get_top_shooters(match_id)

    # KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Home", f"{row['home_team']} ({row['home_score']})")
    with col2:
        st.metric("Away", f"{row['away_team']} ({row['away_score']})")
    with col3:
        st.metric("Date", str(row["match_date"]))

    st.subheader("Team summary (Shots & xG)")
    st.dataframe(shots_df, width="stretch")

    st.subheader("Team passing profile")
    st.dataframe(passing_df, width="stretch")

    st.subheader("Top shooters (by xG)")
    st.dataframe(top_df, width="stretch")

    st.divider()

    if "report" not in st.session_state:
        st.session_state["report"] = ""

    if st.button("Generate AI match report"):
        context = build_context(
            {
                "match_id": match_id,
                "match_date": str(row["match_date"]),
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "home_score": int(row["home_score"]),
                "away_score": int(row["away_score"]),
            },
            passing_df,
            shots_df,
            top_df,
        )
        with st.spinner("Calling Vertex AI..."):
            st.session_state["report"] = generate_report(context)

    if st.session_state["report"]:
        st.subheader("AI Match Report")
        st.text(st.session_state["report"])

if __name__ == "__main__":
    main()