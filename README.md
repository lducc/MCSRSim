# MCSRSim

I like Minecraft and this is a project about me trying to predict 1v1 MCSR Ranked (Minecraft Speedrun) playoffs outcomes using ML and simulating their tournament brackets using Monte Carlo methods.

## Overview

**What is MCSR Ranked?**
MCSR Ranked is a platform where players could speedrun their way to victory by beating their opponent to see who can beat the game faster (to beat the Ender Dragon). Top players from MCSR Ranked have the chance to go into the biggest tournament to see who is the best Minecraft Speedruning player, MCSR Ranked Playoffs.

**What is MCSR Ranked Playoffs?**
MCSR Ranked Playoffs is a single-elim showdown between the top 16 best player in a season, 12 which are the top 12 players based on the leaderboards and consistency during the season, and the remaining 4 are chosen by a sub-tournament as the LCQ (Last Chance Qualifier).

**What does this project do?**

1. **Scrape** 10,000+ match records from the MCSR Ranked API (season 9 for now)
2. **Engineer features** from raw game data (split times, Elo ratings, consistency metrics)
3. **Train ML models** to predict match outcomes between two players
4. **Simulate tournaments** using Monte Carlo methods to forecast playoff winners (Coming Soon)


<!-- ## Pipeline Architecture

```
MCSR Ranked API                                          Streamlit Dashboard
      │                                                        ▲
      ▼                                                        │
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌────────────┐
│   Scraper   │───▶│   Feature    │───▶│    Model    │───▶│   Monte    │
│  (API ETL)  │    │ Engineering  │    │  Training   │    │   Carlo    │
└─────────────┘    └──────────────┘    └─────────────┘    │ Simulation │
                                                          └────────────┘
 get_players.py     build_features.py    train.py          simulate.py
 get_matches.py     engineer.py          compare.py
 get_matches_info.py                     evaluate.py
``` -->

## Features Engineered

| Feature | Description | Intuition |
|---|---|---|
| `elo_diff` | Elo rating difference between players | Higher-rated players win more often |
| `elo_expected` | Expected win probability from Elo formula | Baseline prediction from rating system |
| `rolling_consistency` | Std. deviation of recent completion times | Inconsistent players choke under pressure |
| `tilt_factor` | Performance trend over recent matches | Losing streaks affect gameplay |
| `nether_split_diff` | Difference in Nether entry times | Faster Overworld = stronger opener |
| `bastion_split_diff` | Difference in Bastion completion times | Bastion routing is a key skill differentiator |
| `fortress_split_diff` | Difference in Fortress clear times | Blaze fight speed matters |
| `end_fight_diff` | Difference in End fight times | Clutch ability in the final phase |
| `seed_type` | World seed category (Village, Desert Temple, etc.) | Some players specialize in certain seeds |
| `bastion_type` | Bastion structure type | Different bastions require different strategies |

<!-- ## Model Comparison

| Model | Accuracy | Log-Loss | Brier Score | AUC |
|---|---|---|---|---|
| Elo Baseline | ~55% | — | — | — |
| Logistic Regression | — | — | — | — |
| Random Forest | — | — | — | — |
| **XGBoost** | **~62%** | **0.647** | **0.228** | — |
| LightGBM | — | — | — | — |

> Fill in after running `src/models/compare.py` -->

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

<!-- ### Run the Pipeline (no scraping needed — processed data included)
```bash
# Train model and run simulation (~2 min)
python run_pipeline.py --season 9 --from train

# Full pipeline including scraping (~2-3 hours)
python run_pipeline.py --season 9 --scrape
```

### Run Notebooks
```bash
jupyter notebook notebooks/
```
- `01_eda.ipynb` — Exploratory data analysis and visualizations
- `02_results.ipynb` — Model results, SHAP analysis, calibration, Monte Carlo outcomes -->

## Project Structure

```
MCSRSim/
├── README.md
├── requirements.txt
├── LICENSE
├── run_pipeline.py                 # CLI entry point
│
├── src/
│   ├── scrape/                     # Data collection from MCSR API
│   │   ├── scraper.py              # Base scraper with rate limiting
│   │   ├── get_players.py          # Fetch Season 9 playoff qualifiers
│   │   ├── get_matches.py          # Fetch match history per player
│   │   └── get_matches_info.py     # Fetch detailed match timelines
│   │
│   ├── features/                   # Feature engineering
│   │   ├── build_features.py       # Raw JSON → all_matches.csv
│   │   └── engineer.py             # all_matches.csv → model_train.csv
│   │
│   ├── models/                     # ML pipeline
│   │   ├── train.py                # XGBoost + Optuna hyperparameter tuning
│   │   ├── compare.py              # Multi-model comparison
│   │   ├── evaluate.py             # Metrics, SHAP, calibration analysis
│   │   └── simulate.py             # Monte Carlo bracket simulation
│   │
│   └── utils/
│       └── config.py               # Paths and constants
│
├── notebooks/
│   ├── 01_eda.ipynb                # Exploratory analysis
│   └── 02_results.ipynb            # Results and interpretation
│
├── data/
│   ├── raw/                        # Scraped JSON (gitignored)
│   └── processed/                  # Cleaned CSVs (included in repo)
│       ├── all_matches.csv
│       └── model_train.csv
│
└── models/                         # Saved model artifacts
    └── xgb_best.json
```

## Data Collection

Data is collected via polite scraping from the [MCSR Ranked API](https://mcsrranked.com):

- **Leaderboard + Phase Leaderboard** → identify the top 16 playoff qualifiers
  - Top 12 from phase leaderboard
  - 4 from Last Chance Qualifier (LCQ)
  - Handles edge cases (banned players and their replacements)
- **Match History** → all ranked matches for each qualifier in Season 9
- **Match Details** → detailed timeline data (split times, resets, deaths) for each match

> Scraping is rate-limited (1 req/sec) to be respectful to the API.

## Monte Carlo Tournament Simulation

The trained model's predicted win probabilities are used to simulate the playoff bracket structure:

1. For each matchup, the model predicts P(Player A wins)
2. The outcome is sampled from a Bernoulli distribution with that probability
3. Winners advance through the bracket
4. This is repeated 10,000 times
5. Each player's tournament win % is calculated from the simulations

## License

MIT License — see [LICENSE](LICENSE) for details.
