# FF Draft Room - Testing Standards

## Testing Pyramid

```
        /\
       /  \     Manual Streamlit UI (each page after PRP)
      /----\
     /      \   Integration (data loading + rendering)
    /--------\
   /          \ Unit — utils/ functions (many, automated)
  --------------
```

## When to Test What

| Test Type | When | Tools |
|-----------|------|-------|
| Unit | Every change to `app/utils/` | pytest |
| Integration | After each PRP execution | `streamlit run` + manual |
| Manual UI | After each page feature | Browser inspection |

## Automated Tests

```bash
# Run all tests with coverage
cd ff-draft-room && pytest tests/ --cov=app --cov-report=term-missing

# Run specific module
pytest tests/test_data_loader.py -v

# Run with short output
pytest tests/ -q
```

**Minimum Coverage**: 80% for `app/utils/`  
Coverage for `app/pages/` and `app/components/` is manual only (Streamlit UI is hard to unit test).

## Manual Integration Testing

Required after every PRP execution. Run the app and verify:

### Setup
```bash
cd ff-draft-room
streamlit run app/main.py
# Open http://localhost:8501
```

### Checklist — Every PRP
- [ ] App starts without errors in terminal
- [ ] Page loads without red Streamlit error box
- [ ] Feature works end-to-end (happy path)
- [ ] Error states handled gracefully (missing file, bad data)

### Checklist — History Browser
- [ ] All positions load (QB, RB, WR, TE)
- [ ] All years load (2020–2025)
- [ ] Sort by any column works
- [ ] Search/filter narrows results correctly
- [ ] Row count matches expected (QB: 20, RB: 40, WR: 50, TE: 20)
- [ ] "All years" view combines all correctly

### Checklist — War Room Rankings
- [ ] Loads default baseline on first open
- [ ] Can reorder players
- [ ] Tier assignment saves correctly
- [ ] Notes field saves and persists
- [ ] Save profile writes JSON to `data/rankings/`
- [ ] Load profile restores state correctly
- [ ] Profile list shows all saved profiles

### Checklist — VOR / Analysis
- [ ] VOR scores calculated for all positions
- [ ] Replacement level thresholds produce sensible results
- [ ] Chart renders without error
- [ ] Positive VOR = above replacement, negative = below

## Testing Patterns

### Unit Test Structure
```python
# tests/test_data_loader.py
import pytest
import pandas as pd
from app.utils.data_loader import load_players, normalize_dataframe

def test_load_players_returns_dataframe(tmp_path):
    """load_players returns a DataFrame with correct columns."""
    # Arrange — create minimal CSV
    csv = tmp_path / "QB_2024.csv"
    csv.write_text('"#","Player","Pos","Team","GP","AVG","TTL"\n"1","Josh Allen","QB","BUF","17","22.0","374.6"\n')
    
    # Act
    df = load_players("QB", 2024, data_dir=tmp_path)
    
    # Assert
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["rank", "name", "team", "position", "year", "gp", "ppg", "total_pts"]
    assert len(df) == 1

def test_load_players_missing_file_returns_empty(tmp_path):
    """load_players returns empty DataFrame when file not found."""
    df = load_players("QB", 1990, data_dir=tmp_path)
    assert df.empty

def test_normalize_dataframe_correct_dtypes():
    """normalize_dataframe enforces correct column types."""
    raw = pd.DataFrame({
        "#": ["1"], "Player": ["Josh Allen"], "Team": ["BUF"],
        "GP": ["17"], "AVG": ["22.0"], "TTL": ["374.6"]
    })
    df = normalize_dataframe(raw, position="QB", year=2024)
    assert df["gp"].dtype == int
    assert df["ppg"].dtype == float
    assert df["total_pts"].dtype == float
```

### VOR Unit Tests
```python
# tests/test_vor.py
from app.utils.vor import calculate_vor, get_replacement_level

def test_vor_positive_for_top_players():
    """Top players should have positive VOR."""
    players = [{"name": f"Player {i}", "total_pts": 400 - i*10} for i in range(20)]
    vor_scores = calculate_vor(players, position="QB", replacement_rank=13)
    assert vor_scores[0]["vor"] > 0
    assert vor_scores[12]["vor"] == 0   # replacement level player

def test_vor_negative_below_replacement():
    """Players below replacement rank have negative VOR."""
    players = [{"name": f"Player {i}", "total_pts": 400 - i*10} for i in range(20)]
    vor_scores = calculate_vor(players, position="QB", replacement_rank=13)
    assert vor_scores[13]["vor"] < 0
```

### Rankings Unit Tests
```python
# tests/test_rankings.py
import json
from app.utils.rankings import save_profile, load_profile, list_profiles

def test_save_and_load_profile_roundtrip(tmp_path):
    """Profile saved to JSON loads back identically."""
    profile = {
        "name": "Test Profile",
        "players": [{"rank": 1, "name": "Josh Allen", "tier": 1}]
    }
    save_profile(profile, "test", rankings_dir=tmp_path)
    loaded = load_profile("test", rankings_dir=tmp_path)
    assert loaded["name"] == profile["name"]
    assert loaded["players"] == profile["players"]

def test_list_profiles_returns_names(tmp_path):
    """list_profiles returns names of all saved profiles."""
    (tmp_path / "profile1.json").write_text('{"name": "P1"}')
    (tmp_path / "profile2.json").write_text('{"name": "P2"}')
    names = list_profiles(rankings_dir=tmp_path)
    assert set(names) == {"profile1", "profile2"}
```

## Common Bugs to Watch For

| Bug | How to Detect | Fix |
|-----|--------------|-----|
| CSV column mismatch | KeyError on df["TTL"] | Check FantasyPros export format per year |
| Streamlit rerun loop | Infinite spinner | Check for state mutation outside callbacks |
| Cache stale after CSV update | Old data showing | `st.cache_data.clear()` or restart |
| Session state lost on page nav | Rankings reset | Initialize state in `main.py`, not page files |
| Float formatting in table | `374.600000` | Use `.round(1)` or `.map("{:.1f}".format)` |
| Plotly chart not rendering | Blank space | Check for empty DataFrame before calling chart |

## Debugging Workflow

1. **Reproduce**: Confirm bug exists with minimal steps
2. **Terminal**: Check `streamlit run` output for Python tracebacks
3. **Browser**: Check browser console (F12) for JS errors
4. **Data inspection**: Add `st.dataframe(df.head())` temporarily
5. **State inspection**: Add `st.write(st.session_state)` temporarily
6. **Fix**: Minimal change
7. **Clean up**: Remove debug output before committing

## Pre-Commit Checklist

- [ ] `pytest tests/ -q` passes
- [ ] Coverage ≥ 80% for `app/utils/`
- [ ] `ruff check app/ tests/` — no errors
- [ ] App starts cleanly: `streamlit run app/main.py`
- [ ] Manual test of affected page completed
- [ ] Debug output removed (`st.write`, `print`)
