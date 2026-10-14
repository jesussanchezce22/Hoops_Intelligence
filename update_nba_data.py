
"""Hoops Intelligence — NBA statistics importer.

Downloads NBA regular-season player per-game statistics.
Never replaces the published CSV with empty or invalid data.
"""

import argparse
import csv
import datetime as dt
import time
from pathlib import Path

FIELDS = [
    "name", "team", "pos", "pts", "reb", "ast",
    "stl", "blk", "tov", "gp", "games_next_week",
    "source", "season", "as_of"
]


def transform(rows, season):
    records = []
    as_of = dt.datetime.now(
        dt.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    for row in rows:
        name = str(row.get("PLAYER_NAME", "")).strip()
        gp = int(row.get("GP") or 0)

        if not name or gp < 1:
            continue

        records.append({
            "name": name,
            "team": str(row.get("TEAM_ABBREVIATION", "UNK")),
            "pos": "N/A",
            "pts": float(row["PTS"]),
            "reb": float(row["REB"]),
            "ast": float(row["AST"]),
            "stl": float(row["STL"]),
            "blk": float(row["BLK"]),
            "tov": float(row["TOV"]),
            "gp": gp,
            "games_next_week": "",
            "source": "NBA.com via nba_api",
            "season": season,
            "as_of": as_of,
        })

    if len(records) < 100:
        raise ValueError(
            f"Only {len(records)} player records returned. "
            "Refusing to publish incomplete data."
        )

    return records


def fetch_stats(season):
    from nba_api.stats.endpoints import leaguedashplayerstats

    last_error = None

    for attempt in range(1, 4):
        print(f"NBA.com attempt {attempt}/3", flush=True)

        try:
            result = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star="Regular Season",
                per_mode_detailed="PerGame",
                timeout=45,
            )

            data = result.get_normalized_dict()
            rows = data["LeagueDashPlayerStats"]

            if not rows:
                raise ValueError("NBA.com returned no players.")

            return rows

        except Exception as error:
            last_error = error
            print(
                f"Attempt {attempt} failed: "
                f"{type(error).__name__}: {error}",
                flush=True,
            )

            if attempt < 3:
                time.sleep(attempt * 5)

    raise RuntimeError(
        "NBA.com failed after three attempts. "
        "Existing data remains unchanged."
    ) from last_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2025-26")
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "players.csv"),
    )
    args = parser.parse_args()

    rows = fetch_stats(args.season)
    records = transform(rows, args.season)

    output = Path(args.output)
    temp = output.with_suffix(".tmp")

    try:
        with temp.open(
            "w", encoding="utf-8", newline=""
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=FIELDS
            )
            writer.writeheader()
            writer.writerows(records)

        temp.replace(output)

    finally:
        if temp.exists():
            temp.unlink()

    print(
        f"SUCCESS: {len(records)} players saved "
        f"to {output} for season {args.season}.",
        flush=True,
    )


if __name__ == "__main__":
    main()
