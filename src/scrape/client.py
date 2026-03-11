"""
    Pure API client for the MCSR Ranked API.
    One method per endpoint, stateless, no business logic.
"""
import requests
import time, json
from typing import Dict, List, Any, Optional
from enum import Enum

class MCSRClient:
    BASE_URL = "https://mcsrranked.com/api"

    def __init__(self, rate_limit: float = 1.0):
        self.session = requests.Session()
        self.rate_limit = rate_limit

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        response = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=15)
        response.raise_for_status()
        time.sleep(self.rate_limit)
        return response.json()


    def get_leaderboard(self, season: int) -> List[Dict[str, Any]]:
        params = {"season": season}
        data = self._get(endpoint="leaderboard", params=params)
        return data.get("data", {}).get("users", [])

    def get_phase_leaderboard(self, season: int) -> List[Dict[str, Any]]:
        params = {"season": season}
        data = self._get(endpoint="phase-leaderboard", params=params)
        return data.get("data", {}).get("users", [])

    def get_k_recent_matches_of_a_player(self,
                                         uuid: str,
                                         season: int,
                                         k: int = 100,
                                         before_match_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {
            'season': season,
            'excludedecay': 1,
            'count': k,
            'type': 2,
            'before': before_match_id,
        }
        data = self._get(f"users/{uuid}/matches", params)
        return data.get('data', [])

    def get_match_info(self, match_id: int) -> Dict[str, Any]:
        data = self._get(f"matches/{match_id}")
        if not data:
            raise ValueError(f"No data for match = {match_id}")
        return data

    # def get_user(self, identifier: str) -> Dict[str, Any]:
    #     data = self._get(f"users/{identifier}")
    #     return data.get("data", data)

    # def get_uuid_map(self, season: int, use_phase: bool = False) -> Dict[str, str]:
    #     """Returns a mapping of {'nickname': 'uuid'} from the leaderboard."""
    #     if use_phase:
    #         users = self.get_phase_leaderboard(season)
    #     else:
    #         users = self.get_leaderboard(season)
    #     return {user['nickname']: user['uuid'] for user in users}
