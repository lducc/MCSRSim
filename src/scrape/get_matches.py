"""
    This file scrapes all matches from the players that made it into playoffs
    in a season (assuming season 9 here for simplicity) of MCSR Ranked.
"""
from scraper import MCSRScraper
import json
from pathlib import Path

DIR = Path("data/raw")
DIR.mkdir(parents=True, exist_ok=True)
MATCHES_DIR = DIR / "matches"
MATCHES_DIR.mkdir(parents=True, exist_ok=True)
JSON_PATH = DIR / 'playoff_s9.json'

if __name__ == "__main__":
    with open(JSON_PATH, 'r') as file:
        players = json.load(file)

    scraper = MCSRScraper()
    for i, user in enumerate(players):
        params_matches = {'season': '9',
                        'type': '2'}
        user_uuid = user.get('uuid')
        nickname = user.get('nickname')

        filepath = MATCHES_DIR / f"{nickname}.json"

        #Skip if file exists
        if filepath.exists():
            continue

        print(user_uuid, nickname)

        matches_url = f"https://mcsrranked.com/api/users/{user_uuid}/matches"
        user_matches = []

        while True:
            response = scraper.query_url(matches_url, params = params_matches, polite_scraping=False)
            matches = response.get('data', None)

            if not matches:
                break

            user_matches.extend(matches)
            last_match_id = matches[-1].get('id')
            params_matches['before'] = last_match_id

        with open(filepath, 'w') as file:
            json.dump(user_matches, file, indent=4)


