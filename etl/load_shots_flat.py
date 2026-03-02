import json
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "notional-gist-474313-e1"
DATASET = "football_ai"
TABLE = "shots_flat"

EVENTS_DIR = Path("data/events")

def safe_name(obj):
    return obj.get("name") if isinstance(obj, dict) else None

def main():
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    frames = []

    for path in sorted(EVENTS_DIR.glob("*.json")):
        match_id = int(path.stem)

        with path.open("r", encoding="utf-8") as f:
            events = json.load(f)

        rows = []
        for e in events:
            t = safe_name(e.get("type"))
            if t != "Shot":
                continue

            loc = e.get("location") or [None, None]
            s = e.get("shot") or {}

            rows.append({
                "shot_id": e.get("id"),
                "match_id": match_id,
                "idx": e.get("index"),
                "minute": e.get("minute"),
                "second": e.get("second"),
                "team_name": safe_name(e.get("team")),
                "player_name": safe_name(e.get("player")),
                "under_pressure": e.get("under_pressure"),
                "start_x": loc[0],
                "start_y": loc[1],
                "shot_xg": s.get("statsbomb_xg"),
                "outcome": safe_name(s.get("outcome")),
                "body_part": safe_name(s.get("body_part")),
                "technique": safe_name(s.get("technique")),
            })

        df = pd.DataFrame(rows)
        frames.append(df)
        print(f"Parsed {len(df):,} shots from match {match_id}")

    df_all = pd.concat(frames, ignore_index=True)

    job = client.load_table_from_dataframe(df_all, table_id)
    job.result()

    print(f"Loaded {len(df_all):,} rows into {table_id}")

if __name__ == "__main__":
    main()