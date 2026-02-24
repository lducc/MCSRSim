"""
    This file scrapes the leaderboard, the phase leaderboard and the top 16 players
    (12 based on top 12 of the phase leaderboard + 4 from the LCQ - Last Chance Qualifier)
    in the MCSR API (In one season only, assuming season 9 for testing purposes.

"""

from scraper import MCSRScraper
import json
from typing import List, Dict
from pathlib import Path

# --- CONSTANTS ---
DIR = Path("../data/raw")
DIR.mkdir(parents=True, exist_ok=True)
SEASON_9 = {'season': '9'}
PHASE_LEADERBOARD_URL = 'https://mcsrranked.com/api/phase-leaderboard'
LEADERBOARD_URL = 'https://mcsrranked.com/api/leaderboard'
# USER_URL = "https://mcsrranked.com/api/users"
# PLayers winning LCQ (Based on Liquidpedia)
LCQ_WINNERS = ['HDMICables', 'steezFemboy', 'Pinne', 'steez']

# Note: Watermelon got banned even though he has enough points to qualify for playoffs -> Hax replaces with (13th place)
BANNED_PLAYERS = {'Watermelon1708': 'hackingnoises'} 

# --- FUNCTIONS ---
def export_json(uuid_list: List[str], reference_file: Dict, export_link: str, verbose: bool = False):
    """Filters the reference file for specific UUIDs and exports to JSON."""
    raw = reference_file.get("data", {}).get("users", [])
    
    return_json = []
                    
    for user in raw:
        if user['uuid'] in uuid_list:
            if verbose: #Pretty print if verbose
                print(f"{user['nickname']:>15}:  UUID = {user['uuid']}  |  EloRate = {user['eloRate']}  |  phasePoint = {user['seasonResult']['phasePoint']}")
            return_json.append(user)

    with open(export_link, "w") as file:
        json.dump(return_json, file, indent=4) 

# --- MAIN ---
if __name__ == "__main__":
    scraper = MCSRScraper()
    print("Fetching Leaderboards")

    # Fetching leaderboard + Phase leaderboard (For top 12 players)
    leaderboard_raw = scraper.query_url(LEADERBOARD_URL, params=SEASON_9)
    with open(f"{DIR}/leaderboard_s9.json", "w") as file:
        json.dump(leaderboard_raw, file, indent=4)

    phase_raw = scraper.query_url(PHASE_LEADERBOARD_URL, params=SEASON_9)
    with open(f"{DIR}/phase_leaderboard_s9.json", "w") as file:
        json.dump(phase_raw, file, indent=4)

    # Get Top 12 speedrunners
    playoffs_s9_uuid = []
    users = phase_raw.get("data", {}).get("users", [])
    for i in range(12): 
        playoffs_s9_uuid.append(users[i]['uuid'])


    # Adding LCQ Winners
    uuid_map = scraper.get_uuid_map(leaderboard_raw)

    for nickname in LCQ_WINNERS:
        if nickname in uuid_map:
            playoffs_s9_uuid.append(uuid_map[nickname])
        else:
            print(f"{nickname} not found")

    # Special case: Handle ban and replacement in S9
    for banned, replacement in BANNED_PLAYERS.items():
        banned_uuid = uuid_map.get(banned)
        replacement_uuid = uuid_map.get(replacement)
        
        if banned_uuid in playoffs_s9_uuid:
            playoffs_s9_uuid.remove(banned_uuid)
            if replacement_uuid:
                playoffs_s9_uuid.append(replacement_uuid)
                print(f"Replaced {banned} with {replacement}")

    # Export s9 players into json
    print("Playoff players in S9:")

    export_json(
        uuid_list=playoffs_s9_uuid, 
        reference_file=leaderboard_raw,
        export_link=f'{DIR}/playoff_s9.json',
        verbose=True
    )



