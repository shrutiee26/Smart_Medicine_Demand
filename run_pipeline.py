"""
End-to-End Pipeline Execution Script.
Runs data generation, feature engineering, model training & comparison,
and validates the inventory intelligence engine.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_generator import (
    generate_medicines_csv,
    generate_historical_demand_csv,
    generate_inventory_batches_csv
)
from src.model_trainer import train_and_compare_models
from src.forecast_service import MedicinePredictionSystem


def run_full_pipeline():
    print("=" * 70)
    print("  SMART MEDICINE DEMAND & STOCK PREDICTION PIPELINE")
    print("=" * 70)

    # 1. Generate Data
    print("\n[STEP 1/3] Generating Pharmaceutical Inventory & Demand Datasets...")
    df_meds = generate_medicines_csv()
    df_hist = generate_historical_demand_csv(start_date="2024-01-01", end_date="2026-10-01")
    df_batches = generate_inventory_batches_csv(as_of_date="2026-10-07")

    print(f"-> Medicines Master: {len(df_meds)} records")
    print(f"-> Historical Transactions: {len(df_hist)} records")
    print(f"-> Active Inventory Batches: {len(df_batches)} records")

    # 2. Train & Compare Models
    print("\n[STEP 2/3] Training & Comparing Machine Learning Models...")
    print("   Models: Linear Regression (Ridge), Random Forest, XGBoost")
    print("   Metrics: MAE (Mean Absolute Error), RMSE (Root Mean Sq Error), R2 (Score)")

    summary, best_model = train_and_compare_models(df_hist)

    print("\n" + "=" * 70)
    print("                   MODEL COMPARISON SCORECARD")
    print("=" * 70)
    print(f"{'Model':<20} | {'Test MAE':<10} | {'Test RMSE':<10} | {'Test R²':<10} | {'Train R²':<10} | {'Time (s)':<8}")
    print("-" * 75)

    for m_name, res in summary["models"].items():
        is_winner = " [BEST]" if res["is_best"] else ""
        test_m = res["test_metrics"]
        train_m = res["train_metrics"]
        print(f"{m_name + is_winner:<20} | {test_m['mae']:<10.3f} | {test_m['rmse']:<10.3f} | {test_m['r2']:<10.4f} | {train_m['r2']:<10.4f} | {res['training_time_sec']:<8.2f}")

    print("=" * 70)
    print(f"WINNING MODEL: {summary['best_model']} (Selected for Production Forecasting)")

    # 3. Test Forecast & Inventory Engine
    print("\n[STEP 3/3] Validating Demand Forecast & Inventory Engine...")
    system = MedicinePredictionSystem()
    dash_data = system.get_dashboard_data(horizon=30)

    kpis = dash_data["kpis"]
    print(f"\nInventory Health Summary:")
    print(f" - Total SKUs: {kpis['total_skus']}")
    print(f" - Total Stock On Hand: {kpis['total_stock_units']} units (${kpis['total_inventory_value']:,.2f})")
    print(f" - Critical Stock-Out Risks: {kpis['critical_stockouts']} items")
    print(f" - High Stock-Out Risks: {kpis['high_stock_risks']} items")
    print(f" - Urgent Expiry Batches (<30d): {kpis['urgent_expiry_alerts']} batches (${kpis['total_value_at_risk']:,.2f} at risk)")
    print(f" - Recommended Purchase Orders: {len(dash_data['reorders'])} orders generated")

    print("\nSample Reorder Recommendations:")
    for r in dash_data["reorders"][:4]:
        print(f"  * [{r['urgency']}] {r['name']} - Current Stock: {r['current_stock']} | ROP: {r['reorder_point']} | Recommend Reorder: {r['recommended_qty']} units (Est Cost: ${r['estimated_cost']:,.2f})")

    print("\nSample Near-Expiry Alerts:")
    for a in dash_data["expiry_alerts"][:4]:
        print(f"  * [{a['urgency']}] Batch {a['batch_id']} ({a['medicine_name']}): {a['days_to_expiry']} days left (Exp: {a['expiry_date']}) - Qty: {a['batch_quantity']} | Value at Risk: ${a['value_at_risk']:,.2f}")

    print("\nPIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_full_pipeline()
