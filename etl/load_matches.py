import json
import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "notional-gist-474313-e1"
DATASET = "football_ai"
TABLE = "matches"

def main():
    # Read matches file
    with open("data/matches_37_4.json", "r", encoding="utf-8") as f:
        matches = json.load(f)

    rows = []
    for m in matches:
        rows.append({
            "match_id": int(m["match_id"]),
            "match_date": m.get("match_date"),
            "home_team": m["home_team"]["home_team_name"],
            "away_team": m["away_team"]["away_team_name"],
            "home_score": m.get("home_score"),
            "away_score": m.get("away_score"),
            "competition_id": m["competition"]["competition_id"],
            "season_id": m["season"]["season_id"],
        })

    df = pd.DataFrame(rows)

    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    job = client.load_table_from_dataframe(df, table_id)
    job.result()

    print(f"Loaded {len(df)} matches into {table_id}")

if __name__ == "__main__":
    main()