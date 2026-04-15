# 12-init-team-logos.md — Team Logos on Player Name Boxes

**Date**: 2026-04-15
**Phase**: 1d — Polish
**Scope**: Frontend only — new utility, JSX and CSS changes
**Backend changes**: None
**New tests**: None (pure visual, no logic)
**New ADR**: None

---

## Context

Each player already carries a `team` field (e.g. `"KC"`, `"SF"`, `"JAC"`).
Currently that abbreviation is rendered as a small muted text label in its own
grid column outside the name box. This spec moves team identity inside the name
box as a small NFL team logo image, sourced from the ESPN CDN at runtime.

The external team abbreviation text column is removed — the logo replaces it.

---

## Design Decision: ESPN CDN

Logo images are fetched at runtime from:

```
https://a.espncdn.com/i/teamlogos/nfl/500/{abbrev}.png
```

where `{abbrev}` is a lowercase ESPN team abbreviation.

**Rationale**: Zero setup, no bundled assets, browser caches after first load.
The app requires internet in production (`ff.jurigregg.com`) so there is no
offline regression. The "no external API calls at runtime" constraint in
`CLAUDE.md` targets live stats/rankings data — static image assets are exempt.

---

## Abbreviation Normalization

FantasyPros abbreviations must be lowercased and one known mismatch corrected
before forming the ESPN URL.

| FantasyPros | ESPN | Note |
|-------------|------|------|
| `JAC`       | `jax` | Only hard mismatch |
| All others  | lowercase of FantasyPros value | e.g. `KC` → `kc` |

Free agent / unsigned players use values like `"FA"`, `"--"`, `""`, or `null`.
These must map to `null` so no logo request is made.

---

## Files to Change

### 1. `frontend/src/utils/teamLogos.js` — NEW FILE

```js
const OVERRIDES = {
  JAC: 'jax',
}

const FREE_AGENT_TOKENS = new Set(['FA', '--', '', 'FA '])

export function getLogoUrl(team) {
  if (!team || FREE_AGENT_TOKENS.has(team.trim())) return null
  const abbrev = OVERRIDES[team.toUpperCase()] ?? team.toLowerCase()
  return `https://a.espncdn.com/i/teamlogos/nfl/500/${abbrev}.png`
}
```

Returns `null` for free agents — callers must guard against null before
rendering an `<img>`. This keeps the component clean.

---

### 2. `frontend/src/components/PlayerRow.jsx`

#### Import

```js
import { getLogoUrl } from '../utils/teamLogos'
```

#### Logo element

Define a small helper at the top of the component or inline — a single `<img>`
with an `onError` handler that hides itself if ESPN returns a 404:

```jsx
const logoUrl = getLogoUrl(player.team)

const logoEl = logoUrl ? (
  <img
    src={logoUrl}
    alt={player.team}
    className="player-team-logo"
    onError={e => { e.currentTarget.style.display = 'none' }}
  />
) : null
```

#### War Room name button — add logo as right-side flex child

```jsx
// Before
<button className={nameClasses} onClick={onNameClick}>
  {nameLabel}
</button>

// After
<button className={nameClasses} onClick={onNameClick}>
  <span className="player-name-text">{nameLabel}</span>
  {logoEl}
</button>
```

#### Draft row name span — same treatment

```jsx
// Before
<span className={nameClasses}>{nameLabel}</span>

// After
<span className={nameClasses}>
  <span className="player-name-text">{nameLabel}</span>
  {logoEl}
</span>
```

#### Remove external team abbreviation

Remove `<span className="player-team">{player.team}</span>` from **both** the
war room return and the draft return. The logo inside the name box replaces it.

---

### 3. `frontend/src/components/PlayerRow.css`

#### Update grid — remove `team` column

```css
/* War room row — before */
grid-template-columns: 24px 24px 24px 1fr 36px 24px;

/* War room row — after (team column removed) */
grid-template-columns: 24px 24px 24px 1fr 24px;
```

```css
/* Draft row — before */
grid-template-columns: 12px 24px 1fr 36px;

/* Draft row — after (team column removed) */
grid-template-columns: 12px 24px 1fr;
```

#### Name box — ensure flex layout supports logo

The name box already has `display: flex; align-items: center`. Add
`justify-content: space-between` so the logo is pushed to the right edge:

```css
.player-name-btn {
  /* existing rules stay unchanged */
  display: flex;
  align-items: center;
  justify-content: space-between;   /* add this */
  gap: 6px;                         /* add this */
}
```

#### Name text — clamp overflow before logo

The player name text must not overflow into the logo area:

```css
.player-name-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

#### Team logo

```css
.player-team-logo {
  height: 18px;
  width: auto;
  flex-shrink: 0;
  opacity: 0.72;
  display: block;
}
```

Opacity `0.72` keeps logos present but subordinate to the player name text.
The `onError` fallback in JSX handles ESPN 404s (handles free agents routed
through before `getLogoUrl` returns null — belt and suspenders).

#### Remove orphaned rule

Remove the `.player-team` CSS rule entirely — the element no longer exists.

---

## Layout After Changes

### War Room row
```
[ ▲ ][ ▼ ][ rank ][ name text ············ logo ][ × ]
 24px 24px  24px          1fr                       24px
```

### Draft row
```
[ ● ][ rank ][ name text ················ logo ]
 12px  24px           1fr
```

---

## Behaviour Notes

| Scenario | Result |
|----------|--------|
| Player has valid team (e.g. `"KC"`) | Logo renders at 18px height, right-aligned in name box |
| Player is free agent (`"FA"`, `"--"`) | `getLogoUrl` returns null — no `<img>` rendered |
| ESPN returns 404 (bad abbrev, expansion team) | `onError` hides the image — no broken icon |
| Slow network / logo not yet loaded | Name box shows name only until image loads — no layout shift (logo has fixed height in CSS) |
| Draft mode — mine (green bg) | Logo renders on green background. Opacity 0.72 ensures visibility |
| Draft mode — other (purple bg) | Logo renders on purple background. Same |
| Player name is long | `.player-name-text` truncates with ellipsis before reaching logo |

---

## Acceptance Criteria

- [ ] Each player name box shows a small team logo at its right edge
- [ ] Logo is 18px tall, aspect ratio preserved, opacity ~72%
- [ ] Free agent players (`FA`, `--`) show no logo — no broken image icon
- [ ] Unknown teams fall back silently via `onError` — no broken image icon
- [ ] Player name text truncates with ellipsis before overlapping the logo
- [ ] External team abbreviation text is removed from all row variants
- [ ] War room grid column count updated correctly (5 columns, not 6)
- [ ] Draft row grid column count updated correctly (3 columns, not 4)
- [ ] Logos visible in draft mode on both green (mine) and purple (other) backgrounds
- [ ] Logos visible at `ff.jurigregg.com` (internet access confirmed)
- [ ] No regressions in ▲▼ reorder, notes, add, delete, save/load
- [ ] No regressions in draft mode dot cycling, search scroll-to, exit confirm
- [ ] `npx vite build` — 0 errors, 0 warnings

---

## Non-Goals (Deferred)

- Team-specific column or tier color theming — separate future spec
- Caching/preloading logos — browser cache is sufficient
- Bundling logos as static assets — revisit only if ESPN CDN proves unreliable
- Any backend changes
