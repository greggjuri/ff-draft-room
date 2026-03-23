# Execute PRP

Execute a Project Requirement Plan step-by-step.

## Arguments
- `$ARGUMENTS` - Path to PRP file (e.g., `prps/prp-feature-name.md`)

## Instructions

You are executing a PRP for the **FF Draft Room** project — a local Python/Streamlit fantasy football draft tool running on macOS M1.

### Step 0: Pre-flight Checks

Before starting:
1. Read `CLAUDE.md` for Streamlit patterns and coding conventions
2. Read the PRP at `$ARGUMENTS` completely
3. Verify all dependencies (previous PRPs) are complete
4. Check confidence score ≥ 7 (if not, stop and report)
5. Verify `streamlit` and `pandas` are installed: `pip list | grep -E "streamlit|pandas|plotly"`

### Step 1: Execute Implementation Steps

For each implementation step in the PRP:

1. **Announce**: State which step you're starting
2. **Implement**: Write the code following CLAUDE.md patterns
3. **Validate**: Run tests and lint after each step
4. **Commit**: Atomic commit after validation passes

```bash
# After each step
pytest tests/ -q                    # Run tests
ruff check app/ tests/              # Lint check
git add .
git commit -m "{type}: {description}"
```

### Step 2: Streamlit-Specific Patterns

Always follow these patterns:

```python
# Cache all data loading
@st.cache_data
def load_players(position: str, year: int) -> pd.DataFrame:
    ...

# Initialize session state in main.py, not page files
if "rankings" not in st.session_state:
    st.session_state.rankings = {}

# Use pathlib for all file paths
from pathlib import Path
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "players"

# Graceful missing file handling
try:
    df = pd.read_csv(path)
except FileNotFoundError:
    st.warning(f"Data file not found: {path.name}")
    return pd.DataFrame()
```

### Step 3: Handle Failures

If a step fails:
1. **Diagnose**: Check terminal output from `streamlit run` for tracebacks
2. **Fix**: Minimal change to resolve
3. **Document**: Note issue in commit message
4. **Continue**: Only proceed when step validates

If Streamlit-specific errors occur:
- `SessionStateError`: State being modified outside callback — restructure
- `CachedWidgetWarning`: Widget inside cached function — move outside cache
- `ScriptRunContext`: Threading issue — use `st.session_state` properly

If unable to proceed:
1. Report blocker clearly
2. Suggest potential solutions
3. Ask for guidance

### Step 4: Run Integration Tests

After all implementation steps:

1. Start app: `streamlit run app/main.py`
2. Open `http://localhost:8501`
3. Execute each step in the Integration Test Plan
4. Record pass/fail
5. Fix failures before proceeding

### Step 5: Final Validation

```bash
pytest tests/ --cov=app --cov-report=term-missing
ruff check app/ tests/
streamlit run app/main.py  # Manual full smoke test
```

Verify:
- [ ] All tests pass
- [ ] Coverage ≥ 80% for `app/utils/`
- [ ] No lint errors
- [ ] All success criteria met
- [ ] No debug output remaining (`st.write(...)`, `print(...)`)

### Step 6: Update Documentation

1. Update `docs/TASK.md`:
   - Move task to "Recently Completed"
   - Add learnings to "Architecture Decisions" if applicable

2. If new architectural decisions made:
   - Add ADR to `docs/DECISIONS.md`

### Step 7: Report Completion

```
## PRP Execution Complete

**PRP**: prps/prp-{feature}.md
**Status**: Complete/Partial/Blocked

### Commits Made
- {hash}: {message}
- {hash}: {message}

### Tests
- Unit: X passing, Y% coverage on utils
- Integration: X/Y manual steps passing

### Success Criteria
- [x] Criterion 1
- [x] Criterion 2
- [ ] Criterion 3 (explain if incomplete)

### Issues Encountered
{Issues and resolutions}

### Follow-up Items
{Next tasks or items for TASK.md}
```

## Commit Message Format

```
feat: add historical stats browser page
fix: handle missing CSV file gracefully in data_loader
refactor: extract player table into reusable component
test: add unit tests for VOR calculation
docs: update TASK.md with completed history browser
chore: add .streamlit/config.toml dark theme
```

## Quality Standards

- **No file over 500 lines**: Split if approaching
- **Tests for utils**: 80% coverage minimum
- **Streamlit patterns**: cache + session state per CLAUDE.md
- **Working commits**: App runs after every commit
- **No hardcoded paths**: Use `pathlib.Path` relative to project root

## Emergency Stop

Stop and report before proceeding if you encounter:
- A need for an external API call (violates ADR-003)
- A database requirement (violates ADR-002)
- A contradiction with existing ADRs
- A Streamlit limitation that breaks the feature design
- File approaching 500 lines without a clear split plan

## Notes

- Test on macOS M1 — verify arm64 compatibility for any new dependencies
- The app is personal/local — no auth, no multi-user concerns
- Data CSVs in `data/players/` are read-only source of truth — never modify them
- Rankings JSON in `data/rankings/` is user data — handle corruption gracefully
