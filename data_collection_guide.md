# MCSR Playoffs Predictor — Complete Project Bible

> **Goal:** Build a predictive engine and Monte Carlo simulator for MCSR Ranked 1v1 Playoffs. Validate against Season 9 results, then predict Season 10.

---

## 1. Environment Setup

```bash
conda create -n mcsr python=3.11 pandas numpy scikit-learn xgboost matplotlib seaborn requests -c conda-forge -y
conda activate mcsr
pip install streamlit shap
```

---

## 2. Project Structure (Deployable)

```
E:\Code\MCSR\
├── data/
│   ├── raw/                        # Untouched API JSON (gitignored)
│   │   ├── leaderboard_s9.json
│   │   ├── matches/{nickname}.json
│   │   └── versus/{p1}_vs_{p2}.json
│   └── processed/                  # Cleaned CSVs for modeling
│       ├── all_matches.csv
│       ├── player_features.csv
│       └── player_seedtype_features.csv
├── src/
│   ├── __init__.py
│   ├── api_client.py               # Cached API wrapper + pagination
│   ├── collect.py                  # CLI: python -m src.collect
│   ├── features.py                 # Feature engineering pipeline
│   ├── model.py                    # XGBoost training & prediction
│   └── simulator.py                # Monte Carlo bracket engine
├── app.py                          # Streamlit dashboard (entry point)
├── config.py                       # Constants: season, cutoffs, rosters
├── requirements.txt
├── .gitignore
└── README.md
```

**CLI pipeline:**
```bash
python -m src.collect              # Pull & cache API data
python -m src.collect --validate   # Sanity check the data
python -m src.features             # Engineer features → CSVs
python -m src.model                # Train XGBoost
python -m src.simulator            # Run Monte Carlo 10,000x
streamlit run app.py               # Launch dashboard
```

---

## 3. API Reference (Verified Against Live Data)

> **Base URL:** `https://api.mcsrranked.com`
> **Rate limit:** 500 requests per 10 minutes. Total data pull is ~200 requests — well within limits.

### Endpoints

| Endpoint | Params | Returns |
|---|---|---|
| `GET /phase-leaderboard` | `season=9` | Phase points leaderboard. Sorted by phase points. Includes `predPhasePoint` (live predicted) and `seasonResult.phasePoint` (locked-in). **Use this one.** |
| `GET /leaderboard` | `season=9` | Elo leaderboard. Sorted by `seasonResult.eloRate`. Same player data, different sort order. |
| `GET /users/{identifier}` | — | Full player profile. Identifier = UUID or nickname. |
| `GET /users/{uuid}/matches` | `season=9`, `type=2`, `before={match_id}` | Player's ranked match history. ~20 matches per page. Paginate with `before`. |
| `GET /users/{uuid1}/versus/{uuid2}` | — | Head-to-head stats between two players. |

### Key Concepts

**`type=2`** means ranked matches (type 1 = casual).

**`phasePoint` vs `predPhasePoint`:**
- A Season = 4 months. Each month = 1 **Phase**.
- At the end of each Phase, you earn Phase Points based on your Elo rank at that moment (Rank 1 → 100 pts, Rank 2 → 97, etc.).
- `phasePoint` = **banked points** from completed Phases (locked, can't change).
- `predPhasePoint` = banked points + *projected* points if the current live Phase ended right now.
- For Season 9 (finished), both values are identical. For a live Season 10, use `predPhasePoint`.

**Why Phase Points matter:** Top 12 by phase points = automatic playoff invite (Seeds 1-12). Top 100 can enter the Last-Chance Qualifier for Seeds 13-16. Phase points reward **consistency across the whole season**, not one hot streak.

---

## 4. Data Collection — The 3 Layers

### Layer 1: WHO — Player Roster

```
GET /phase-leaderboard?season=9
```

Extract the **top 12** by `phasePoint` (auto-qualified), then manually add the **4 LCQ qualifiers** from Liquipedia.

Each player object contains:
```json
{
  "uuid": "635f35ee...",
  "nickname": "edcr",
  "eloRate": 2407,
  "seasonResult": { "eloRate": 2477, "eloRank": 5, "phasePoint": 282 }
}
```

**S9 Top 12 (verified):**

| Seed | Nickname | UUID | Phase Pts |
|---|---|---|---|
| 1 | edcr | `635f35ee69ed4f0c94ff26ece4818956` | 282 |
| 2 | Infume | `a54e3bc4c6354b07a236b81efbcfe791` | 276 |
| 3 | doogile | `3c8757790ab0400b8b9e3936e0dd535b` | 248 |
| 4 | Aquacorde | `253b53d832ab4bafb5ee0308d5164ccf` | 219 |
| 5 | silverrruns | `17e787d1d6374f818b294f2319db370d` | 212 |
| 6 | bing_pigs | `92b63a39b36a445fa94c77ae212dcea3` | 197 |
| 7 | nahhann | `2ef2bfed3d084649b56290328970ace9` | 193 |
| 8 | Feinberg | `9a8e24df4c8549d696a6951da84fa5c4` | 185 |
| 9 | BeefSalad | `3b01d4b4fef14f178b75f05c04dd34ef` | 181 |
| 10 | BlazeMind | `ac601ce7376f49cea7ce14cd577dac85` | 181 |
| 11 | lowk3y_ | `7665f76f431b41c6b321bea16aff913b` | 171 |
| 12 | Watermelon1708 | `cc432b2626a44ae1836a50244adbf468` | 159 |

> Seeds 13-16 (LCQ qualifiers) must be looked up from Liquipedia or MCSR Discord.

---

### Layer 2: HOW THEY PLAYED — Match History

For each of the 16 players:
```
GET /users/{uuid}/matches?season=9&type=2
```

**Pagination:** Each call returns ~20 matches. Take the `id` of the last match and pass `before={id}` to get the next page. Repeat until empty array.

**Each match object contains:**
```json
{
  "id": 4471359,
  "seedType": "BURIED_TREASURE",
  "date": 1767115960,
  "forfeited": false,
  "players": [
    { "uuid": "7c926787...", "nickname": "hackingnoises", "eloRate": 2176 },
    { "uuid": "bc80af38...", "nickname": "Ancoboyy", "eloRate": 2203 }
  ],
  "result": { "uuid": "7c926787...", "time": 512567 },
  "changes": [
    { "uuid": "7c926787...", "change": 14, "eloRate": 2597 },
    { "uuid": "bc80af38...", "change": -14, "eloRate": 2435 }
  ]
}
```

**Key fields to extract per match:**
| Field | Where | Notes |
|---|---|---|
| Match ID | `id` | Unique identifier |
| Seed Type | `seedType` | One of 5 types (see below) |
| Date | `date` | Epoch in seconds |
| Winner UUID | `result.uuid` | `null` if draw |
| Completion Time | `result.time` | In milliseconds (÷1000 for seconds) |
| Is Forfeit | `forfeited` | `true` = someone quit early |
| Player Elos | `players[].eloRate` | Current Elo at time of match |
| Elo Changes | `changes[]` | `change` = delta, `eloRate` = post-match Elo |

**Pre-match Elo trick:** `pre_match_elo = changes[].eloRate - changes[].change`

**The 5 Seed Types (Maps):**
| Seed Type | Unlock Elo | Notes |
|---|---|---|
| `VILLAGE` | All | Most common, broad biome variants |
| `SHIPWRECK` | All | Ocean-based, quick iron access |
| `DESERT_TEMPLE` | All | Early loot, lava pools nearby |
| `RUINED_PORTAL` | 600+ (Iron) | Can skip nether portal building |
| `BURIED_TREASURE` | 1200+ (Emerald) | Diamond access, high-Elo only |

> **DATE CUTOFF:** S9 Playoffs started Jan 11, 2026 (epoch `1736553600`). Filter `match.date < 1736553600` to exclude playoff matches from training data.

---

### Layer 3: HEAD-TO-HEAD — Matchup History

For every pair of playoff players (16 choose 2 = 120 pairs):
```
GET /users/{uuid1}/versus/{uuid2}
```

Gives you the historical win/loss between two specific players.

---

### Caching Strategy

Save each API response as raw JSON. Before any API call, check if the file exists first:

```python
import os, json, requests, time

def cached_get(url, filepath):
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    time.sleep(1.5)  # polite rate limiting
    return data
```

**File layout:**
```
data/raw/leaderboard_s9.json
data/raw/matches/{nickname}_matches.json       # all pages concatenated
data/raw/versus/{nickname1}_vs_{nickname2}.json
```

### Sanity Checks (Before Moving On)

Add a `--validate` flag to your collection script that prints:
- Total match count per player (expect 200-500 each)
- Seed type distribution (should see all 5 types)
- Players with fewer than 20 matches on any seed type (sparse data warning)
- Forfeit percentage (consider excluding forfeits from time-based features)
- Date range of matches (confirm nothing after the playoff cutoff)

---

## 5. Feature Engineering

Each row in the training CSV = one historical match between Player A and Player B.

**Target variable:** `did_a_win` (1 or 0)

### Category 1: Global Performance

| Feature | Formula | Source |
|---|---|---|
| `elo_a` | Pre-match Elo of Player A | `changes[].eloRate - changes[].change` |
| `elo_b` | Pre-match Elo of Player B | Same |
| `elo_diff` | `elo_a - elo_b` | Derived. Often the single strongest predictor. |
| `global_win_rate_a` | Wins ÷ Total matches (last 30 days) | Aggregate from match history |
| `avg_time_global_a` | Mean completion time (last 30 days) | Only non-forfeited matches |

### Category 2: Behavioral / Psychological ("Secret Sauce")

| Feature | Formula | Why It Matters |
|---|---|---|
| `consistency_score_a` | σ (std dev) of Player A's last 10 completion times | Low σ = reliable. High σ = erratic. **Your thesis: consistency > speed.** |
| `tilt_factor_a` | Win rate after a loss vs. baseline win rate | A player with 60% overall but 40% after losses is highly tiltable |
| `win_streak_a` | Consecutive wins entering this match | Captures momentum / hot hand |

### Category 3: Per-Seed-Type ("Map Awareness")

These are calculated **only from matches on the same seed type** as the current match.

| Feature | Formula | Why It Matters |
|---|---|---|
| `seed_win_rate_a` | Win rate on this specific seed type | Some players dominate Buried Treasure but struggle on Village |
| `seed_avg_time_a` | Avg completion time on this seed type | Raw speed on this map |
| `seed_time_diff` | `seed_avg_time_a - seed_avg_time_b` | Who is faster on this specific map? |

### Category 4: Head-to-Head

| Feature | Formula | Why It Matters |
|---|---|---|
| `h2h_win_rate_a_vs_b` | A's win % in all historical matches vs B | Stylistic matchups exist — some players are "kryptonite" for others |

### Optional Bonus Features (Add Later If Needed)

| Feature | Formula | When to Add |
|---|---|---|
| `elo_momentum_30d` | `elo_today - elo_30_days_ago` | Differentiates stagnant vs. surging players |
| `opponent_consistency` | σ of opponent's times | Does Player A do better vs chaotic or consistent opponents? |

> **Rule:** Don't add more features until you've trained V1 and checked SHAP feature importance. Let the model tell you what matters.

---

## 6. Model Training — XGBoost

### Training Data Format

One row per historical match. For S9 validation, use only matches **before** the playoff date.

```
match_id, seed_type, elo_a, elo_b, elo_diff, global_win_rate_a, global_win_rate_b,
avg_time_global_a, avg_time_global_b, consistency_score_a, consistency_score_b,
tilt_factor_a, tilt_factor_b, win_streak_a, win_streak_b,
seed_win_rate_a, seed_win_rate_b, seed_avg_time_a, seed_avg_time_b, seed_time_diff,
h2h_win_rate_a_vs_b, did_a_win
```

### Model Config

```python
from xgboost import XGBClassifier

model = XGBClassifier(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    objective='binary:logistic',   # outputs probability
    eval_metric='logloss',
    use_label_encoder=False
)
```

### Evaluation Metrics

| Metric | What It Measures | Why It Matters |
|---|---|---|
| **Log-Loss** | How accurate are your *probabilities*? | Primary metric. Lower = better. Penalizes confident wrong predictions. |
| **Brier Score** | Mean squared error of probabilities | Similar to Log-Loss but easier to interpret (0 = perfect, 0.25 = random) |
| **Accuracy** | Binary win/loss correctness | Secondary. Less useful because 55% accuracy with good calibration beats 65% accuracy with bad calibration in Monte Carlo. |
| **Calibration Curve** | When you say "70%", does that team win ~70% of the time? | Critical for Monte Carlo — you're using these probabilities as weighted coin flips |

### Validation Strategy

Use **time-series split**, NOT random train/test split:
- Train on the first 80% of the season (by date)
- Test on the last 20% (but still before playoffs)
- This prevents future data leakage

### SHAP Values (Feature Importance)

After training, run SHAP to see what the model actually learned:
```python
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test)
```

**Pearson Correlation:** To prove your thesis ("consistency > speed"), compute the correlation between `consistency_score` and `overall_win_rate` across all players. If negative (lower σ → higher win rate), your thesis holds.

---

## 7. Playoff Format & Simulation Rules

### S9 Playoff Structure (Same for S10)

- **Format:** 16-player single-elimination bracket
- **Rounds:** Ro16, QF, SF, 3rd Place, Grand Final
- **Match format:** Best of 5 (first to 3 seeds) for all rounds, Best of 7 (first to 4) for Grand Final
- **Gameplay:** Both players play the same Minecraft seed simultaneously. First to finish wins that seed.

### Seeding & Opponent Selection

1. Top 12 by Phase Points = Seeds 1-12
2. 4 LCQ qualifiers = Seeds 13-16
3. **Seeds 1-7 CHOOSE their opponents** from a pool of {Seeds 9-16}. Seed 8 gets whoever is left.

**Simplified modeling approach:**
- For S9 validation: **hardcode the actual picks** from the real bracket
- For S10 prediction: **greedy strategy** — each top seed picks the opponent they have the highest P(win) against (from XGBoost predictions)

### Veto System (Seed Type Pick & Ban)

Before each Best of 5/7 match:
1. **Lower seed bans** 1 of 5 seed types
2. **Higher seed bans** 1 of remaining 4
3. **Higher seed picks** the first seed type to play
4. Loser of each round picks the next seed type
5. Already-played seed types can't be re-picked (until after seed 3, when bans/replays are allowed)

**Simplified modeling approach:**
- Each player bans the opponent's **best seed type** (highest `seed_win_rate` for the opponent)
- Each player picks their **own best remaining seed type** when it's their turn

---

## 8. Monte Carlo Bracket Simulation

### The Loop (10,000 iterations)

```
FOR each of 10,000 simulations:
    1. SET UP BRACKET (16 players, seeded)
    2. SIMULATE OPPONENT SELECTION (seeds 1-7 pick)
    3. FOR each match in the bracket (Ro16 → QF → SF → Final):
        a. SIMULATE VETO (ban opponent's best seed type)
        b. FOR each round in the Bo5/Bo7:
            i.  Determine which seed type is being played
            ii. Build the feature vector for this specific matchup on this seed type
            iii. Ask XGBoost: P(Player A wins this round) = ?
            iv. Roll a random number [0, 1]
            v.  If random < P(A wins): A wins this round. Else B wins.
            vi. Update win_streak, check for tilt
        c. Winner = whoever reaches 3 wins (or 4 for Grand Final)
    4. RECORD the tournament winner

AFTER 10,000 simulations:
    Count how many times each player won → tournament win probability
```

### Dynamic Feature Updates Mid-Match

Within a Bo5, after each round:
- **Winner's** `win_streak` increments
- **Loser's** `win_streak` resets to 0
- **Loser's** `tilt_factor` activates (use their post-loss win rate)
- Feed updated features back into XGBoost for the next round's probability

This is what makes the simulation realistic — momentum and psychology shift mid-match.

---

## 9. Validation — Proving It Works (S9)

### What to Compare Against

The S9 Playoffs already happened (Jan 11-19, 2026). You know the actual bracket results. Compare your simulation output to reality:

| Metric | How to Measure |
|---|---|
| **Match-level accuracy** | For each actual S9 match, did your model's favored player (>50% probability) win? |
| **Round-level accuracy** | Within each Bo5, how well did round-by-round probabilities hold up? |
| **Tournament winner** | Did your Monte Carlo's #1 most-probable winner match the actual champion? |
| **Top-4 prediction** | Were 3 or 4 of your predicted semifinalists correct? |
| **Calibration** | When you said "70% chance," did that player actually win ~70% of those matchups? |
| **Log-Loss on playoff matches** | Overall probability accuracy across all playoff games |

### The "Baseline" to Beat

A naive model that only uses Elo difference (higher Elo wins) is your **baseline**. If your full model (with consistency, tilt, seed-type features) produces better Log-Loss than the Elo-only model, you've **proven** that your engineered features add value. This is the key slide for any presentation.

---

## 10. S10 Prediction

Once S9 validation proves the model works:

1. Re-pull data for Season 10 (same pipeline, `season=10`)
2. Identify the 16 playoff players from `predPhasePoint` (if season is ongoing) or `phasePoint` (if season ended)
3. Re-train XGBoost on all available S10 ranked data (up to playoff start)
4. Run the Monte Carlo simulator with S10 players
5. Output: probabilistic bracket forecast on the Streamlit dashboard

---

## 11. Tools & Libraries Reference

| Tool | Purpose |
|---|---|
| `requests` | Hit the MCSR API |
| `pandas` | Data cleaning, CSV operations, feature engineering |
| `numpy` | Math (std dev, rolling windows) |
| `xgboost` | The prediction model |
| `scikit-learn` | Train/test split, metrics (log_loss, brier_score_loss), calibration curves |
| `shap` | Feature importance visualization |
| `matplotlib` / `seaborn` | Plots, calibration curves, distributions |
| `streamlit` | Dashboard / web app for displaying results |
| `scipy.stats` | Pearson correlation (consistency vs win rate thesis) |
| `json` / `os` | File caching |

---

## 12. The Elevator Pitch

*"I built a predictive engine and Monte Carlo simulator for 1v1 Minecraft Speedrunning tournaments. I pulled thousands of matches via REST API and engineered features around human psychology — specifically calculating a player's Rolling Consistency (variance in finish times) and Tilt Factor (performance drops after losses). I trained an XGBoost model to predict individual match probabilities, evaluated it using Log-Loss, and then fed those probabilities into a Monte Carlo engine that simulates entire tournament brackets 10,000 times. Ultimately, the project statistically proves that reliability and low variance are better predictors of winning than peak speed — a concept that directly translates to financial risk modeling and telecom network stability."*

---

## 13. Build Order Checklist

1. [ ] `config.py` — Constants: API base URL, season number, playoff epoch cutoff, 16 player UUIDs
2. [ ] `src/api_client.py` — `cached_get()`, `get_player_matches()`, `get_h2h()`
3. [ ] `src/collect.py` — Pull all data, concatenate, save to `data/raw/` and `data/processed/all_matches.csv`
4. [ ] `src/collect.py --validate` — Sanity checks (match counts, seed distribution, forfeit %, date range)
5. [ ] `src/features.py` — Engineer all features → `player_features.csv`, `player_seedtype_features.csv`, `matchup_training_data.csv`
6. [ ] `src/model.py` — Train XGBoost, evaluate Log-Loss/Brier, generate SHAP plot
7. [ ] Baseline comparison — Train Elo-only model, prove your features improve Log-Loss
8. [ ] Pearson correlation — Prove consistency (low σ) correlates with higher win rate
9. [ ] `src/simulator.py` — Monte Carlo loop: bracket → veto → Bo5/Bo7 → 10,000 runs
10. [ ] S9 validation — Compare simulation output to actual S9 bracket results
11. [ ] `app.py` — Streamlit dashboard: bracket visualization, win probabilities, feature importance
12. [ ] S10 prediction — Re-run pipeline on S10 data
