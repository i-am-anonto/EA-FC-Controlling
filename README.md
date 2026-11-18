# FC 27 Tactical Playbook
A lightweight, zero-cost Python companion app for EAFC 27 players. Built entirely on an in-memory NLP architecture, it avoids database subscriptions, user accounts, and API fees. 

## Architecture
- **UI:** Streamlit with injected DOM components (WebSpeech API, PWA Manifest).
- **Database:** Local static `EAFC_27_Complete_Controls_2.csv`.
- **Search Engine:** A weighted hybrid ranker using `all-MiniLM-L6-v2` for dense semantic embeddings, `rank_bm25` for sparse keyword frequency, and `rapidfuzz` to correct mid-match spelling errors.
- **Visuals:** Python string parser dynamically generates dark-mode CSS-animated SVGs representing controller stick paths.

## Deployment (Zero Cost)
1. Push this repository to GitHub.
2. Connect to **Streamlit Community Cloud** or **Hugging Face Spaces**.
3. Deploy directly from the `main` branch. 
4. The PWA `manifest.json` handles mobile-first installability so users can save it as an offline home screen app.

## Benchmark Results
Run `python benchmark.py` to test NLP configurations. 
*(Paste benchmark_readme_table.txt contents here)*