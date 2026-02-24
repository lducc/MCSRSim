""" 
    This file defines a class for easy scraping based on the MCSR API.
"""
import requests
import time
from typing import Dict

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
