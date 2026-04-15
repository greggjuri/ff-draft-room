# Init-10: Draggable Tier Boundaries

**Date**: 2026-04-15
**Status**: Draft
**Phase**: 1d — Polish

---

## Problem Statement

Tier boundaries are currently fixed by how players are seeded from CSV data.
The only way to move a player between tiers is to repeatedly press ▲▼ until
they cross the boundary — a friction-heavy workflow when prepping multiple
positions before a draft. The user needs to be able to grab a tier divider
and pull it up or down to quickly redistribute players between tiers.

---

## Proposed Solution

Replace the static `— TIER N —` header in `TierGroup.jsx` with a draggable
separator line rendered **between** tier groups. Dragging it down moves the
last player of the upper tier into the lower tier. Dragging it up moves the
first player of the lower tier into the upper tier. Movement snaps per player
row — no pixel-smooth sliding, just clean one-player-at-a-time reassignment.

A new backend utility function and endpoint handle the tier update. The
frontend handles all drag UX and calls the API on each snap.

---

## Architecture Decision: ADR-009

**ADR-001** (Streamlit era) stated "no drag-and-drop". That decision was
specifically about player reordering via drag — the concern was Streamlit
complexity, now irrelevant. Tier boundary dragging is a distinct, narrower
affordance: a single vertical axis, snapping to discrete rows, affecting
only two adjacent tiers. A new ADR explicitly carves this out.

**ADR-009: Draggable Tier Boundaries** (to be written alongside this PRP)
- Drag-and-drop for player reordering remains out of scope (▲▼ buttons stay)
- Tier boundary drag is limited to War Room mode only
- Drag direction is vertical only; each snap unit = one player row

---

## Data Model

No schema changes. Each player already stores `tier` as an integer field.
The boundary drag simply updates `tier` on the player being moved.

**Example — drag Tier 1 / Tier 2 boundary DOWN one row in QB:**

Before:
```
Tier 1: Josh Allen (rank 1), Lamar Jackson (rank 2), Jalen Hurts (rank 3)
Tier 2: Joe Burrow (rank 4), C.J. Stroud (rank 5)
```

After:
```
Tier 1: Josh Allen (rank 1), Lamar Jackson (rank 2), Jalen Hurts (rank 3), Joe Burrow (rank 4)
Tier 2: C.J. Stroud (rank 5)
```

`position_rank` values do **not change** — only the `tier` field on Joe Burrow
flips from 2 → 1. This keeps the operation atomic and reversible.

---

## Backend Changes

### New utility function — `backend/utils/rankings.py`

```python
def set_player_tier(
    profile: dict, position: str, position_rank: int, new_tier: int
) -> dict:
    """Reassign a single player's tier without changing their rank.

    Returns a new profile dict — does not mutate input.
    Raises ValueError if the player is not found.
    """
```

No renumbering. No cascade. One player's `tier` field changes. This is
intentionally minimal — tier boundaries are implicit (the gap between
players with different tier values), so one player update is all that's
needed per snap.

### New API endpoint — `backend/routers/rankings.py`

```
PUT /api/rankings/{position}/{rank}/tier
Body: { "tier": N }
Response: list[dict]  ← updated position players
```

Validation:
- `position` must be in `POSITIONS`
- `rank` must exist in the position's player list
- `tier` must be a positive integer
- `tier` must be adjacent to the player's current tier (±1 only) — prevents
  accidental jumps from a buggy frontend call

**Route registration**: this route must be registered BEFORE `/{position}`
to avoid FastAPI treating `tier` as a position match. In practice it's a
sub-route of `/{position}/{rank}` so ordering relative to `/{position}`
alone is not an issue — but note it for completeness.

### New request model

```python
class SetTierRequest(BaseModel):
    tier: int
```

### Tests — `tests/test_rankings.py`

New test cases for `set_player_tier`:
- Reassigns tier correctly, returns new profile
- Does not mutate input profile
- Raises `ValueError` on unknown player
- Does not change `position_rank`
- Does not affect other players

New test cases for the endpoint (integration via `TestClient`):
- `PUT /api/rankings/QB/1/tier` with `{ "tier": 2 }` → 200, correct tier
- Invalid position → 422
- Non-existent rank → 400
- Non-adjacent tier (`tier: 5` when current is `1`) → 400

---

## Frontend Changes

### New component — `TierSeparator.jsx`

A thin draggable line rendered **between** adjacent tier groups. Not inside
`TierGroup` — rendered by `PositionColumn` in the gap between groups.

**Visual design:**
- At rest: `2px` horizontal rule, color `#1E3A5F` (matches existing column
  dividers), centered grip icon `⠿` in Honolulu Blue `#0076B6`
- On hover: grip brightens, cursor becomes `ns-resize`
- While dragging: separator highlighted in `#0076B6`, opacity 0.8

**Props:**
```jsx
<TierSeparator
  position={position}          // "QB" | "RB" | "WR" | "TE"
  upperTier={tierNum}          // tier above this boundary
  lowerTier={tierNum + 1}      // tier below this boundary
  upperCount={players.length}  // players in upper tier (for empty-tier guard)
  lowerCount={players.length}  // players in lower tier (for empty-tier guard)
  onBoundaryMove={fn}          // (position, direction) => void
  isDraft={bool}               // hidden when true
/>
```

### Drag behaviour

`onMouseDown` on the separator starts a drag session. The component tracks
cumulative Y delta against a `rowHeight` constant (measured from a player
row `ref` in `PositionColumn`).

Each time `|deltaY| >= rowHeight`:
- `deltaY > 0` (dragging down) → call `onBoundaryMove(position, 'down')`
- `deltaY < 0` (dragging up) → call `onBoundaryMove(position, 'up')`
- Reset delta accumulator

`onMouseUp` / `onMouseLeave` ends the drag session.

**Touch support**: `onTouchStart` / `onTouchMove` / `onTouchEnd` mirrors the
mouse handlers using `touches[0].clientY` — important for mobile draft-day
use on `ff.jurigregg.com`.

### Empty tier guard

Before calling `onBoundaryMove`, the frontend checks:
- Dragging **down**: `upperCount > 1` — prevent upper tier going to 0 players
- Dragging **up**: `lowerCount > 1` — prevent lower tier going to 0 players

If either check fails: no API call, no visual snap. Optionally add a brief
shake animation on the separator to indicate the limit has been reached.

### `PositionColumn.jsx` changes

- Compute `rowHeight` via a `ref` on the first `PlayerRow` rendered
- Render `<TierSeparator>` between each pair of adjacent tier groups
- Handle `onBoundaryMove(position, direction)`:
  1. Identify the target player (last of upper tier on 'down', first of lower
     tier on 'up')
  2. Compute `newTier` (current ± 1)
  3. Call `PUT /api/rankings/{position}/{rank}/tier`
  4. On success: update local state via the existing `onRankingsUpdate` pattern
  5. Mark dirty (unsaved indicator)

### `api/rankings.js` — new function

```js
export async function setPlayerTier(position, rank, tier, token) {
  // PUT /api/rankings/{position}/{rank}/tier
}
```

Follows the existing pattern: accepts `token`, returns updated player list,
throws on non-2xx.

### Draft Mode

`TierSeparator` renders `null` when `isDraft={true}`. No other changes needed
in Draft Mode.

---

## Success Criteria

- [ ] A draggable separator line appears between every pair of adjacent tiers
      in all four position columns
- [ ] Dragging down one row moves the first player of the lower tier into
      the upper tier; dragging up does the reverse
- [ ] Movement snaps per row — one player reassigned per snap unit
- [ ] `position_rank` values are unchanged after a tier reassignment
- [ ] Empty tier is impossible — separator stops responding at the 1-player
      limit in either direction
- [ ] Separator is hidden in Draft Mode
- [ ] Touch drag works (mobile / `ff.jurigregg.com`)
- [ ] Unsaved indicator appears after any tier reassignment
- [ ] All 64 existing tests continue to pass
- [ ] New tests: ≥ 5 unit tests for `set_player_tier`, ≥ 3 endpoint tests
- [ ] `ruff check backend/ tests/` — zero errors
- [ ] No file exceeds 500 lines

---

## Files to Create / Modify

```
backend/utils/rankings.py          MODIFY — add set_player_tier()
backend/routers/rankings.py        MODIFY — add PUT /{position}/{rank}/tier
frontend/src/api/rankings.js       MODIFY — add setPlayerTier()
frontend/src/components/
  PositionColumn.jsx               MODIFY — render TierSeparator, handle move
  PositionColumn.css               MODIFY — separator gap/layout styles
  TierSeparator.jsx                NEW
  TierSeparator.css                NEW
tests/test_rankings.py             MODIFY — new set_player_tier tests
tests/test_rankings_api.py         MODIFY (or test_profile_management.py)
                                           — new endpoint tests
docs/DECISIONS.md                  MODIFY — add ADR-009
docs/TASK.md                       MODIFY — add to in-progress, update backlog
```

---

## Out of Scope

- Drag-to-reorder players (▲▼ buttons remain the reorder mechanism)
- Creating new tiers or deleting empty tiers
- Merging tiers
- Any visual changes to the tier header label itself
- Multi-row drag (dragging more than one player at a time)
