# 13-init-team-gradients.md — Team Color Gradients on Player Name Boxes

**Date**: 2026-04-15
**Phase**: 1d — Polish
**Scope**: Frontend only — new utility, JSX and CSS changes
**Backend changes**: None
**New tests**: None (pure visual)
**New ADR**: None

---

## Context

Team logos were added to the right edge of player name boxes in PRP-012.
This spec adds a complementary gradient to the name box background: the left
portion holds the existing tier color (solid, so the name text always reads
cleanly) and the right portion fades toward the team's primary color — tying
the logo badge visually back into the name box itself.

The gradient applies in both War Room and Draft Mode. In Draft Mode, the
gradient base color is the draft status color (`#1A7A3A` mine,
`#6B2FA0` other), so the team tint sits on top of the status color rather than
replacing it.

---

## Design Specification

### Gradient structure

```
|--- name text zone (solid) ---|--- logo zone (team tint) ---|
0%                            45%                           100%
```

```css
linear-gradient(
  to right,
  {base} 0%,
  {base} 45%,
  color-mix(in srgb, {teamColor} 22%, {base}) 100%
)
```

`color-mix(in srgb, {teamColor} 22%, {base})` blends 22% of the team color
into the base — enough to be visible on close inspection, not enough to
compete with the name text or overwhelm dark base colors.

`color-mix` is supported in all modern browsers (Chrome 111+, Firefox 113+,
Safari 16.2+) — acceptable for a personal app.

### Base colors per state

| State | Base color |
|-------|-----------|
| War Room — tier odd | `#1A3A5C` |
| War Room — tier even | `#2A5A8C` |
| Draft — mine | `#1A7A3A` |
| Draft — other | `#6B2FA0` |
| Draft — undrafted | tier odd/even (same as War Room) |

### Free agents / no team

`getTeamColor` returns `null` for FA, `--`, empty, or unknown team values.
When `null`, no inline style is set — the name box retains its plain solid
tier/status background exactly as today.

---

## All 32 Team Colors

Colors chosen for maximum visibility on the dark navy background. For teams
whose primary color is black or very dark navy (Raiders, Steelers, Bears,
Cowboys primary, Patriots primary, Seahawks primary, etc.), the most
distinctive visible secondary color is used instead.

```js
// FantasyPros abbreviation → hex
const TEAM_COLORS = {
  ARI: '#97233F', // Cardinals — Cardinal Red
  ATL: '#A71930', // Falcons   — Red
  BAL: '#241773', // Ravens    — Purple
  BUF: '#C60C30', // Bills     — Red (navy too dark)
  CAR: '#0085CA', // Panthers  — Panther Blue
  CHI: '#C83803', // Bears     — Orange (navy too dark)
  CIN: '#FB4F14', // Bengals   — Orange
  CLE: '#FF3C00', // Browns    — Orange
  DAL: '#00338D', // Cowboys   — Royal Blue
  DEN: '#FB4F14', // Broncos   — Orange
  DET: '#0076B6', // Lions     — Honolulu Blue
  GB:  '#FFB612', // Packers   — Gold
  HOU: '#A71930', // Texans    — Battle Red
  IND: '#002C5F', // Colts     — Royal Blue
  JAC: '#006778', // Jaguars   — Teal
  KC:  '#E31837', // Chiefs    — Red
  LV:  '#A5ACAF', // Raiders   — Silver (black invisible)
  LAC: '#0073CF', // Chargers  — Powder Blue
  LAR: '#B3995D', // Rams      — New Century Gold
  MIA: '#008E97', // Dolphins  — Aqua
  MIN: '#4F2683', // Vikings   — Purple
  NE:  '#C60C30', // Patriots  — Red (navy too dark)
  NO:  '#D3BC8D', // Saints    — Old Gold
  NYG: '#A71930', // Giants    — Red
  NYJ: '#003F2D', // Jets      — Green
  PHI: '#004C54', // Eagles    — Midnight Green
  PIT: '#FFB612', // Steelers  — Gold (black invisible)
  SF:  '#AA0000', // 49ers     — Red
  SEA: '#69BE28', // Seahawks  — Action Green (navy too dark)
  TB:  '#D50A0A', // Buccaneers — Red
  TEN: '#4B92DB', // Titans    — Titans Blue (navy too dark)
  WSH: '#773141', // Commanders — Burgundy
}
```

---

## Files to Change

### 1. `frontend/src/utils/teamColors.js` — NEW FILE

Parallel to `teamLogos.js`. Same free-agent token set for consistency.

```js
const TEAM_COLORS = {
  ARI: '#97233F', ATL: '#A71930', BAL: '#241773', BUF: '#C60C30',
  CAR: '#0085CA', CHI: '#C83803', CIN: '#FB4F14', CLE: '#FF3C00',
  DAL: '#00338D', DEN: '#FB4F14', DET: '#0076B6', GB:  '#FFB612',
  HOU: '#A71930', IND: '#002C5F', JAC: '#006778', KC:  '#E31837',
  LV:  '#A5ACAF', LAC: '#0073CF', LAR: '#B3995D', MIA: '#008E97',
  MIN: '#4F2683', NE:  '#C60C30', NO:  '#D3BC8D', NYG: '#A71930',
  NYJ: '#003F2D', PHI: '#004C54', PIT: '#FFB612', SF:  '#AA0000',
  SEA: '#69BE28', TB:  '#D50A0A', TEN: '#4B92DB', WSH: '#773141',
}

const FREE_AGENT_TOKENS = new Set(['FA', '--', '', 'FA '])

export function getTeamColor(team) {
  if (!team || FREE_AGENT_TOKENS.has(team.trim())) return null
  return TEAM_COLORS[team.toUpperCase()] ?? null
}
```

Returns `null` for unknown abbreviations — safe fallback to solid bg.

---

### 2. `frontend/src/components/PlayerRow.jsx`

#### Import

```js
import { getTeamColor } from '../utils/teamColors'
```

#### Gradient helper (top of component file, outside the component function)

```js
const TIER_BASES = { odd: '#1A3A5C', even: '#2A5A8C' }
const DRAFT_BASES = { mine: '#1A7A3A', other: '#6B2FA0' }

function buildGradient(base, teamHex) {
  return [
    `linear-gradient(to right,`,
    `  ${base} 0%,`,
    `  ${base} 45%,`,
    `  color-mix(in srgb, ${teamHex} 22%, ${base}) 100%`,
    `)`,
  ].join(' ')
}
```

#### Name style computation (inside component, before return)

```js
const teamColor = getTeamColor(player.team)

let nameStyle
if (teamColor) {
  const tierBase = player.tier % 2 === 0 ? TIER_BASES.even : TIER_BASES.odd
  const draftBase = DRAFT_BASES[draftStatus] ?? null
  const base = draftBase ?? tierBase
  nameStyle = { background: buildGradient(base, teamColor) }
}
```

Note: `draftStatus` is already available in the component — it is computed
from props in both the war room and draft returns. In the war room return,
`draftStatus` is `'undrafted'` (the default), so `DRAFT_BASES['undrafted']`
is `undefined`, `draftBase` is `null`, and the tier base is used. Correct.

#### Apply to both returns

War room name button:
```jsx
<button className={nameClasses} style={nameStyle} onClick={onNameClick}>
```

Draft row name span:
```jsx
<span className={nameClasses} style={nameStyle}>
```

No other JSX changes required.

---

### 3. `frontend/src/components/PlayerRow.css`

#### Remove `!important` from draft status background rules

Currently:
```css
.player-name-btn.status-mine  { background: #1A7A3A !important; }
.player-name-btn.status-other { background: #6B2FA0 !important; }
```

Inline styles cannot override CSS `!important`. Remove the `!important`
flags and increase specificity so the class-based solid colors still win
over the tier-based class backgrounds (for when there is no team color):

```css
.player-row .player-name-btn.status-mine  { background: #1A7A3A; }
.player-row .player-name-btn.status-other { background: #6B2FA0; }
```

With `!important` removed, the inline `style` attribute (which has the
gradient) will take precedence when a team color exists. When no team color
exists (`nameStyle` is undefined), no inline style is set and the
class-based solid background applies as before.

The increased specificity (`.player-row .player-name-btn` instead of
`.player-name-btn`) ensures the draft status colors still beat the
`.tier-odd` / `.tier-even` backgrounds in the cascade for free agents.

**No other CSS changes are required.** The existing tier-odd/even background
rules remain — they apply when `nameStyle` is undefined (no team color).

---

## Behaviour Summary

| Scenario | Name box background |
|----------|-------------------|
| War Room, valid team | Gradient: tier color → team tint (22%) |
| War Room, FA / no team | Solid tier color (unchanged) |
| Draft undrafted, valid team | Gradient: tier color → team tint |
| Draft mine, valid team | Gradient: `#1A7A3A` → team tint on green |
| Draft other, valid team | Gradient: `#6B2FA0` → team tint on purple |
| Draft mine, FA / no team | Solid `#1A7A3A` (unchanged) |
| Draft other, FA / no team | Solid `#6B2FA0` (unchanged) |
| Hover (any) | Solid `#0076B6` via `:hover` — gradient replaced |

Hover intentionally wipes the gradient — clean Honolulu Blue on hover is the
existing behavior and should not change.

---

## Acceptance Criteria

- [ ] Player name boxes show a gradient: flat tier color on left, team tint on right
- [ ] Gradient starts changing at ~45% of the name box width (logo zone only)
- [ ] Name text is always on the flat portion — no color bleed under text
- [ ] Free agent / no-team players have solid background (no gradient, no regression)
- [ ] Draft mode mine (green) shows gradient from green → team tint
- [ ] Draft mode other (purple) shows gradient from purple → team tint
- [ ] Hover still produces solid Honolulu Blue on all rows
- [ ] `npx vite build` — 0 errors
- [ ] No regressions in reorder, notes, add, delete, save/load, search, tier drag

---

## Non-Goals (Deferred)

- Adjusting gradient opacity per team (bright teams like SEA/GB look fine at 22%)
- Per-column gradient intensity tuning
- Any backend changes
- New automated tests
