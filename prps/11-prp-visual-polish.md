# PRP-011: War Room Visual Enhancement

**Created**: 2026-04-15
**Initial**: `initials/11-init-visual-polish.md`
**Status**: Complete

---

## Overview

### Problem Statement
All four position columns look identical except for the label text. The
flat dark background lacks texture and depth. The board reads well but
has no visual personality or positional identity.

### Proposed Solution
Two CSS-focused enhancements:
1. **Position-specific accent colors** — each column gets a distinct hue
   applied to the header border, position label, and tier left-border
2. **Background hash-mark texture** — subtle horizontal stripe pattern on
   the app background for depth, evoking football field yard lines

### Success Criteria
- [ ] Column headers show 3px bottom border in position color
- [ ] Position labels (QB, RB, WR, TE) rendered in position color
- [ ] `depth · N` sub-label shown below position label in muted grey
- [ ] Tier headers have 2px left border: dark shade odd tiers, mid shade even
- [ ] Left border on tier headers has no border-radius
- [ ] Background shows subtle horizontal stripe texture
- [ ] Texture not visible on modals/dialogs (opaque backgrounds)
- [ ] Hover on player rows still shows `#0076B6` across all columns
- [ ] Draft mode mine/other colors unaffected
- [ ] No regressions in any War Room or Draft Mode functionality
- [ ] `cd frontend && npx vite build` — no errors
- [ ] No file exceeds 500 lines

---

## Context

### Related Documentation
- `docs/DECISIONS.md` — ADR-006 (FastAPI + React, full CSS control)
- `initials/11-init-visual-polish.md` — Design spec with exact color values

### Dependencies
- **Required**: PRP 05 (React frontend), PRP 10 (tier drag — current PositionColumn shape)
- **None external** — pure CSS + minimal JSX changes

### Design Tokens

| Position | `--pos-color` | `--pos-color-dark` | `--pos-color-mid` |
|----------|---------------|--------------------|--------------------|
| QB       | `#C8881A`     | `#6A4A0A`          | `#9A6A1A`          |
| RB       | `#239B52`     | `#0F4A25`          | `#1A7A3A`          |
| WR       | `#0076B6`     | `#1A3A5C`          | `#2A5A8C`          |
| TE       | `#C0541A`     | `#6A2A0A`          | `#9A4A1A`          |

### Files to Modify
```
frontend/src/App.css                       # Background texture
frontend/src/components/PositionColumn.jsx # Position class + depth label
frontend/src/components/PositionColumn.css # Position color tokens + header styles
frontend/src/components/TierGroup.css      # Tier left-border accent
```

No backend changes. No new tests. No new components.

---

## Technical Specification

### Background Texture (`App.css`)

The `body` rule currently uses `background: var(--bg-primary)` — this is
the `background` shorthand, which resets `background-image` to `none`.
You cannot just add a `background-image` alongside it; the shorthand wins.
Replace the single `background` shorthand with two explicit properties
using the **literal color value**, not the variable:

```css
/* Replace:  background: var(--bg-primary);  */
background-color: #0D1B2A;
background-image: repeating-linear-gradient(
  180deg,
  transparent 0px,
  transparent 48px,
  rgba(0, 118, 182, 0.028) 48px,
  rgba(0, 118, 182, 0.028) 50px
);
```

The stripe pitch is 50px (2px line, 48px gap), tinted Honolulu Blue at
2.8% opacity.

The sticky header uses `background: var(--bg-primary)` which is opaque —
this correctly covers the texture underneath. Dialogs have
`background: var(--bg-secondary)` on the `<dialog>` element plus the
`::backdrop` overlay — also opaque. No additional work needed.

### Position Column Class (`PositionColumn.jsx`)

Add position identifier as CSS class:
```jsx
<div className={`position-column position-${position.toLowerCase()}`}>
```

Add depth constant map and sub-label to header:
```js
const POSITION_DEPTH = { QB: 30, RB: 50, WR: 50, TE: 30 }
```

### Position Color Tokens (`PositionColumn.css`)

Define CSS custom properties on `.position-qb`, `.position-rb`,
`.position-wr`, `.position-te`. These cascade to all child elements
including `TierGroup` and `PlayerRow`.

Update `.column-header` to use `border-bottom: 3px solid var(--pos-color)`.
Update `.column-position` to use `color: var(--pos-color)`.
Add `.column-depth` for the sub-label.

### Tier Left-Border (`TierGroup.css`)

Add left-border to `.tier-header` using `var(--pos-color-dark)`.
The existing `tierNum % 2` class (`tier-odd` / `tier-even`) on
`.tier-header` already handles odd/even differentiation. Use
`.tier-header.tier-even` for the mid shade variant.

Remove `border-radius` from `.tier-header` if present (a left-only
border with border-radius looks broken).

---

## Implementation Steps

### Step 1: Background texture
**Files**: `frontend/src/App.css`

Replace `background: var(--bg-primary)` on `body` with the two-property
gradient form.

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds
- [ ] Background shows subtle stripe pattern in browser

---

### Step 2: Position column class + depth label
**Files**: `frontend/src/components/PositionColumn.jsx`

1. Add `POSITION_DEPTH` constant map
2. Add position class to wrapper div
3. Add depth sub-label to column header

**Validation:**
```bash
cd frontend && npx vite build
```
- [ ] Build succeeds
- [ ] Each column shows `depth · N` below position label

---

### Step 3: Position color tokens + header styling
**Files**: `frontend/src/components/PositionColumn.css`

1. Add `.position-qb`, `.position-rb`, `.position-wr`, `.position-te`
   with `--pos-color`, `--pos-color-dark`, `--pos-color-mid`
2. Update `.column-header` border to use `var(--pos-color)`
3. Update `.column-position` color to use `var(--pos-color)`
4. Add `.column-depth` styles
5. Remove hardcoded color values replaced by custom properties

**Validation:**
- [ ] Column headers show 3px border in position color
- [ ] Position labels in position color
- [ ] Sub-labels in muted grey

---

### Step 4: Tier left-border accent
**Files**: `frontend/src/components/TierGroup.css`

1. Add `border-left: 2px solid var(--pos-color-dark)` to `.tier-header`
2. Override with `var(--pos-color-mid)` on `.tier-header.tier-even`
3. Ensure no border-radius on `.tier-header`

**Validation:**
- [ ] Tier headers show left border in position color shades
- [ ] Odd tiers use dark shade, even tiers use mid shade
- [ ] No rounded corners on tier headers

---

### Step 5: Final visual verification
**Commands:**
```bash
cd frontend && npx vite build
```

**Validation:**
- [ ] Build clean
- [ ] All 4 columns visually distinct
- [ ] Background texture visible on close inspection, invisible at a glance
- [ ] Hover states unchanged (Honolulu Blue on all columns)
- [ ] Draft mode colors unchanged
- [ ] Dialogs opaque, no texture bleed
- [ ] No regressions in functionality

---

## Testing Requirements

### No Automated Tests
This is a pure visual change — no backend modifications, no new logic.

### Manual Browser Tests
- [ ] QB column header: gold border + label `#C8881A`
- [ ] RB column header: green border + label `#239B52`
- [ ] WR column header: blue border + label `#0076B6`
- [ ] TE column header: orange border + label `#C0541A`
- [ ] All columns show `depth · N` sub-label
- [ ] Tier headers show left border (dark shade odd, mid shade even)
- [ ] Background stripe texture visible at full zoom
- [ ] Texture not visible through dialog backdrop
- [ ] Player hover → Honolulu Blue across all columns
- [ ] Draft mode mine (green) / other (purple) unchanged
- [ ] Reorder, notes, add, delete, save/load all work
- [ ] Search highlight works
- [ ] Tier drag separator works

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | `cd frontend && npx vite build` | Build succeeds | ☐ |
| 2 | Start dev servers | Both start cleanly | ☐ |
| 3 | Open War Room | Four columns with distinct colors | ☐ |
| 4 | Inspect QB header | Gold 3px border, gold label, `depth · 30` | ☐ |
| 5 | Inspect RB header | Green 3px border, green label, `depth · 50` | ☐ |
| 6 | Inspect WR header | Blue 3px border, blue label, `depth · 50` | ☐ |
| 7 | Inspect TE header | Orange 3px border, orange label, `depth · 30` | ☐ |
| 8 | Inspect tier headers | Left border in position color shades | ☐ |
| 9 | Inspect background | Subtle stripe pattern visible | ☐ |
| 10 | Open any dialog | No texture bleed through | ☐ |
| 11 | Hover player row | Honolulu Blue regardless of column | ☐ |
| 12 | Switch to Draft Mode | Mine/other colors correct | ☐ |
| 13 | Reorder + Save | Works normally | ☐ |

---

## Error Handling

No new error handling needed — CSS-only changes.

---

## Open Questions

None — the init spec provides exact hex values, CSS snippets, and explicit
guidance on what stays unchanged.

---

## Rollback Plan

```bash
git revert <commit>
cd frontend && npx vite build
```

Pure CSS/JSX — no data or backend impact.

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | 10 | Exact hex values, CSS snippets, explicit unchanged-list |
| Feasibility | 10 | CSS custom properties + minimal JSX — standard React patterns |
| Completeness | 10 | All files listed, every color value specified, cascading approach clear |
| Alignment | 10 | ADR-006 gave us full CSS control specifically for this kind of work |
| **Average** | **10** | Ready for execution |

---

## Notes

### CSS Custom Property Cascade
The key insight is that `--pos-color-*` variables defined on
`.position-{pos}` cascade automatically through the DOM to all child
components. No prop drilling needed — `TierGroup.css` references
`var(--pos-color-dark)` and it resolves via DOM ancestry. This is the
cleanest approach and keeps the color definitions in one place.

### WR Keeps Honolulu Blue
WR's `--pos-color` is `#0076B6` — the same as the app's existing accent.
This is intentional: the blue column is the natural home for the app's
primary accent color. The three new colors (gold, green, orange) are
additions around it.
