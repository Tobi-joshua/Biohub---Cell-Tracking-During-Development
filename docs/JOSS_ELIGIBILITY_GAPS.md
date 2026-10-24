# JOSS eligibility gaps (preparation checklist)

Internal checklist for the maintainer—not a JOSS submission. Summarizes gaps relative to [JOSS scope](https://joss.theoj.org/about) and [submission requirements](https://joss.readthedocs.io/en/latest/submitting.html) as understood in October 2026.

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
| Author metadata (JOSS YAML) | Tobi Joshua Samuel; ORCID 0009-0007-1850-1726; email tobilobasam3@gmail.com; affiliation Independent Researcher, Ibadan, Nigeria |

## Gaps and risks (require maintainer action)

### Public development history (six months)

JOSS expects roughly **six months of public development history** before submission, with releases, issues, or pull requests visible online—not a private prototype uploaded shortly before the paper.

**Observation:** Git history in this clone spans **2026-06-30 to 2026-07-07** (about one week of commits on `main`), with `docs/CLEANUP_REPORT.md` noting a **history rewrite** on 2026-07-07.

**Impact:** Editors may defer submission until a longer, authentic public record exists—or until the author can document continuous open development elsewhere (e.g., prior public repo, tagged releases over months).

**Action:** Continue development on GitHub with dated releases/issues; avoid further history rewrites without noting them in the JOSS pre-review issue.

### Research impact, JOSS scope, and independent adoption

JOSS 2026 guidance emphasizes **demonstrable research impact**—publications, external use, integrations, or credible near-term significance such as reproducible materials and documented use in a research context.

**How this maps to `paper.md`:** The Research impact statement stays focused on **actual use** (author’s Kaggle competition work, author-verified public score **0.659**, Streamlit demo, pytest/reproducible materials, IEEE companion text). **Eligibility framing** belongs here in the checklist, not in the paper.

**Author use vs external use:** Substantive use of research software by the developer in a research context (here, the Biohub challenge) can support JOSS eligibility together with community-ready documentation and tests. **Independent adoption** by other groups strengthens the case but is not yet recorded in repository metadata.

**Observation:** Primary documented use is **author-led** participation in Biohub Cell Tracking During Development, including an **author-verified public leaderboard score of 0.659** (competition metric; see `EXPERIMENTS.md` and `paper.md`). Seven pytest cases verify pipeline behaviour on synthetic data separately from that score. A public Streamlit demo and IEEE-format companion manuscript are in-repo.

**Impact:** Reviewers may ask for third-party citations, reproduction on real Biohub volumes, or a public submission permalink.

**Action:** Encourage external users to cite a Zenodo/GitHub release; add factual adoption notes only when they exist.

### Competition evidence link (missing)

**Observation:** The author verified the **0.659 public leaderboard score** in their Kaggle account. Repository files do **not** yet include a **public submission or notebook permalink** that third parties can open without the author’s account.

**Action:** Add a stable Kaggle submission or notebook URL to `EXPERIMENTS.md`, the JOSS pre-review issue, or this checklist when available.

### Streamlit UI figure data source (JOSS paper)

**Observation:** `figures/joss_streamlit_detection_lineage.png` is built from IEEE manuscript PDF panels (Detection and Lineage). Visible sidebar state indicates **Synthetic demo** with default analysis sliders. The author should confirm this matches their intended illustration (vs a local Zarr volume) before JOSS submission.

### Dual paper formats

**Observation:** Repository contains both JOSS Markdown (`paper.md`) and IEEE LaTeX (`paper/main.tex`).

**Action:** Keep claims consistent; JOSS reviewers read `paper.md`.

### Community contributors

**Observation:** Small number of merged pull requests (#1–#4) in early July 2026; mostly single-author commit history.

**Action:** Welcome external issues/PRs; not strictly required but strengthens community signal.

### Affiliation note (not a JOSS gap)

University of Lagos is the author’s degree-awarding institution, **not** the affiliation used in `paper.md` (Independent Researcher, Ibadan, Nigeria). Do not swap these unless affiliation policy changes.

## Not blockers but review friction

- **Learned detector scaffold** is unimplemented without weights—stated in `paper.md`.
- **Hosted notebook paths** still reference Kaggle-style mounts in `Config.resolve_paths` for compatibility—acceptable if documented.
- **Binary/large data** not in repo—expected; document download steps (already in `DATA_NOTES.md`).

## Suggested pre-submission sequence

1. Keep `joss-preparation` updated until tests, paper PDF, and checklist items are satisfactory (no merge to `main` until intended).
2. Accumulate public activity (releases, issues, external users) toward the six-month history expectation.
3. Open JOSS pre-review issue with links to `paper.md`, CI badge, competition context, and submission permalink when ready.
4. Respond to reviewer requests on API docs, coverage, or real-data reproduction.
