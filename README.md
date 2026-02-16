# Bike Sales Dashboard

Interactive Streamlit dashboard for Bike Sales analysis using `Sales.csv`.

## Setup

1. (Optional) Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Place your `Sales.csv` file in one of these locations (in order of preference):
- `bike-sales-dashboard/data/Sales.csv`
- `bike-sales-dashboard/Sales.csv`
- Root workspace `Sales.csv` (it will attempt to locate)

4. Run the app

```bash
cd "$(dirname "$0")"
streamlit run app.py
```

## Notes
- The app will prompt for file upload if `Sales.csv` is not found.
- For best results ensure `Date` column is present and parsable.

## Running (optimized)

Development (fast feedback):

```bash
# create and activate venv (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Production (stable / headless):

```bash
# run headless on port 8501 and disable CORS for reverse-proxy setups
streamlit run app.py --server.headless true --server.port 8501 --server.enableCORS false
```

Docker (recommended for production):

```bash
docker build -t bike-sales-dashboard:latest .
docker run -p 8501:8501 --env PORT=8501 --rm bike-sales-dashboard:latest
```

Optimizations applied / recommended:
- Uses `@st.cache_data` to cache loaded/processed data (already implemented).
- Added a Streamlit config file (`.streamlit/config.toml`) to set sensible server defaults.
- Prefer running in a container for reproducibility; use a reverse proxy (Nginx) for TLS and buffering in production.
- Keep `Sales.csv` in the `data/` folder and avoid large uploads; preprocess and save reduced datasets if needed.

If you want, I can also add a `docker-compose.yml`, a sample Nginx proxy, or tune cache behavior further.
