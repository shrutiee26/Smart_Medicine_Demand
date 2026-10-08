"""
FastAPI Server for Smart Medicine Demand & Stock Prediction System.
Serves REST API endpoints and hosts the modern web dashboard.
"""

import os
import io
import csv
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.forecast_service import MedicinePredictionSystem

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="Smart Medicine Demand & Stock Prediction System",
    description="ML-powered demand forecasting, stock-out detection, dynamic reorders, and near-expiry alerts.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global system instance
prediction_system = MedicinePredictionSystem()


class SimulationRequest(BaseModel):
    horizon_days: int = 30
    outbreak_multiplier: float = 1.0
    lead_time_buffer_days: int = 0


class ReorderAction(BaseModel):
    medicine_id: str
    quantity: int
    po_notes: str = "Automated AI reorder trigger"


@app.get("/api/dashboard")
def get_dashboard_summary(
    horizon: int = Query(30, ge=7, le=90),
    outbreak: float = Query(1.0, ge=0.5, le=3.0),
    lead_time_buffer: int = Query(0, ge=-2, le=14)
):
    """Returns high-level KPIs, inventory health, expiry alerts, and reorder plan."""
    if not prediction_system.is_ready():
        prediction_system.load_all()

    try:
        data = prediction_system.get_dashboard_data(
            horizon=horizon,
            outbreak_multiplier=outbreak,
            lead_time_buffer=lead_time_buffer
        )
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/medicines")
def get_medicines_list():
    """Returns all medicine catalogues."""
    if prediction_system.df_meds is None:
        prediction_system.load_all()
    return {"status": "success", "medicines": prediction_system.df_meds.to_dict(orient="records")}


@app.get("/api/forecast/{medicine_id}")
def get_medicine_forecast(
    medicine_id: str,
    days_history: int = Query(60, ge=14, le=180),
    days_forecast: int = Query(30, ge=7, le=90)
):
    """Returns historical sales, ML demand forecasts, and model comparison data for a given medicine."""
    if not prediction_system.is_ready():
        prediction_system.load_all()

    # Validate medicine ID
    valid_ids = prediction_system.df_meds['medicine_id'].tolist()
    if medicine_id not in valid_ids:
        raise HTTPException(status_code=404, detail=f"Medicine ID '{medicine_id}' not found.")

    chart_data = prediction_system.get_medicine_chart_data(
        medicine_id=medicine_id,
        days_history=days_history,
        days_forecast=days_forecast
    )
    return {"status": "success", "data": chart_data}


@app.post("/api/simulate")
def run_simulation(sim: SimulationRequest):
    """Simulates real-time demand surge or supplier disruption."""
    if not prediction_system.is_ready():
        prediction_system.load_all()

    data = prediction_system.get_dashboard_data(
        horizon=sim.horizon_days,
        outbreak_multiplier=sim.outbreak_multiplier,
        lead_time_buffer=sim.lead_time_buffer_days
    )
    return {"status": "success", "data": data}


from typing import Optional


class AddStockBatchRequest(BaseModel):
    medicine_id: str
    quantity: int
    expiry_date: str
    batch_id: Optional[str] = None
    storage_location: Optional[str] = "Main Warehouse"
    unit_cost: Optional[float] = None
    mfd_date: Optional[str] = None


class UpdateStockBatchRequest(BaseModel):
    quantity: int


@app.post("/api/reorder/confirm")
def confirm_reorder(action: ReorderAction):
    """Simulates creating a purchase order."""
    return {
        "status": "success",
        "message": f"Purchase order successfully dispatched for {action.medicine_id} ({action.quantity} units).",
        "po_number": f"PO-{datetime.now().strftime('%Y%m%d')}-{action.medicine_id[-3:]}",
        "dispatched_at": datetime.now().isoformat()
    }


@app.post("/api/stock/add")
def add_medicine_stock(item: AddStockBatchRequest):
    """Interactively adds a new medicine stock batch."""
    try:
        batch = prediction_system.add_stock_batch(
            medicine_id=item.medicine_id,
            quantity=item.quantity,
            expiry_date=item.expiry_date,
            batch_id=item.batch_id,
            storage_location=item.storage_location,
            unit_cost=item.unit_cost,
            mfd_date=item.mfd_date
        )
        return {"status": "success", "message": f"Successfully added {item.quantity} units for {item.medicine_id} (Batch {batch['batch_id']})", "batch": batch}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/stock/batch/{batch_id}")
def update_medicine_stock(batch_id: str, req: UpdateStockBatchRequest):
    """Updates batch stock quantity."""
    try:
        updated = prediction_system.update_batch_quantity(batch_id, req.quantity)
        return {"status": "success", "message": f"Updated batch {batch_id} to {req.quantity} units", "batch": updated}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/stock/batch/{batch_id}")
def delete_medicine_stock_batch(batch_id: str):
    """Deletes a stock batch."""
    try:
        prediction_system.delete_batch(batch_id)
        return {"status": "success", "message": f"Deleted batch {batch_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/stock/clear")
def clear_all_medicine_stock():
    """Resets inventory to completely blank."""
    try:
        prediction_system.clear_all_stock()
        return {"status": "success", "message": "All stock cleared to blank state"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stock/load-demo")
def load_demo_medicine_stock():
    """Loads realistic sample stock for demonstration."""
    try:
        prediction_system.load_demo_stock()
        return {"status": "success", "message": "Demo stock loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/reorders")
def export_reorders_csv():
    """Generates a downloadable CSV containing smart reorder recommendations."""
    if not prediction_system.is_ready():
        prediction_system.load_all()

    data = prediction_system.get_dashboard_data(horizon=30)
    reorders = data.get("reorders", [])

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "medicine_id", "name", "category", "current_stock",
        "reorder_point", "recommended_qty", "urgency",
        "supplier_lead_time_days", "estimated_cost", "reason"
    ])
    writer.writeheader()
    for row in reorders:
        writer.writerow(row)

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reorder_recommendations_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


# Mount static frontend
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
