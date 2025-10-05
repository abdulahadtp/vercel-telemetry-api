from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from pathlib import Path

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load the telemetry data once when the server starts
try:
    # The path goes from api/index.py up to the root to find the file
    base_path = Path(__file__).parent.parent
    telemetry_df = pd.read_json(base_path / 'telemetry.json')
except Exception:
    telemetry_df = None

# Define the structure of the incoming JSON request body
class TelemetryRequest(BaseModel):
    regions: list[str]
    threshold_ms: int

@app.post("/api")
def get_telemetry_metrics(request: TelemetryRequest):
    results = {}
    if telemetry_df is None:
        return {"error": "Telemetry data not loaded."}

    for region in request.regions:
        region_df = telemetry_df[telemetry_df['region'] == region]

        if not region_df.empty:
            # Calculate all the required metrics
            avg_latency = region_df['latency_ms'].mean()
            p95_latency = region_df['latency_ms'].quantile(0.95)
            avg_uptime = region_df['uptime_pct'].mean()
            breaches = int((region_df['latency_ms'] > request.threshold_ms).sum())

            results[region] = {
                "avg_latency": avg_latency,
                "p95_latency": p95_latency,
                "avg_uptime": avg_uptime,
                "breaches": breaches
            }

    return results