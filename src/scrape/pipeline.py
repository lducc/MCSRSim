"""
    This is a pipeline orchestrator to compile all the players and ranked matches data
    using the MCSR Ranked API.
"""

import os, json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum
from tqdm import tqdm

from .client import MCSRClient
from ..utils import load_players


class MCSRPipeline:
    def __init__(self, client: MCSRClient, data_dir: Path = Path("data/raw")):
        self.client = client
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.PLAYERS_IN_EVERY_SEASONS = load_players()

    def get_all_matches_of_a_player(self, uuid: str, season: int) -> List[Dict[str, Any]]:
        all_matches = []
        k_most_recent_matches = self.client.get_k_recent_matches_of_a_player(uuid, season)

        if not k_most_recent_matches:
            return all_matches

        all_matches.extend(k_most_recent_matches)
        before_match_id = k_most_recent_matches[-1].get("id", '')

        while True:
            k_next_recent_matches = self.client.get_k_recent_matches_of_a_player(uuid, season, before_match_id=before_match_id)
            if not k_next_recent_matches:
                break

            before_match_id = k_next_recent_matches[-1].get("id", "")
            all_matches.extend(k_next_recent_matches)

        return all_matches

    def get_seasonal_players(self, season: int) -> List[Dict[str, str]]:
        return self.PLAYERS_IN_EVERY_SEASONS.get(season, [])

    def get_all_matches_of_all_players(self, season: int, use_cache: bool = True) -> List[Dict[str, Any]]:
        cache_path = self.data_dir / f"matches_s{season}.json"

        if cache_path.exists() and use_cache:
            print(f"Season {season}: loading from cache ({cache_path})")
            with open(cache_path) as f:
                return json.load(f)

        matches = {}
        players = self.get_seasonal_players(season)

        for player in tqdm(players, desc=f"S{season} matches", unit="player"):
            uuid = player.get('uuid')
            player_matches = self.get_all_matches_of_a_player(uuid, season)

            for match in player_matches:
                matches[match["id"]] = match

        result = list(matches.values())

        with open(cache_path, "w") as f:
            json.dump(result, f, indent=4)

        return result

    def get_match_info(self, match_id: int, use_cache: bool = True) -> Dict[str, Any]:
        info_dir = self.data_dir / "matches_info"
        info_dir.mkdir(parents=True, exist_ok=True)
        cache_path = info_dir / f"{match_id}.json"

        if cache_path.exists() and use_cache:
            with open(cache_path) as f:
                return json.load(f)

        response = self.client.get_match_info(match_id)

        with open(cache_path, "w") as f:
            json.dump(response, f, indent=4)

        return response

    def get_all_match_info(self, match_ids: List[int], use_cache : bool = True) -> List[Dict[str, Any]]:
        results = []
        for match_id in tqdm(match_ids, desc="Getting matches info", unit="match"):
            try:
                result = self.get_match_info(match_id, use_cache=use_cache)
                results.append(result)
            except Exception as e:
                print(f"Error for match_id = {match_id}: {e}")
                time.sleep(5)

        return results
