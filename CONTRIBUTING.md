# Contributing

Thank you for your interest in **Biohub Cell Lineage Tracker**.

## Development setup

```bash
git clone https://github.com/Tobi-joshua/Biohub---Cell-Tracking-During-Development.git
cd Biohub---Cell-Tracking-During-Development
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

Run the app: `streamlit run app.py`

## Project layout

| Path | Purpose |
|------|---------|
| `src/biohub/` | Core detection, tracking, export, and validation |
| `app.py` | Streamlit application |
| `scripts/` | Figure generation, notebook builder, tuning utilities |
| `paper/` | IEEE manuscript source |
| `tests/` | *(planned)* unit and integration tests |

## Pull requests

1. Fork the repository and create a feature branch from `main`.
2. Keep changes focused; match existing code style and naming.
3. Update `CHANGELOG.md` for user-visible changes.
4. Ensure `streamlit run app.py` starts without errors.
5. Open a pull request with a clear description and screenshots for UI changes.

## Branch naming

Use descriptive branch names, for example:

- `feature/gap-closing-tuning`
- `fix/detection-threshold`
- `docs/paper-figures`

## Reporting issues

Include:

- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or screenshots

## Code of conduct

Be respectful and constructive. This is a research software project intended for open collaboration.
