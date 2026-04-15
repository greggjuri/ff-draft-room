# PRP-013: Team Color Gradients on Player Name Boxes

**Created**: 2026-04-15
**Initial**: `initials/13-init-team-gradients.md`
**Status**: Complete

---

## Overview

### Problem Statement
Player name boxes have team logos (PRP-012) but the background is still a
flat tier color. There's no visual connection between the logo badge and
the name box itself.

### Proposed Solution
Add a subtle gradient to each name box background: the left portion stays
solid (tier or draft-status color for readable text), the right portion
fades toward the team's primary color at 22% blend — tying the logo badge
visually into the name box.

### Success Criteria
- [ ] Name boxes show gradient: flat tier color left, team tint right
- [ ] Gradient transition starts at ~45% width (logo zone only)
- [ ] Name text sits on flat portion — no color bleed under text
- [ ] Free agent / no-team players have solid background (no gradient)
- [ ] Draft mine shows gradient from green → team tint
- [ ] Draft other shows gradient from purple → team tint
- [ ] Hover still produces solid Honolulu Blue on all rows
- [ ] `cd frontend && npx vite build` — no errors
- [ ] No regressions in any functionality

---

## Context

### Related Documentation
- `initials/13-init-team-gradients.md` — Full design spec with all 32 team colors
- `prps/12-prp-team-logos.md` — Team logos (prerequisite)

### Dependencies
- **Required**: PRP-012 (team logos — current PlayerRow shape)

### Files to Create/Modify
```
# NEW
frontend/src/utils/teamColors.js            # getTeamColor() — 32 team hex map

# MODIFIED
frontend/src/components/PlayerRow.jsx       # Gradient style computation + inline style
frontend/src/components/PlayerRow.css       # Remove !important from draft status rules
```

No backend changes. No new tests.

---

## Technical Specification

### Team Color Utility (`frontend/src/utils/teamColors.js`)

Map of all 32 NFL teams (FantasyPros abbreviations → hex). Teams with
dark primary colors use their most visible secondary color instead.
Returns `null` for free agents and unknown abbreviations.

### Gradient Construction

```css
linear-gradient(
  to right,
  {base} 0%,
  {base} 45%,
  color-mix(in srgb, {teamColor} 22%, {base}) 100%
)
```

`color-mix` blends 22% team color into the base. Supported in
Chrome 111+, Firefox 113+, Safari 16.2+.

### Base Color Selection

| State | Base |
|-------|------|
| War Room tier odd | `#1A3A5C` |
| War Room tier even | `#2A5A8C` |
| Draft mine | `#1A7A3A` |
| Draft other | `#6B2FA0` |
| Draft undrafted | tier odd/even |

### CSS `!important` Fix

Current draft status rules use `!important`, which blocks inline styles.
Remove `!important` and increase specificity to `.player-row .player-name-btn.status-*`
so class-based solid colors still beat tier backgrounds for free agents,
but inline gradient styles take precedence when a team color exists.

---

## Implementation Steps

### Step 1: Create teamColors utility
**Files**: `frontend/src/utils/teamColors.js`

Create with all 32 team colors and `getTeamColor()` function.

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds

---

### Step 2: Update PlayerRow JSX — gradient computation + inline style
**Files**: `frontend/src/components/PlayerRow.jsx`

1. Import `getTeamColor`
2. Add `TIER_BASES`, `DRAFT_BASES` constants and `buildGradient()` helper
3. Compute `nameStyle` from team color + base color
4. Apply `style={nameStyle}` to name button (war room) and name span (draft)

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds

---

### Step 3: Update PlayerRow CSS — remove !important
**Files**: `frontend/src/components/PlayerRow.css`

Replace:
```css
.player-name-btn.status-mine  { background: #1A7A3A !important; }
.player-name-btn.status-other { background: #6B2FA0 !important; }
```
With:
```css
.player-row .player-name-btn.status-mine  { background: #1A7A3A; }
.player-row .player-name-btn.status-other { background: #6B2FA0; }
```

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds
- [ ] Manual: gradients visible in browser
- [ ] Manual: hover still solid Honolulu Blue
- [ ] Manual: draft mine/other show gradient on status base color
- [ ] Manual: free agents show solid background

---

### Step 4: Final verification

- [ ] Frontend builds cleanly
- [ ] Backend tests still pass (69)
- [ ] Manual visual check across all 4 columns
- [ ] No regressions

---

## Testing Requirements

### No Automated Tests
Pure visual — no logic requiring unit tests.

### Manual Browser Tests
- [ ] Gradient visible on right portion of name boxes (team-colored tint)
- [ ] Left portion flat — name text fully readable
- [ ] Free agents (FA, --) have solid background, no gradient
- [ ] Draft mine: gradient from green base
- [ ] Draft other: gradient from purple base
- [ ] Hover: solid Honolulu Blue (gradient overridden)
- [ ] All team colors render correctly (spot-check KC red, GB gold, SEA green)
- [ ] Tier drag, reorder, notes, search all still work

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `cd frontend && npx vite build` | Build succeeds | ☐ |
| 2 | Start dev servers | Both start cleanly | ☐ |
| 3 | Open War Room | Gradients visible on player name boxes | ☐ |
| 4 | Scroll QB column | Right edge of name boxes tinted per team | ☐ |
| 5 | Check a GB player | Gold tint on right edge | ☐ |
| 6 | Check a KC player | Red tint on right edge | ☐ |
| 7 | Hover a player | Solid Honolulu Blue, no gradient | ☐ |
| 8 | Switch to Draft Mode | Gradients on undrafted rows | ☐ |
| 9 | Mark player "mine" | Green base gradient | ☐ |
| 10 | Mark player "other" | Purple base gradient | ☐ |
| 11 | Reorder + Save | Works normally | ☐ |

---

## Error Handling

No new error handling needed. `getTeamColor` returns `null` for unknown
teams — no gradient applied, solid background preserved.

---

## Open Questions

None — the init spec provides all 32 colors, exact CSS gradient syntax,
base color logic, and the `!important` removal fix.

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
| Clarity | 10 | All 32 colors specified, gradient CSS provided, base color logic explicit |
| Feasibility | 10 | CSS `color-mix` + inline style — standard modern CSS |
| Completeness | 10 | All files, every state combination (war room/draft/hover/FA) covered |
| Alignment | 10 | Pure visual CSS enhancement, no ADR impact |
| **Average** | **10** | Ready for execution |
