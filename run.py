"""
    This file is the start of the CLI, contains the neccessary pipeline for users to scrape and
    run the AI models all at once.
"""
from src import MCSRClient, MCSRPipeline

#Data scraping -> Transform into csvs -> Feature Engineer -> Feed into ML models -> Perform tournament selection

client = MCSRClient(rate_limit=0.8)
pipeline = MCSRPipeline(client)

#Data scraping
all_matches = {}
for season in range(1, 2):
    season_matches = pipeline.get_all_matches_of_all_players(season)
    for m in season_matches:
        all_matches[m["id"]] = m

print(f"Total matches: {len(all_matches)}")

#Enrich matches with detailed info (split times, resets, deaths)
pipeline.get_all_match_info(list(all_matches.keys()))


#Transform into csvs


#Feature Engineer


#Feed into ML models


#Tournament Predictions
