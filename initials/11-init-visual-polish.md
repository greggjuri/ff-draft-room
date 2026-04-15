# 11-init-visual-polish.md — War Room Visual Enhancement

**Date**: 2026-04-15
**Phase**: 1d — Polish
**Scope**: Frontend only — CSS and minimal JSX changes
**Backend changes**: None
**New tests**: None (pure visual)
**New ADR**: None (no architectural decision)

---

## Context

The War Room board uses a consistent dark navy / Honolulu Blue palette that reads
well but lacks visual differentiation between positions. Every column looks
identical except for the position label text. Two enhancements have been chosen
for this phase:

1. **Position-specific column accent colors** — QB, RB, WR, and TE each get a
   distinct identity color used on the column header and tier left-border accents.
2. **Background hash-mark texture** — a very subtle repeating line pattern at
   low opacity over the dark navy background to add depth and atmosphere without
   distracting from the board content.

A third enhancement — team-specific coloring — has been explicitly deferred to a
later phase. This spec covers only the two items above.

---

## Design Tokens

### Position Accent Colors

| Position | Primary (`--pos-color`) | Dark accent (`--pos-color-dark`) | Mid accent (`--pos-color-mid`) |
|----------|------------------------|-----------------------------------|-------------------------------|
| QB       | `#C8881A`              | `#6A4A0A`                         | `#9A6A1A`                     |
| RB       | `#239B52`              | `#0F4A25`                         | `#1A7A3A`                     |
| WR       | `#0076B6`              | `#1A3A5C`                         | `#2A5A8C`                     |
| TE       | `#C0541A`              | `#6A2A0A`                         | `#9A4A1A`                     |

WR intentionally keeps `#0076B6` (Honolulu Blue) as its primary — it is already
the app's accent color and this column is the natural home for it. The other three
positions introduce new, distinct hues.

### Background Texture

A horizontal repeating stripe pattern applied to the app's root background.
Emulates the alternating light/dark yard-stripe banding of a football field when
viewed from above. Very low opacity — the texture should be perceptible on close
inspection, invisible at a glance.

```css
background-color: #0D1B2A;
background-image: repeating-linear-gradient(
  180deg,
  transparent 0px,
  transparent 48px,
  rgba(0, 118, 182, 0.028) 48px,
  rgba(0, 118, 182, 0.028) 50px
);
```

Stripe pitch: 50px (2px line, 48px gap). Tinted with Honolulu Blue at 2.8% opacity
so it reads as part of the same color family rather than a neutral grey line.

---

## Files to Change

### 1. `frontend/src/App.css`

Add the background texture to the root app container. The existing `background`
declaration on `.app` (or `body`, whatever holds `#0D1B2A`) should be replaced
with the two-property form:

```css
/* Before */
background: #0D1B2A;

/* After */
background-color: #0D1B2A;
background-image: repeating-linear-gradient(
  180deg,
  transparent 0px,
  transparent 48px,
  rgba(0, 118, 182, 0.028) 48px,
  rgba(0, 118, 182, 0.028) 50px
);
```

If the dark background is set on `body` in `index.html` or a global reset, move
it to a CSS class that wraps the React tree so the texture is scoped to the app.
Do not apply `background-image` to `body` directly — it will tile underneath
modals and dialogs in unexpected ways.

---

### 2. `frontend/src/components/PositionColumn.jsx`

Add the position identifier as a CSS class on the column wrapper so position-
scoped CSS custom properties cascade through all child components.

```jsx
// Before — approximate current shape
<div className="position-column">

// After
<div className={`position-column position-${position.toLowerCase()}`}>
```

Also add the `depth` sub-label to the column header. Player depth constants are
already defined in the frontend (or can be inlined — the values never change):

```
QB: 30 · RB: 50 · WR: 50 · TE: 30
```

Add a depth constant map near the top of the component file:

```js
const POSITION_DEPTH = { QB: 30, RB: 50, WR: 50, TE: 30 };
```

Update the column header JSX:

```jsx
// Before
<div className="col-header">
  <span className="col-position-label">{position}</span>
</div>

// After
<div className="col-header">
  <span className="col-position-label">{position}</span>
  <span className="col-depth-label">depth · {POSITION_DEPTH[position]}</span>
</div>
```

---

### 3. `frontend/src/components/PositionColumn.css`

Define the four position CSS custom property sets. All color values cascade
automatically to `TierGroup` and `PlayerRow` children via the DOM hierarchy —
no prop drilling required.

```css
/* Position-scoped design tokens */
.position-qb {
  --pos-color:      #C8881A;
  --pos-color-mid:  #9A6A1A;
  --pos-color-dark: #6A4A0A;
}
.position-rb {
  --pos-color:      #239B52;
  --pos-color-mid:  #1A7A3A;
  --pos-color-dark: #0F4A25;
}
.position-wr {
  --pos-color:      #0076B6;
  --pos-color-mid:  #2A5A8C;
  --pos-color-dark: #1A3A5C;
}
.position-te {
  --pos-color:      #C0541A;
  --pos-color-mid:  #9A4A1A;
  --pos-color-dark: #6A2A0A;
}

/* Column header — position label */
.col-header {
  border-bottom: 3px solid var(--pos-color);
  padding-bottom: 6px;
  text-align: center;
}

.col-position-label {
  color: var(--pos-color);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.12em;
  display: block;
}

.col-depth-label {
  color: #4a7090;
  font-size: 10px;
  letter-spacing: 0.05em;
  display: block;
  margin-top: 2px;
}
```

Remove or override any existing rule that set the col-header border or
`.col-position-label` color to a hardcoded value — these now come from
`var(--pos-color)` via the position class.

---

### 4. `frontend/src/components/TierGroup.css`

Add a left-border accent to tier group headers. Odd tiers use `--pos-color-dark`,
even tiers use `--pos-color-mid`. This gives each tier a subtle chromatic hint
that ties back to its column color without being loud.

```css
/* Tier header left-border accent — position-tinted */
.tier-header {
  border-left: 2px solid var(--pos-color-dark);
  padding-left: 8px;           /* add if not already present */
}

/* Even tiers get the mid shade */
.tier-group:nth-child(even) .tier-header {
  border-left-color: var(--pos-color-mid);
}
```

**Important**: the `--pos-color-*` variables are defined on `.position-{pos}` in
`PositionColumn.css`. They cascade down to `.tier-header` automatically because
`TierGroup` is a child of `PositionColumn` in the DOM. No changes to `TierGroup`
props or JSX are required.

Verify that `border-radius: 0` is set (or absent) on `.tier-header` — a left-
only border with a non-zero border-radius looks broken. Rounded corners only work
when all four sides have a border.

---

### 5. `frontend/src/components/TierGroup.jsx`

No changes required if the component already renders with a wrapper that carries
odd/even tier index. If it does not, the parent (`PositionColumn.jsx`) must pass
a `tierIndex` prop so the component can apply an `even` / `odd` class:

```jsx
// In PositionColumn.jsx, when mapping over tiers:
<TierGroup
  key={tier}
  tierIndex={index}   // 0-based index — add this prop
  ...
/>

// In TierGroup.jsx, on the wrapper:
<div className={`tier-group ${tierIndex % 2 === 0 ? 'odd' : 'even'}`}>
```

Check whether the existing `tier` field value (1-based integer from backend data)
is already used to apply an odd/even class — if so, use that instead of a new
prop. Avoid redundancy.

---

## What Stays Unchanged

| Element | Reason |
|---------|--------|
| Player name box backgrounds (`#1A3A5C` / `#2A5A8C`) | The tier background is the core alternating visual — keep it |
| Draft mode colors (`#1A7A3A` mine / `#6B2FA0` other) | These are functional status signals, not decoration |
| Honolulu Blue `#0076B6` as the interactive / hover color | Hover state on player rows remains consistent across all columns |
| Status dots | Unchanged |
| All typography outside the column header sub-label | Monospace font, existing sizes |
| All backend code | This spec is frontend-only |

---

## Acceptance Criteria

- [ ] Each column header shows a `3px` bottom border in its position color
- [ ] Each column position label (`QB`, `RB`, etc.) is rendered in its position color
- [ ] Each column header shows a `depth · N` sub-label in muted grey below the position label
- [ ] Tier headers have a `2px` left border: dark shade on odd tiers, mid shade on even tiers
- [ ] Left border on tier headers has no border-radius (flat edge)
- [ ] Background of the main app container shows the subtle horizontal stripe texture
- [ ] Texture is not visible on top of modals/dialogs (dialogs have opaque backgrounds)
- [ ] Hovering a player row still turns the name box to `#0076B6` regardless of column
- [ ] Draft mode mine/other colors are unaffected
- [ ] No regressions in War Room functionality (reorder, notes, add, delete, save/load)
- [ ] No regressions in Draft Mode (dot cycling, exit confirm, search)
- [ ] Visual check at both `localhost:5173` (dev) and `ff.jurigregg.com` (prod) after deploy

---

## Non-Goals (Deferred)

- Team-specific coloring — deferred to a future spec
- Player row color gradients based on VOR value — future consideration
- Animated transitions or hover effects beyond existing behavior
- Logo / header branding treatment
- Any change to the sticky header layout or toolbar
