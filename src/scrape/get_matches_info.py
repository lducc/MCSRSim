"""
    This file tries to scrape the full match info that normally wouldnt be possible in the
    "https://mcsrranked.com/api/users/{user_uuid}/matches" endpoint that file "get_matches.py" uses.
    Instead, we scrape the full match timestamps based on the "api/matches/{match_id}" endpoint

"""

import pandas as pd
import json
import time
from pathlib import Path
from scraper import MCSRScraper

DIR = Path("./data")
CSV_PATH = DIR / "processed" / "all_matches.csv"

MATCH_INFO_DIR = DIR / "raw" / "matches_info"
MATCH_INFO_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    df = pd.read_csv(CSV_PATH)

    # Get a unique list of match IDs
    match_ids = df['match_id'].unique()
    total_matches = len(match_ids)

    # print(f"{total_matches} unique matches")

    scraper = MCSRScraper()

    for i, match_id in enumerate(match_ids, 1):
        filepath = MATCH_INFO_DIR / f"{match_id}.json"

        if filepath.exists():
            print(f"[{i}/{total_matches}] Skipping {match_id}")
            continue

        print(f"[{i}/{total_matches}] Downloading match {match_id}")

        url = f"https://mcsrranked.com/api/matches/{match_id}"

        try:
            response = scraper.query_url(url, polite_scraping=True)

            with open(filepath, "w") as f:
                json.dump(response, f, indent=4)

            time.sleep(0.1)

        except Exception as e:
            print(f"Error: {match_id}: {e}")
            time.sleep(10)