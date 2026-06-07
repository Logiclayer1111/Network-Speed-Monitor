"""
FastAPI REST API Server
Provides endpoints for frontend dashboard
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.db_manager import DatabaseManager

# Global database instance
db = DatabaseManager()

# Process start time for uptime tracking
PROCESS_START_TIME = time.time()

# ============ Pydantic Models ============

class SpeedSample(BaseModel):
    timestamp: int
    download_mbps: float
    upload_mbps: float
    latency_ms: int
    packet_loss: Optional[float] = 0

class DailyAggregate(BaseModel):
    date: str
    window_start: int
    avg_download: float
    avg_upload: float
    avg_latency: float
    sample_count: int

class HealthResponse(BaseModel):
    status: str
    samples_collected: int
    last_update: str
    uptime_hours: float
    db_size_mb: float

# ============ FastAPI App Setup ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("Starting Network Speed Monitor API...")
    
    # Start background aggregator
    # Use absolute-import fallback that works whether this file is run as a module or script.
    try:
        from backend.api.aggregator import start_aggregator  # type: ignore
    except Exception:
        from api.aggregator import start_aggregator  # type: ignore
    start_aggregator()
    
    yield
    
    # Cleanup
    print("Shutting down API...")

app = FastAPI(
    title="Network Speed Monitor API",
    description="API for network speed monitoring dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ API Endpoints ============

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Network Speed Monitor API",
        "version": "1.0.0",
        "endpoints": [
            "/api/daily/{date}",
            "/api/week",
            "/api/worst-times",
            "/api/stats",
            "/api/health"
        ]
    }

@app.get("/api/daily/{date}")
async def get_daily_speed(
    date: str,  # YYYY-MM-DD
    resolution: str = Query("minute", regex="^(minute|15min)$")
):
    """
    Get speed data for a specific day
    
    - **date**: Date in YYYY-MM-DD format
    - **resolution**: 'minute' for raw data or '15min' for aggregates
    """
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
        
        data = db.get_samples_by_date(date, resolution)
        
        if not data and resolution == "minute":
            # Return empty array instead of 404
            return JSONResponse([])
        
        return JSONResponse(data)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

@app.get("/api/week")
async def get_week_data(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format")
):
    """Get last 7 days of aggregated data"""
    try:
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
        
        data = db.get_week_data(start_date)
        return JSONResponse(data)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

@app.get("/api/worst-times")
async def get_worst_times(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    window_minutes: int = Query(15, ge=5, le=60, description="Time window in minutes")
):
    """Identify worst performing time windows"""
    data = db.get_worst_times(days, window_minutes)
    return JSONResponse({
        "analysis_window_days": days,
        "window_minutes": window_minutes,
        "worst_periods": data
    })

@app.get("/api/stats")
async def get_statistics():
    """Get overall statistics"""
    stats = db.get_stats()
    return JSONResponse(stats)

@app.get("/api/health")
async def get_health():
    """Health check endpoint"""
    stats = db.get_stats()
    
    # Calculate database size
    db_size = 0
    if os.path.exists(db.db_path):
        db_size = os.path.getsize(db.db_path) / (1024 * 1024)
    
    uptime_hours = (time.time() - PROCESS_START_TIME) / 3600
    
    return HealthResponse(
        status="healthy",
        samples_collected=stats['total_samples'],
        last_update=str(stats['last_sample']['timestamp']) if stats['last_sample'] else "Never",
        uptime_hours=round(uptime_hours, 1),
        db_size_mb=round(db_size, 2)
    )

@app.get("/api/export")
async def export_data(
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD")
):
    """Export data to CSV"""
    try:
        # Validate dates
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
        
        # Create exports directory
        export_dir = Path(__file__).parent.parent / "exports"
        export_dir.mkdir(exist_ok=True)
        
        filename = f"speedmon_export_{start_date}_to_{end_date}.csv"
        filepath = export_dir / filename
        
        rows_exported = db.export_to_csv(start_date, end_date, str(filepath))
        
        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type="text/csv"
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/adapters")
async def get_adapters():
    """Get list of detected adapters"""
    from poller.adapter_detector import AdapterDetector
    
    detector = AdapterDetector()
    adapters = detector.get_all_adapters_info()
    
    return JSONResponse({
        "adapters": adapters,
        "selected_adapter": detector.get_active_physical_adapter()
    })

# ============ Main Entry Point ============

if __name__ == "__main__":
    # Print registered routes to help diagnose subprocess startup issues
    print("Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(route.path)

    import uvicorn
    
    # Avoid extended Unicode characters which can crash console encoding in subprocess tests.
    print("Network Speed Monitor API Server")
    print("API Docs: http://localhost:8000/docs")
    print("Health:   http://localhost:8000/health")

    print("Starting uvicorn...")
    uvicorn.run(
        app,
        host="localhost",
        port=8000,
        reload=False,
        workers=1,
        log_level="info"
    )
