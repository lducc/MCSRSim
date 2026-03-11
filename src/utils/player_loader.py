import yaml
from pathlib import Path
import json

DIR = Path("./data/players.yaml")

def load_players():
    with open(DIR) as f:
        raw = yaml.safe_load(f)

    players = raw["playoffs"]
    return players

if __name__ == "__main__":
    players = load_players()
    # with open('all_player.json', "w") as f:
    #     json.dump(players, f, indent=4)