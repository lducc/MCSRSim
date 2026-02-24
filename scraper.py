import requests
import json
import time, os
from typing import List, Dict

SEASON_9 = {'season': '9'}
RANKED_MATCHES = {'type': '2'}
PHASE_LEADERBOARD_URL = 'https://mcsrranked.com/api/phase-leaderboard'
LEADERBOARD_URL = 'https://mcsrranked.com/api/leaderboard'
# USER_URL = "https://mcsrranked.com/api/users"
#PLayers winning LCQ -> Move straight into playoffs
LCQ_WINNERS = ['HDMICables', 'steezFemboy', 'Pinne', 'steez']

#Note: Watermelon got banned even though he has enough points to qualify for playoffs -> Hax replaces with (13th place)
BANNED_PLAYERS = {'Watermelon1708': 'hackingnoises'} 


class MCSRScraper:
    def __init__(self):
        self.session = requests.Session()

    def query_url(self, url: str, params: Dict = None, polite_scraping : bool = True) -> Dict:
        """Fetches JSON from MCSR API"""
        response = self.session.get(url, params=params)
        response.raise_for_status()  
        if polite_scraping:
            time.sleep(1)                #wait 1 second between calls
        return response.json()


    def get_uuid_map(self, reference_file: Dict) -> Dict[str, str]:
        """Returns a mapping of {'nickname': 'uuid'} for instant lookup"""
        users = reference_file.get('data', {}).get('users', [])
        return {user['nickname']: user['uuid'] for user in users}
    

    def export_json(self, uuid_list: List[str], reference_file: Dict, export_link: str, verbose: bool = False):
        """Filters the reference file for specific UUIDs and exports to JSON."""
        raw = reference_file.get("data", {}).get("users", [])
        
        #Initialize json format
        return_json = {
            "status": reference_file.get("status"),
            "data": {
                "season": reference_file.get("data", {}).get("season"),
                "users": []
            }
        }
                        
        for user in raw:
            if user['uuid'] in uuid_list:
                if verbose: #Pretty print if verbose
                    print(f"{user['nickname']:>15}:  UUID = {user['uuid']}  |  EloRate = {user['eloRate']}  |  phasePoint = {user['seasonResult']['phasePoint']}")
                return_json['data']['users'].append(user)

        with open(export_link, "w") as file:
            json.dump(return_json, file, indent=4) 

if __name__ == "__main__":
    scraper = MCSRScraper() 
    
    print("Fetching Leaderboards...")

    #Fetching leaderboard + Phase leaderboard (For top 12 players)
    leaderboard_raw = scraper.query_url(LEADERBOARD_URL, params=SEASON_9)
    with open("leaderboard_s9.json", "w") as file:
        json.dump(leaderboard_raw, file, indent=4)

    phase_raw = scraper.query_url(PHASE_LEADERBOARD_URL, params=SEASON_9)
    with open("phase_leaderboard_s9.json", "w") as file:
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

    print("Playoff players in S9:")
    PLAYOFF_S9_PLAYERS = 'playoff_s9.json'
    scraper.export_json(
        uuid_list=playoffs_s9_uuid, 
        reference_file=leaderboard_raw,
        export_link=PLAYOFF_S9_PLAYERS,
        verbose=True
    )

    #Extract ranked matches for the 16 players

    
    # uuid = '9a8e24df4c8549d696a6951da84fa5c4'
    # for uuid in playoffs_s9_uuid:
    #     matches_url = f"https://mcsrranked.com/api/users/{uuid}/matches"
    #     response = scraper.query_url(matches_url, params = params_matches)
    #     print(response)

    with open('playoff_s9.json', 'r') as file:
        players = json.load(file)

    players_data = players.get('data', {}).get('users', [])
    for user in players_data:

        params_matches = {'season': '9',
                        'type': '2'}
        user_uuid = user.get('uuid')
        nickname = user.get('nickname')

        filepath = f'data/raw/matches/{nickname}.json'
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

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
            # print(last_match_id)
            params_matches['before'] = last_match_id

        with open(filepath, 'w') as file:
            json.dump(user_matches, file, indent=4)

