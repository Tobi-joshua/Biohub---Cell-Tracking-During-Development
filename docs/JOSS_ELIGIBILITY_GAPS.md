# JOSS eligibility gaps (draft assessment)

This is an **internal checklist** for the maintainer—not a JOSS submission. It summarizes gaps relative to [JOSS scope](https://joss.theoj.org/about) and [submission requirements](https://joss.readthedocs.io/en/latest/submitting.html) as understood in October 2026.

## Likely satisfied today

| Requirement | Evidence in repository |
|-------------|------------------------|
| OSI license | MIT [`LICENSE`](../LICENSE) |
| Public source + issues | GitHub repository linked from `README.md` |
| Research application | 3D cell tracking / lineage reconstruction for developmental microscopy |
| Tests | `tests/` with pytest on synthetic ground truth (7 tests) |
| Documentation | `README.md`, `DATA_NOTES.md`, `docs/REPRODUCIBLE_EXAMPLE.md`, `CONTRIBUTING.md` |
| Paper source in repo | `paper.md`, `paper.bib` on `joss-preparation` branch |
| Automated paper build | `.github/workflows/joss-preparation.yml` |

## Gaps and risks (require maintainer action)

### Public development history (six months)

JOSS expects roughly **six months of public development history** before submission, with releases, issues, or pull requests visible online—not a private prototype uploaded shortly before the paper.

**Observation:** Git history in this clone spans **2026-06-30 to 2026-07-07** (about one week of commits on `main`), with `docs/CLEANUP_REPORT.md` noting a **history rewrite** on 2026-07-07.

**Impact:** Editors may defer submission until a longer, authentic public record exists—or until the author can document continuous open development elsewhere (e.g., prior public repo, tagged releases over months).

**Action:** Continue development on GitHub with dated releases/issues; avoid further history rewrites without noting them in the JOSS pre-review issue.

### Demonstrated research use beyond the author

JOSS 2026 guidance emphasizes **demonstrable research impact** (external users, publications, integrations)—not only aspirational statements.

**Observation:** Documented use is primarily **author-led**: Biohub competition logs in `EXPERIMENTS.md`, Streamlit demo, and an IEEE-style preprint manuscript in `paper/main.tex` without a listed DOI.

**Impact:** Reviewers may ask for third-party adoption, citations, or independent reproduction on real Biohub volumes.

**Action:** Encourage collaborators to cite a Zenodo/GitHub release; publish methods preprint or link competition notebooks; add anonymized user testimonials only if factual.

### Author metadata

**Observation:** `paper.md` lists a single independent author; ORCID and institutional affiliation are placeholders.

**Action:** Add ORCID, correct affiliation, and corresponding-author contact before submission.

### Dual paper formats

**Observation:** Repository contains both JOSS Markdown (`paper.md`) and IEEE LaTeX (`paper/main.tex`).

**Action:** Ensure claims stay consistent; JOSS reviewers read `paper.md`, not `main.tex`.

### Competition score evidence

**Observation:** Public score **0.659** is recorded in `EXPERIMENTS.md` but may need a **permalink** to the competition leaderboard entry.

**Action:** Attach verifiable links or screenshots in the JOSS pre-review issue; do not cite scores that cannot be checked.

### Community contributors

**Observation:** Small number of merged pull requests (#1–#4) in early July 2026; mostly single-author commit history.

**Action:** Welcome external issues/PRs; not strictly required but strengthens community signal.

## Not blockers but review friction

- **Learned detector scaffold** is unimplemented without weights—state clearly in paper (done).
- **Hosted notebook paths** still reference Kaggle-style mounts in `Config.resolve_paths` for compatibility—acceptable if documented.
- **Binary/large data** not in repo—expected; document download steps (already in `DATA_NOTES.md`).

## Suggested timeline (process, not calendar)

1. Merge `joss-preparation` when satisfied with tests and paper draft (user requested **no merge to main** during this task).
2. Accumulate public activity (releases, issues, external users).
3. Open JOSS pre-review issue with links to `paper.md`, test badge, and impact evidence.
4. Respond to reviewer requests on API docs, coverage, or real-data reproduction.
