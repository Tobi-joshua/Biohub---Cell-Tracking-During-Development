# AI usage disclosure (JOSS preparation)

Supports the **AI usage disclosure** section in `paper.md`. Covers Cursor-assisted work on the **`joss-preparation`** branch and items the author has not yet fully confirmed.

## Generative AI on this branch

| Activity | Tool | Role | Verification |
|----------|------|------|--------------|
| JOSS branch setup | Cursor Cloud Agent (Composer) | Tests, `docs/REPRODUCIBLE_EXAMPLE.md`, `paper.md` / `paper.bib`, CI workflow, JSON export fix | `PYTHONPATH=src python3 -m pytest tests/ -v` (7 tests); Open Journals PDF action on push |
| Paper drafting and revision | Same | Technical sections from `src/biohub/`, README, `EXPERIMENTS.md`, IEEE manuscript | PDF rebuild in GitHub Actions; author review of claims |
| Author metadata pass | Same + author commit `f49fd3e` | ORCID, email, Ibadan affiliation in `paper.md` YAML | Matches author-supplied details (Oct 2026) |
| Competition wording update | Same | Author-verified 0.659 public score language; no agent access to Kaggle | Wording per author statement; no independent account check by agent |

## Not confirmed by the author or repository

- Whether generative AI contributed to **earlier** commits, notebooks, `paper/main.tex`, Streamlit UI text, or figures before the JOSS branch.
- Whether **all** AI-assisted prose was line-by-line re-validated by the author (the paper does not claim complete human re-validation).
- **Funding**: repository metadata does not describe grants; the paper does not assert absence of external funding.

`docs/CLEANUP_REPORT.md` records agent-related branch cleanup and a **2026-07-07 history rewrite** on `main`.

## Author-verified facts (outside agent access)

- **Public leaderboard score 0.659** on Biohub Cell Tracking During Development—verified by the author in their Kaggle account (Oct 2026). Agents did not log into Kaggle.
- **Missing for public audit:** permalink to the competition submission or notebook (track in `docs/JOSS_ELIGIBILITY_GAPS.md`).
