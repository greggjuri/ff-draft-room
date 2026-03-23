# Init Template - Feature Specification

## init-XX: {Feature Name}

**Created**: {YYYY-MM-DD}
**Priority**: {High/Medium/Low}
**Depends On**: {init-YY, or "None"}

---

## Problem Statement

{What problem does this feature solve within the FF Draft Room? Why is it needed? 1-3 sentences.}

## Goal

{What will be true when this feature is complete? What can the user do in the app?}

## Requirements

### Must Have (P0)
1. {Requirement 1}
2. {Requirement 2}
3. {Requirement 3}

### Should Have (P1)
1. {Requirement 4}
2. {Requirement 5}

### Nice to Have (P2)
1. {Requirement 6}

## User Stories

**As a** fantasy football drafter  
**I want to** {action in the app}  
**So that** {benefit to draft preparation or live draft}

## Technical Considerations

### Data Changes
- {New fields needed in player schema, rankings JSON, or CSV normalization}
- {Changes to existing data structures}

### Streamlit Changes
- {New page or component}
- {Changes to existing pages/sidebar}
- {Session state keys needed}

### Utils Changes
- {New utility functions}
- {Changes to data_loader.py, rankings.py, vor.py, constants.py}

### Files to Create/Modify
```
app/pages/{page_name}.py         # New page or changes
app/utils/{util_name}.py         # New or modified util
app/components/{component}.py    # New or modified component
tests/test_{name}.py             # New tests
```

## Constraints

- No external API calls — fully offline
- Must work with existing FantasyPros CSV format
- 500-line file limit — plan modular split if needed
- Streamlit cache and session state patterns from CLAUDE.md

## Success Criteria

- [ ] {Testable criterion 1}
- [ ] {Testable criterion 2}
- [ ] {Testable criterion 3}
- [ ] All unit tests pass (`pytest tests/ -q`)
- [ ] App starts without error after change

## Out of Scope

{Explicitly list what this feature does NOT include}

- {Not included 1}
- {Not included 2}

## Open Questions

- [ ] {Question 1 — answer before generating PRP}
- [ ] {Question 2}

## Notes

{Additional context, UI mockup description, or references to research findings}

---

## Template Usage

1. Copy to `initials/init-{feature-name}.md`
2. Fill all sections (delete Notes if empty)
3. Answer all open questions before generating PRP
4. In Claude Code: `/generate-prp initials/init-{feature}.md`
