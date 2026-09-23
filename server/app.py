import json
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from server.schemas import TelemetrySyncRequest, NudgeResponse
from server.nudge_engine import AICoachNudgeEngine
from server.database import DatabaseManager

app = FastAPI(
    title="Jarvis AI Coach API",
    description="FastAPI Backend for mobile & desktop telemetry ingestion and AI Coach personalized nudges.",
    version="1.0.0",
)

# Enable CORS for mobile app & local web UI calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager()
nudge_engine = AICoachNudgeEngine()


@app.get("/")
def read_root():
    return {
        "name": "Jarvis AI Coach API",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/api/v1/telemetry/sync", response_model=NudgeResponse)
def sync_telemetry(payload: TelemetrySyncRequest):
    """Ingest telemetry payload from Android app or desktop activity monitor,

    log data to persistent store, and return generated AI Coach nudges.
    """
    try:
        # Save telemetry sync snapshot
        db.save_telemetry_sync(
            client_id=payload.client_id,
            platform=payload.platform,
            ts=payload.timestamp,
            payload_json=payload.model_dump_json(),
        )

        # Generate nudges
        nudges = nudge_engine.generate_nudges(payload)

        # Persist nudges
        for nudge in nudges:
            db.save_nudge(
                nudge_id=nudge.id,
                category=nudge.category,
                message=nudge.message,
                priority=nudge.priority,
                suggested_action=nudge.suggested_action or "",
                ts=nudge.created_at,
            )

        return NudgeResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            nudges=nudges,
            total=len(nudges),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Telemetry sync failed: {str(e)}")


@app.post("/api/v1/nudges/generate", response_model=NudgeResponse)
def generate_nudges(payload: TelemetrySyncRequest):
    """Generate personalized AI coach nudges on demand for a given telemetry context."""
    try:
        nudges = nudge_engine.generate_nudges(payload)
        return NudgeResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            nudges=nudges,
            total=len(nudges),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nudge generation failed: {str(e)}")


@app.get("/api/v1/nudges/recent")
def get_recent_nudges(limit: int = 10):
    """Retrieve recent persistent nudges."""
    return {"nudges": db.get_recent_nudges(limit=limit)}
