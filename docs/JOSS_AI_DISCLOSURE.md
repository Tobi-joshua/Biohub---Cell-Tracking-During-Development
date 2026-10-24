# AI usage disclosure (JOSS preparation)

This document supports the **AI usage disclosure** section required in JOSS papers. It covers assistance during the **`joss-preparation` branch** work described in the Cloud Agent task (October 2026) and flags repository history that may imply earlier AI-assisted development.

## Generative AI in this preparation session

| Activity | Tool / context | How it was used | Verification |
|----------|----------------|-----------------|--------------|
| JOSS branch implementation | Cursor Cloud Agent (Composer) | Read JOSS documentation, inspected the codebase, added pytest suites on synthetic ground truth, wrote `docs/REPRODUCIBLE_EXAMPLE.md`, drafted `paper.md` / `paper.bib`, added GitHub Actions workflow, fixed JSON export tuple serialization in `src/biohub/export.py` | All tests run locally via `PYTHONPATH=src python3 -m pytest tests/ -v` (7 passed). Paper compiles in CI via Open Journals draft action. |
| Paper prose | Same agent | Drafted JOSS sections from repository evidence only (README, EXPERIMENTS.md, source modules) | **Author must review** every claim, affiliation, and impact statement before submission. |
| Citations | Same agent | Selected widely used related software papers; bib entries copied/adapted from existing `paper/references.bib` | **Author must confirm** completeness and that no citation invents usage or benchmarks. |

The submitting author should paste a shortened version of the above into `paper.md` or expand it per [JOSS paper guidance](https://joss.readthedocs.io/en/latest/paper.html).

## Items requiring author confirmation (earlier work)

The repository contains signals of **prior AI- or agent-assisted engineering** that this session did **not** independently audit:

1. **`docs/CLEANUP_REPORT.md`** — Documents removal of agent-specific branches, replacement of `EXPERIMENTS.md`, and a **2026-07-07 history rewrite** on `main` (force-push). Confirm whether generative AI contributed to earlier commits, notebooks, or documentation before stating "no AI use" globally.
2. **Commit messages and sprint-style docs** — References to automated tuning sweeps and leaderboard optimization may reflect AI-paired development; disclose if tools such as Cursor, Copilot, or chat assistants were used.
3. **IEEE manuscript (`paper/main.tex`)** — If any section was AI-drafted originally, note that here and describe human review.
4. **Streamlit app copy and figures** — Confirm whether UI text or generated figures used AI image or text tools.

If no earlier AI tools were used, the author may state explicitly: *"No generative AI was used outside the October 2026 JOSS preparation session listed above."*

## Recommended author action before JOSS submission

- Review and edit `paper.md` for accuracy, affiliations, and ORCID metadata.
- Confirm competition score claims with stable URLs or screenshots.
- Merge or adjust this disclosure in the final JOSS paper YAML/body as editors expect a single authoritative statement.
