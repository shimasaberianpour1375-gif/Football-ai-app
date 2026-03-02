import json
from pathlib import Path
import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "notional-gist-474313-e1"
DATASET = "football_ai"
TABLE = "events_flat"

EVENTS_DIR = Path("data/events")

def safe_name(obj, key="name"):
    if isinstance(obj, dict):
        return obj.get(key)
    return None

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
            loc = e.get("location") or [None, None]

            rows.append({
                "event_id": e.get("id"),
                "match_id": match_id,
                "idx": e.get("index"),
                "period": e.get("period"),
                "minute": e.get("minute"),
                "second": e.get("second"),
                "ts": e.get("timestamp"),
                "type_name": safe_name(e.get("type")),
                "team_name": safe_name(e.get("team")),
                "player_name": safe_name(e.get("player")),
                "possession": e.get("possession"),
                "play_pattern": safe_name(e.get("play_pattern")),
                "under_pressure": e.get("under_pressure"),
                "x": loc[0],
                "y": loc[1],
            })

        frames.append(pd.DataFrame(rows))
        print(f"Parsed {len(rows):,} events from match {match_id}")

    df = pd.concat(frames, ignore_index=True)
    job = client.load_table_from_dataframe(df, table_id)
    job.result()

    print(f"Loaded {len(df):,} rows into {table_id}")

if __name__ == "__main__":
    main()