# FF Draft Room 🏈

A local Python/Streamlit fantasy football draft preparation and live-draft tracking tool.

Built for 10-team half-PPR Yahoo leagues. Runs entirely on your machine — no cloud, no subscriptions, no ads.

## Features

### War Room (Pre-Draft)
- **Historical Stats Browser** — 6 years of verified half-PPR data (2020–2025), all positions, sortable
- **Rankings Editor** — Build and save custom ranking profiles from historical baselines
- **Tier Builder** — Assign tier breaks visually, see positional scarcity at a glance
- **VOR Calculator** — Value Over Replacement scores for smarter draft decisions

### Live Draft *(coming soon)*
- Snake draft tracker with pick clock
- Best available board updating in real time
- Positional needs and scarcity alerts

## Data

All player data sourced from [FantasyPros](https://www.fantasypros.com) half-PPR season leaders exports.

| Position | Per Year | Years | Total |
|----------|----------|-------|-------|
| QB | 20 | 2020–2025 | 120 |
| RB | 40 | 2020–2025 | 240 |
| WR | 50 | 2020–2025 | 300 |
| TE | 20 | 2020–2025 | 120 |
| **Total** | | | **780** |

## Requirements

- Python 3.11+
- macOS (tested on M1) or any Unix system

## Installation

```bash
# Clone the repo
git clone https://github.com/greggjuri/ff-draft-room.git
cd ff-draft-room

# Install dependencies
pip install -r requirements.txt

# Add your FantasyPros CSV exports
# Copy files to data/players/ following the naming convention:
# QB_2020.csv, QB_2021.csv ... QB_2025.csv
# RB_2020.csv ... RB_2025.csv
# WR_2020.csv ... WR_2025.csv
# TE_2020.csv ... TE_2025.csv

# Start the app
streamlit run app/main.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## CSV Format

This app expects FantasyPros half-PPR season leaders exports. Export directly from:  
`fantasypros.com → Fantasy Football → Leaders → [Position] → Half PPR → Export CSV`

Expected columns: `#, Player, Pos, Team, GP, [week columns], AVG, TTL`

## Development

This project uses the [CE workflow](https://github.com/greggjuri/CE-templates) — Claude.ai for planning, Claude Code for execution.

```bash
# Run tests
pytest tests/ --cov=app --cov-report=term-missing

# Lint
ruff check app/ tests/

# Generate a new feature PRP (in Claude Code)
/generate-prp initials/init-{feature}.md

# Execute a PRP (in Claude Code)
/execute-prp prps/prp-{feature}.md
```

See `docs/PLANNING.md` for architecture and `docs/TASK.md` for current status.

## Project Structure

```
ff-draft-room/
├── app/
│   ├── main.py              # Streamlit entry point
│   ├── pages/               # War Room, History, Analysis, Live Draft
│   ├── components/          # Reusable UI components
│   └── utils/               # Data loading, VOR, rankings logic
├── data/
│   ├── players/             # FantasyPros CSV exports (add yours here)
│   └── rankings/            # Your saved ranking profiles (JSON)
├── docs/                    # PLANNING, TASK, DECISIONS, TESTING
├── initials/                # Feature specs
├── prps/                    # Implementation plans
└── tests/                   # pytest unit tests
```

## License

Personal use. Not affiliated with Yahoo, FantasyPros, or the NFL.
