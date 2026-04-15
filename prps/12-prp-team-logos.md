# PRP-012: Team Logos on Player Name Boxes

**Created**: 2026-04-15
**Initial**: `initials/12-init-team-logos.md`
**Status**: Complete

---

## Overview

### Problem Statement
Player team identity is shown as a small muted text abbreviation in its
own grid column outside the name box. It's functional but bland — the
board has no visual team identity beyond three letters of text.

### Proposed Solution
Replace the external team abbreviation text with a small NFL team logo
image rendered inside the player name box, right-aligned. Logos sourced
from ESPN CDN at runtime. A new utility maps FantasyPros abbreviations
to ESPN URLs, handling the JAC→jax mismatch and free agent cases.

### Success Criteria
- [ ] Each player name box shows a team logo at its right edge (18px tall)
- [ ] Free agent players (FA, --, empty) show no logo, no broken icon
- [ ] Unknown/bad abbreviations fall back silently via `onError`
- [ ] Player name text truncates with ellipsis before overlapping logo
- [ ] External team abbreviation text removed from all row variants
- [ ] War room grid: 5 columns (was 6, team column removed)
- [ ] Draft row grid: 3 columns (was 4, team column removed)
- [ ] Logos visible on draft mode green (mine) and purple (other) backgrounds
- [ ] `cd frontend && npx vite build` — no errors
- [ ] No regressions in reorder, notes, add, delete, save/load, search, draft

---

## Context

### Related Documentation
- `initials/12-init-team-logos.md` — Full design spec
- `docs/DECISIONS.md` — ADR-003 notes "no external API calls" targets
  live stats data, not static image assets

### Dependencies
- **Required**: PRP 05 (React frontend), PRP 11 (visual polish — current PlayerRow shape)
- **External**: ESPN CDN for logo images (runtime, browser-cached)

### Files to Create/Modify
```
# NEW
frontend/src/utils/teamLogos.js             # getLogoUrl() utility

# MODIFIED
frontend/src/components/PlayerRow.jsx       # Logo inside name box, remove team span
frontend/src/components/PlayerRow.css       # Grid update, logo styles, remove .player-team
```

No backend changes. No new tests. No new components.

---

## Technical Specification

### Logo URL Utility (`frontend/src/utils/teamLogos.js`)

```js
const OVERRIDES = { JAC: 'jax' }
const FREE_AGENT_TOKENS = new Set(['FA', '--', '', 'FA '])

export function getLogoUrl(team) {
  if (!team || FREE_AGENT_TOKENS.has(team.trim())) return null
  const abbrev = OVERRIDES[team.toUpperCase()] ?? team.toLowerCase()
  return `https://a.espncdn.com/i/teamlogos/nfl/500/${abbrev}.png`
}
```

Returns `null` for free agents. Callers guard against null before
rendering `<img>`.

### PlayerRow.jsx Changes

1. Import `getLogoUrl` from `../utils/teamLogos`
2. Compute `logoUrl = getLogoUrl(player.team)` at top of component
3. Define `logoEl` — an `<img>` with `onError` handler that hides itself
4. In war room name button: wrap name text in `<span className="player-name-text">`,
   add `{logoEl}` after it
5. In draft row name span: same treatment
6. Remove `<span className="player-team">{player.team}</span>` from both returns

### PlayerRow.css Changes

1. War room grid: `24px 24px 24px 1fr 36px 24px` → `24px 24px 24px 1fr 24px`
   (remove the 36px team column)
2. Draft grid: `12px 24px 1fr 36px` → `12px 24px 1fr`
   (remove the 36px team column)
3. Add `justify-content: space-between` and `gap: 6px` to `.player-name-btn`
4. Add `.player-name-text` with flex overflow/ellipsis
5. Add `.player-team-logo` — 18px height, opacity 0.72, flex-shrink 0
6. Remove `.player-team` rule entirely

### Layout After Changes

War room: `[ ▲ ][ ▼ ][ rank ][ name text ········· logo ][ × ]`
Draft:    `[ ● ][ rank ][ name text ··········· logo ]`

---

## Implementation Steps

### Step 1: Create teamLogos utility
**Files**: `frontend/src/utils/teamLogos.js`

Create the utility directory and file with `getLogoUrl()`.

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds (new file imported nowhere yet is fine)

---

### Step 2: Update PlayerRow JSX
**Files**: `frontend/src/components/PlayerRow.jsx`

1. Import `getLogoUrl`
2. Add `logoUrl` and `logoEl` computation
3. Wrap name text in `<span className="player-name-text">` in both returns
4. Add `{logoEl}` inside name button/span in both returns
5. Remove `<span className="player-team">` from both returns

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds

---

### Step 3: Update PlayerRow CSS
**Files**: `frontend/src/components/PlayerRow.css`

1. Update war room grid to 5 columns
2. Update draft grid to 3 columns
3. Add `justify-content: space-between` and `gap: 6px` to `.player-name-btn`
4. Add `.player-name-text` styles
5. Add `.player-team-logo` styles
6. Remove `.player-team` rule

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds
- [ ] Manual: logos appear in name boxes
- [ ] Manual: no broken icons for any player

---

### Step 4: Final verification

**Validation:**
- [ ] Frontend builds cleanly
- [ ] All existing backend tests still pass
- [ ] Manual: logos visible in all 4 columns
- [ ] Manual: free agent rows show no logo
- [ ] Manual: long names truncate with ellipsis before logo
- [ ] Manual: draft mode mine/other backgrounds show logos
- [ ] Manual: search, reorder, notes, add, delete all work

---

## Testing Requirements

### No Automated Tests
Pure visual change — no backend, no logic requiring unit tests.

### Manual Browser Tests
- [ ] Logo appears for players with valid teams (KC, SF, BUF, etc.)
- [ ] JAC correctly maps to `jax` ESPN URL
- [ ] Free agents (FA, --) show no `<img>` element
- [ ] Logo is 18px tall, right-aligned in name box
- [ ] Logo opacity ~72% — visible but subordinate to name
- [ ] Long player names truncate before logo (ellipsis)
- [ ] War room grid aligned correctly (5 columns)
- [ ] Draft row grid aligned correctly (3 columns)
- [ ] Draft mode green/purple backgrounds: logos still visible
- [ ] Slow network: name shows first, logo loads after (no layout shift)
- [ ] Hover: Honolulu Blue background, logo still visible

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `cd frontend && npx vite build` | Build succeeds | ☐ |
| 2 | Start dev servers | Both start cleanly | ☐ |
| 3 | Open War Room | Logos visible in all player name boxes | ☐ |
| 4 | Scroll through QB column | All logos correct, no broken icons | ☐ |
| 5 | Check a known FA player (if any) | No logo, no broken icon | ☐ |
| 6 | Hover a player row | Blue background, logo visible | ☐ |
| 7 | Switch to Draft Mode | Logos visible, dots work | ☐ |
| 8 | Mark a player "mine" | Green bg, logo visible at 72% | ☐ |
| 9 | Reorder two players | Logos follow players correctly | ☐ |
| 10 | Open notes dialog | Dialog works, no regression | ☐ |
| 11 | Search for a player | Scroll-to works, logo visible | ☐ |

---

## Error Handling

| Scenario | Handling |
|----------|---------|
| ESPN CDN returns 404 | `onError` sets `display: none` — no broken icon |
| Team is null/undefined | `getLogoUrl` returns null — no `<img>` rendered |
| Team is "FA" or "--" | `getLogoUrl` returns null — no `<img>` rendered |
| ESPN CDN unreachable | `onError` hides image — name text still visible |

---

## Open Questions

None — the init spec provides the exact utility function, JSX changes,
CSS values, and ESPN URL format.

---

## Rollback Plan

```bash
git revert <commit>
cd frontend && npx vite build
```

Pure frontend — no data or backend impact.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Exact utility code, JSX diffs, CSS values, grid layouts all specified |
| Feasibility | 10 | Standard `<img>` with error fallback — nothing exotic |
| Completeness | 10 | All files listed, every edge case covered (FA, 404, long names) |
| Alignment | 9 | ESPN CDN is a runtime image fetch, which the init spec explicitly exempts from the "no external API" constraint. Reasonable for static assets. |
| **Average** | **9.75** | Ready for execution |

---

## Notes

### ESPN CDN URL Pattern
`https://a.espncdn.com/i/teamlogos/nfl/500/{abbrev}.png` where `{abbrev}`
is lowercase. The `/500/` is the image size bucket — browser resizes to
18px CSS height. These are aggressively cached by browsers and CDN edge
servers.

### Only One Hard Mismatch
FantasyPros uses `JAC` for Jacksonville; ESPN uses `jax`. All other teams
use the same abbreviation (just lowercased). The `OVERRIDES` map handles
this single case.
