# Generate PRP

Generate a comprehensive Project Requirement Plan (PRP) for a feature.

## Arguments
- `$ARGUMENTS` - Path to initial file (e.g., `initials/init-feature-name.md`)

## Instructions

You are generating a PRP for the **FF Draft Room** project — a local Python/Streamlit fantasy football draft tool.

### Step 1: Gather Context

Read and internalize the following project documentation:
1. `CLAUDE.md` — Coding conventions, file structure, Streamlit patterns
2. `docs/PLANNING.md` — Architecture, data model, dev phases
3. `docs/DECISIONS.md` — ADRs (especially ADR-001 Streamlit, ADR-002 JSON, ADR-003 CSV data)
4. `docs/TASK.md` — Current task status
5. `docs/TESTING.md` — Testing standards and patterns

### Step 2: Read the Initial File

Read the init spec at `$ARGUMENTS`:
1. Understand the feature requirements
2. Verify all open questions are answered
3. Identify integration points with existing pages/utils
4. Note Streamlit-specific constraints

### Step 3: Research Codebase

1. Check `app/utils/` for existing utilities to reuse or extend
2. Check `app/pages/` for existing page patterns
3. Check `app/components/` for reusable components
4. Check `tests/` for existing test patterns to follow
5. Check `data/players/` for available CSV files

### Step 4: Generate PRP

Create `prps/prp-{feature-slug}.md` using `prps/templates/prp-template.md`.

Fill in all sections with FF Draft Room specifics:
1. **Overview** — Clear problem + solution
2. **Success Criteria** — Measurable, testable outcomes (include pytest pass + app starts)
3. **Context** — Reference specific ADRs, existing files
4. **Technical Specification** — Data model, session state keys, util functions, Streamlit layout
5. **Implementation Steps** — Ordered, atomic, with exact file paths
6. **Testing Requirements** — Unit tests for utils, manual tests for UI
7. **Integration Test Plan** — Specific `streamlit run` manual steps
8. **Error Handling** — Missing files, bad JSON, column mismatches
9. **Open Questions** — Block on anything unclear
10. **Rollback Plan** — git revert steps

### Step 5: Score Confidence

Score 1-10 on each dimension:
- **Clarity**: Requirements unambiguous for this Streamlit app?
- **Feasibility**: Works within Streamlit constraints + local-only architecture?
- **Completeness**: All files, tests, and session state covered?
- **Alignment**: Consistent with all ADRs, especially ADR-001/002/003?

**If average < 7**: List concerns, ask clarifying questions, do NOT proceed.

### Step 6: Output

1. Create PRP file at `prps/prp-{feature-slug}.md`
2. Report file path
3. Display confidence scores
4. List any open questions or concerns

## Quality Checklist

Before completing:
- [ ] Every step has specific file paths
- [ ] Steps are atomic and individually validatable
- [ ] Unit tests cover utils functions (not Streamlit UI)
- [ ] Integration test plan uses `streamlit run` manual steps
- [ ] No ADRs contradicted (especially: no external APIs, no database, no drag-and-drop assumptions)
- [ ] Session state keys documented
- [ ] Rollback plan exists

## Example Usage

```
/generate-prp initials/init-project-setup.md
/generate-prp initials/init-history-browser.md
/generate-prp initials/init-war-room-rankings.md
```
