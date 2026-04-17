# FF Draft Room - Testing Standards

## Testing Pyramid

```
        /\
       /  \     Manual browser UI (each PRP)
      /----\
     /      \   API integration (curl verification)
    /--------\
   /          \ Unit — utils/ functions (many, automated)
  --------------
```

## When to Test What

| Test Type | When | Tools |
|-----------|------|-------|
| Unit | Every change to `backend/utils/` | pytest |
| API | After each backend PRP | curl + uvicorn |
| Manual UI | After each frontend PRP | Browser at localhost:5173 |

## Automated Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=backend --cov-report=term-missing

# Run specific module
pytest tests/test_rankings.py -v

# Run with short output
pytest tests/ -q
```

**Current test count**: 76 passing, 1 skipped (vor placeholder)

**Minimum Coverage**: 80% for `backend/utils/`

## Test Files

```
tests/
├── conftest.py                  # sys.path + storage fixture (LocalStorage)
├── test_data_loader.py          # 8 tests — CSV loading + normalization
├── test_rankings.py             # 32 tests — seed, CRUD, swap, add, delete, set_player_tier
├── test_profile_management.py   # 21 tests — list, save-as, load, reset, seed, rename, delete
├── test_storage.py              # 15 tests — LocalStorage, S3Storage (moto), get_storage factory
└── test_vor.py                  # Future (1 skipped placeholder)
```

## Manual UI Testing

Required after every frontend PRP. Run both servers:

### Setup
```bash
# Terminal 1
source .venv/bin/activate
uvicorn backend.main:app --reload

# Terminal 2
cd frontend && npm run dev
# Open http://localhost:5173
```

### Checklist — War Room Core
- [ ] 4 columns visible: QB / RB / WR / TE
- [ ] Correct player counts: QB 30 / RB 50 / WR 50 / TE 30
- [ ] Tier headers visible with alternating player name backgrounds
- [ ] ▲▼ reorders players, ranks update immediately
- [ ] ▲ disabled on rank 1, ▼ disabled on last rank
- [ ] Click player name → notes dialog, pre-filled
- [ ] Save notes → 📝 appears
- [ ] [+ Position · Tier N] → add dialog, validation works
- [ ] [×] → confirm dialog, delete removes player
- [ ] ● UNSAVED indicator after changes
- [ ] SAVE clears indicator

### Checklist — Profile Management
- [ ] SAVE AS → dialog, saves named profile
- [ ] LOAD → lists profiles, loads selected
- [ ] LOAD → warns if unsaved changes
- [ ] RESET → restores from seed.json or CSV
- [ ] ★ SET DEFAULT → writes seed.json
- [ ] Profile name shown in header

### Checklist — Draft Mode
- [ ] Click DRAFT toggle → draft mode, controls hidden
- [ ] Status dots visible on all players
- [ ] Click dot → cycles undrafted → mine (green) → other (purple)
- [ ] Exit with picks → confirm dialog
- [ ] Exit without picks → immediate
- [ ] Notes dialog disabled in draft mode

### Checklist — Search
- [ ] Search box visible in header (both modes)
- [ ] Type "allen" → dropdown shows matches grouped by position
- [ ] Matching text bolded in results
- [ ] Click result → scrolls to player, blue outline highlight
- [ ] Escape clears search
- [ ] × button clears search
- [ ] "zzzzz" → "No players found"
- [ ] Header sticks to top on scroll

### Checklist — Tier Drag
- [ ] Draggable separator visible between adjacent tiers
- [ ] Drag down → first player of lower tier joins upper tier
- [ ] Drag up → last player of upper tier joins lower tier
- [ ] Separator stops at 1-player tier (no empty tiers)
- [ ] Separator hidden in Draft Mode
- [ ] Touch drag works on mobile

### Checklist — Profile Rename/Delete
- [ ] Load dialog shows Rename + Delete on each profile row
- [ ] Active profile shows ● indicator
- [ ] Rename → inline input → Save → list refreshes, header updates if active
- [ ] Delete → inline confirm → removes profile
- [ ] Delete active profile → header resets, data reloads

### Checklist — Visual Polish
- [ ] Column headers show position-specific colors (QB gold, RB green, WR blue, TE orange)
- [ ] Depth sub-label shown below position label
- [ ] Tier headers have left-border in position color shades
- [ ] Team logos visible inside player name boxes (right-aligned)
- [ ] Team color gradient visible on right portion of name boxes
- [ ] Free agents have solid background, no logo, no gradient

### Checklist — Error Handling
- [ ] Backend down → error banner shown
- [ ] Duplicate add → inline error in dialog
- [ ] Empty name/team → inline error

## API Integration Testing (curl)

```bash
BASE="http://localhost:8000/api"

# Health
curl -s http://localhost:8000/health

# Rankings CRUD
curl -s $BASE/rankings
curl -s $BASE/rankings/QB
curl -s -X POST $BASE/rankings/QB/reorder -H "Content-Type: application/json" -d '{"rank_a":1,"rank_b":2}'
curl -s -X POST $BASE/rankings/QB/add -H "Content-Type: application/json" -d '{"name":"Test","team":"TST","tier":1}'
curl -s -X DELETE $BASE/rankings/QB/31
curl -s -X PUT $BASE/rankings/QB/1/notes -H "Content-Type: application/json" -d '{"notes":"Test"}'
curl -s -X POST $BASE/rankings/save

# Profile management
curl -s $BASE/rankings/profiles
curl -s -X POST $BASE/rankings/save-as -H "Content-Type: application/json" -d '{"name":"Test Profile"}'
curl -s -X POST $BASE/rankings/load -H "Content-Type: application/json" -d '{"name":"Test Profile"}'
curl -s -X POST $BASE/rankings/set-default
curl -s -X POST $BASE/rankings/reset
```

## Testing Patterns

### Unit Test Structure
```python
import pytest
from utils.rankings import seed_rankings, swap_players

def test_swap_exchanges_ranks(sample_profile):
    result = swap_players(sample_profile, "QB", 2, 3)
    qbs = get_position_players(result, "QB")
    assert qbs[1]["name"] == "P3"

def test_swap_does_not_mutate_input(sample_profile):
    original = copy.deepcopy(sample_profile)
    swap_players(sample_profile, "QB", 2, 3)
    assert sample_profile == original
```

### Profile Test Structure
```python
def test_save_as_creates_file(tmp_path):
    profile = _sample_profile()
    result = save_profile_as(profile, "Mock Draft 1", rankings_dir=tmp_path)
    assert result["saved"] is True
    assert (tmp_path / "Mock_Draft_1.json").exists()
```

## Pre-Commit Checklist

- [ ] `pytest tests/ -q` passes (76+)
- [ ] `ruff check backend/ tests/` — no errors
- [ ] `cd frontend && npx vite build` — no errors
- [ ] Backend starts: `uvicorn backend.main:app --reload`
- [ ] Manual test of affected feature completed

---

*Last updated: 2026-04-17 (tier drag, visual polish, team logos/gradients, profile rename/delete)*
