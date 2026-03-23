# PRP Template

## PRP-XXX: {Feature Name}

**Created**: {YYYY-MM-DD}
**Initial**: `initials/init-{feature}.md`
**Status**: Draft/Ready/In Progress/Complete

---

## Overview

### Problem Statement
{What problem are we solving? Copy/adapt from init spec.}

### Proposed Solution
{High-level description of what we're building in the FF Draft Room.}

### Success Criteria
- [ ] {Criterion 1 — testable}
- [ ] {Criterion 2 — testable}
- [ ] {Criterion 3 — testable}
- [ ] All unit tests pass (`pytest tests/ -q`)
- [ ] App starts cleanly: `streamlit run app/main.py`

---

## Context

### Related Documentation
- `docs/PLANNING.md` — Architecture overview, data model
- `docs/DECISIONS.md` — ADR-001 (Streamlit), ADR-002 (JSON persistence), ADR-003 (CSV data source)
- {Any additional relevant ADRs}

### Dependencies
- **Required**: {Features/PRPs that must be complete first}
- **Optional**: {Features that enhance but aren't required}

### Files to Modify/Create
```
app/pages/{page}.py              # Description
app/utils/{util}.py              # Description
app/components/{component}.py    # Description
tests/test_{name}.py             # NEW: unit tests
```

---

## Technical Specification

### Data Model Changes
```python
# New or modified dataclass/schema
@dataclass
class {ModelName}:
    field: type
    optional_field: type | None = None
```

### Session State Keys
```python
# Keys added to st.session_state by this feature
st.session_state["{key}"] = {type}  # Description
```

### New Utility Functions
```python
# app/utils/{util}.py
def function_name(param: type) -> return_type:
    """Docstring."""
    pass
```

### Streamlit Component Structure
```
# Page layout description
st.sidebar: {sidebar content}
main area:
  - {component 1}
  - {component 2}
  - {component 3}
```

---

## Implementation Steps

### Step 1: {First Step Title}
**Files**: `app/utils/{util}.py`, `tests/test_{util}.py`

{Detailed description of what to implement.}

```python
# Key code pattern or pseudocode
def example():
    pass
```

**Validation**:
```bash
pytest tests/test_{util}.py -v
ruff check app/utils/{util}.py
```
- [ ] Tests pass
- [ ] No lint errors

---

### Step 2: {Second Step Title}
**Files**: `app/pages/{page}.py`

{Detailed description.}

**Validation**:
```bash
streamlit run app/main.py
# Navigate to {page} — verify manually
```
- [ ] Page loads without error
- [ ] {Specific UI behavior works}

---

### Step 3: {Third Step Title}
**Files**: `app/components/{component}.py`

{Detailed description.}

**Validation**:
- [ ] {Specific validation}

---

### Step N: Final Integration Check
**Commands**:
```bash
pytest tests/ --cov=app --cov-report=term-missing
streamlit run app/main.py
```

**Validation**:
- [ ] All tests pass, coverage ≥ 80% for utils
- [ ] Full manual test checklist from TESTING.md completed
- [ ] No debug output (`st.write`, `print`) left in code

---

## Testing Requirements

### Unit Tests
```
tests/test_{feature}.py:
  - test_{function}_happy_path: {Description}
  - test_{function}_missing_file: {Description}
  - test_{function}_invalid_input: {Description}
```

### Manual Streamlit Tests
- {Scenario 1}: {Steps to verify}
- {Scenario 2}: {Steps to verify}

---

## Integration Test Plan

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Start app: `streamlit run app/main.py` | Loads at localhost:8501, no errors | ☐ |
| 2 | Navigate to {page} | Page renders correctly | ☐ |
| 3 | {User action} | {Expected result} | ☐ |
| 4 | {Error case} | Graceful error message | ☐ |

---

## Error Handling

| Error | Cause | Handling |
|-------|-------|---------|
| FileNotFoundError | Missing CSV | `st.warning`, return empty DataFrame |
| json.JSONDecodeError | Corrupt profile | `st.error`, return None |
| KeyError on DataFrame | Column mismatch | Log + `st.error` with column name |

---

## Open Questions

- [ ] {Question needing answer before implementation}

---

## Rollback Plan

1. `git revert {commit}` — revert feature commit
2. `streamlit run app/main.py` — verify app still starts
3. Delete any new JSON profiles created during testing if needed

---

## Confidence Scores

| Dimension | Score (1-10) | Notes |
|-----------|--------------|-------|
| Clarity | X | Are requirements unambiguous? |
| Feasibility | X | Compatible with Streamlit + current architecture? |
| Completeness | X | All aspects covered? |
| Alignment | X | Consistent with ADRs + project goals? |
| **Average** | **X** | |

{If average < 7, list specific concerns before proceeding}

---

## Notes

{Additional context or considerations}
