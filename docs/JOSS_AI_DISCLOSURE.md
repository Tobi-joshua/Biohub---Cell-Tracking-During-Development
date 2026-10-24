# AI usage disclosure (JOSS preparation)

Supports the **AI usage disclosure** section in `paper.md`. Covers Cursor-assisted work on the **`joss-preparation`** branch.

## Generative AI on this branch

| Activity | Tool | Role | Verification |
|----------|------|------|--------------|
| JOSS branch setup | Cursor Cloud Agent (Composer) | Tests, reproducible example doc, `paper.md` / `paper.bib`, CI workflow, JSON export fix | Pytest (7 cases); Open Journals PDF action on push |
| Paper drafting and revision | Same | Technical sections from `src/biohub/`, README, `EXPERIMENTS.md`, IEEE manuscript | PDF rebuild in GitHub Actions |
| Author metadata | Author commit `f49fd3e` + agent passes | ORCID, email, Ibadan affiliation in `paper.md` YAML | Author-supplied details (Oct 2026) |
| Competition wording | Same + author statement | Author-verified 0.659 public score language; no agent Kaggle access | Not independently checked by agent |
| UI figure for JOSS | Same | Extracted Detection/Lineage panels from author IEEE PDF via `scripts/build_joss_streamlit_figure.py`; no fabricated screenshots | Visual check in compiled `paper.pdf` |

## Unresolved questions for the author

These are **not** answered in repository metadata. Do not infer “no AI use” or complete human re-validation until you confirm:

1. Did generative AI assist **earlier** commits, notebooks, `paper/main.tex`, Streamlit UI text, or figures before the JOSS branch?
2. Was the IEEE manuscript PDF (source of Streamlit screenshots) produced with AI-assisted writing or editing?
3. Have you line-by-line re-validated all AI-drafted prose in `paper.md` and related docs?
4. Are funding sources absent from the repository, or simply undocumented?
5. Does the **Synthetic demo** label in the JOSS UI figure accurately represent the session you want cited (vs local Biohub Zarr data)?

`docs/CLEANUP_REPORT.md` records agent-related branch cleanup and a **2026-07-07 history rewrite** on `main`.

## Author-verified facts (outside agent access)

- **Public leaderboard score 0.659** on Biohub Cell Tracking During Development—verified by the author in their Kaggle account (Oct 2026). Agents did not log into Kaggle.
- **Missing for public audit:** permalink to the competition submission or notebook (`docs/JOSS_ELIGIBILITY_GAPS.md`).
