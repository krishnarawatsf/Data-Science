FROM python:3.11-slim

WORKDIR /app

# system deps for some pandas/plotly operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PORT=8501
EXPOSE 8501

# Use shell form so the $PORT env var is expanded at runtime
CMD bash -lc "streamlit run app.py --server.port $PORT --server.headless true --server.enableCORS false"
