# FF Draft Room - Architecture Decisions

## ADR-001: Streamlit as UI Framework

**Date**: 2026-03-22
**Status**: Accepted

### Context
Need a local Python UI for a data-heavy fantasy football tool. Options evaluated: PyQt5/PySide6 (native desktop), Flask+HTML (full web stack), Streamlit (Python-native browser app).

### Decision
Use Streamlit for the UI layer.

### Rationale
- Pure Python — no HTML/CSS/JS required
- Built-in data table, chart, and filter components match our use case exactly
- Runs in browser (modern look) without web development overhead
- `@st.cache_data` handles our CSV-heavy workload efficiently
- Hot reload during development speeds iteration
- Dark theme configurable via `config.toml`

### Alternatives Considered
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| PyQt5 | Native desktop, true drag-and-drop | "Looks like PyQt5", heavier development | Rejected |
| Flask + HTML | Full control | Need to write HTML/CSS/JS | Rejected |
| Streamlit | Python-native, fast, modern in browser | Limited true drag-and-drop | **Selected** |

### Consequences
**Positive:**
- Fastest path from data to interactive UI
- Single language (Python) for entire app
- Easy to extend with new pages

**Negative:**
- No true drag-and-drop for tier/ranking reordering — must use workarounds (selectbox-based reordering or number input rank assignment)
- Streamlit reruns entire script on interaction — must use `@st.cache_data` aggressively

---

## ADR-002: JSON Files for Rankings Persistence

**Date**: 2026-03-22
**Status**: Accepted

### Context
User rankings, tier assignments, and notes need to persist between sessions. Options: SQLite database, JSON files, pickle files.

### Decision
Use JSON files in `data/rankings/` directory for all user-created ranking profiles.

### Rationale
- Human-readable — user can inspect or manually edit profiles
- No database setup required
- Easy to back up, share, or version control
- Simple read/write with Python's built-in `json` module
- Profiles are small (< 200 players per profile, ~50KB max)

### Alternatives Considered
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| SQLite | Queryable, robust | Overkill for file sizes involved | Rejected |
| JSON files | Simple, portable, human-readable | No concurrent access (not needed) | **Selected** |
| Pickle | Fast, Pythonic | Not human-readable, version fragile | Rejected |

### Consequences
**Positive:**
- Zero setup — works out of the box
- Profiles portable between machines

**Negative:**
- No query capability — load entire profile into memory (acceptable at this scale)

---

## ADR-003: FantasyPros CSV as Sole Data Source

**Date**: 2026-03-22
**Status**: Accepted

### Context
Need historical half-PPR fantasy scoring data for 2020–2025. Options: hardcode approximations, scrape live data, use pre-downloaded CSV exports.

### Decision
Use exclusively FantasyPros half-PPR season leaders CSV exports as the data source. No approximations, no fallbacks, no hardcoded data.

### Rationale
- Data integrity — verified from authoritative source
- Already collected: 24 CSV files (4 positions × 6 years)
- Reproducible — user can re-export if needed
- No external API calls at runtime — fully offline
- The research phase confirmed this is the correct approach

### Consequences
**Positive:**
- 100% verified data, no guesswork
- App works fully offline
- Easy to add future years by dropping in new CSV

**Negative:**
- Missing columns (ADP, team record, off/def rank) — to be added manually when needed
- App warns gracefully if a CSV file is missing

---

## ADR-004: VOR Replacement Level Thresholds

**Date**: 2026-03-22
**Status**: Accepted

### Context
VOR (Value Over Replacement) requires defining the "replacement level" player at each position — the player you'd get off waivers if you missed the position entirely.

### Decision
Default replacement levels for 10-team half-PPR, standard roster:
- QB: Rank 13 (QB on the streaming wire)
- RB: Rank 25 (RB2 on a weak team)
- WR: Rank 35 (WR3/flex on weak team)
- TE: Rank 13 (streaming TE)

These are configurable per ranking profile.

### Rationale
Standard industry thresholds for 10-team leagues with 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX.
Matches methodology used by Fantasy Footballers and FantasyPros consensus.

### Consequences
**Positive:**
- Sensible defaults for the target league format
- User can adjust per profile if needed

**Negative:**
- VOR is projection-based; historical VOR is informational only

---

## Template for New Decisions

```markdown
## ADR-XXX: Title

**Date**: YYYY-MM-DD
**Status**: Proposed/Accepted/Deprecated/Superseded

### Context
What is the issue motivating this decision?

### Decision
What are we doing?

### Rationale
- Reason 1
- Reason 2

### Alternatives Considered
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|

### Consequences
**Positive:**
- Benefit

**Negative:**
- Tradeoff
```

## Key Principles

1. **No approximations**: All player data must come from verified CSV exports
2. **Local first**: No cloud dependencies, no API calls at runtime
3. **Streamlit patterns**: Cache data aggressively, use session state correctly
4. **Graceful degradation**: Missing files warn the user, never crash the app
