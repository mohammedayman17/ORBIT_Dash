# ORBIT | Astronaut Sleep Monitor

A minimal, dark mission-control style dashboard built with Streamlit, Pandas, and Plotly.

## Included
- `orbit_dash.py` — interactive dashboard
- `nasa_spaceapps_astronaut_sleep_health.csv` — supplied synthetic dataset
- `requirements.txt` — Python dependencies

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. (Recommended) Create and activate a virtual environment:

   macOS/Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Windows:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Start the dashboard:
   ```bash
   streamlit run app.py
   ```

Streamlit will open the dashboard in your browser. If it does not, visit the local URL printed in the terminal (usually http://localhost:8501).

## Deploy
Push this folder to a GitHub repository and deploy it through Streamlit Community Cloud. Set the app entry point to `orbit_dash.py`.

## Notes
- The dashboard supports the included CSV automatically.
- You can also upload a compatible CSV from the sidebar.
- The dataset is synthetic. Avoid presenting relationships as causal or as validated medical findings.
