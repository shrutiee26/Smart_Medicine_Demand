# 🏥 PharmaPulse AI: Smart Medicine Demand & Stock Prediction System

An end-to-end Machine Learning pharmaceutical demand forecasting and stock-out prevention platform. The system anticipates demand spikes, detects stock-out risks across supplier lead times, calculates dynamic Economic Order Quantities (EOQ), and issues near-expiry batch alerts using First-Expired, First-Out (FEFO) prioritization.

---

## 🚀 Key Features

1. **Comparative Machine Learning Arena**:
   - Compares **Linear Regression (Ridge)**, **Random Forest Regressor**, and **XGBoost Regressor** on chronological holdout test sets.
   - Evaluated on **Mean Absolute Error (MAE)**, **Root Mean Squared Error (RMSE)**, and **Coefficient of Determination ($R^2$)**.
   - Automated model selection: The best-performing model is automatically persisted and served for production inference.
2. **Multi-Horizon Predictive Demand Forecasting**:
   - Dynamic 7-day, 14-day, and 30-day ahead demand projections with 85% statistical confidence intervals.
   - Leverages cyclical date encodings, lag series ($t-1, t-7, t-14, t-30$), 7/14/30-day rolling averages & volatilities, environmental conditions (temperature, precipitation), and epidemic risk indices.
3. **Dynamic Reorder Point (ROP) & EOQ Recommendations**:
   - Formula: $\text{ROP} = (\text{Avg Daily Demand} \times \text{Lead Time}) + \text{Safety Stock}$
   - Safety Stock: $\text{SS} = Z \times \sigma_{\text{daily}} \times \sqrt{\text{Lead Time}}$ ($Z=1.65$ for 95% service level)
   - Economic Order Quantity: $\text{EOQ} = \sqrt{\frac{2 \cdot D \cdot S}{H}}$ clamped to supplier Minimum Order Quantities (MOQ).
   - Generates prioritized purchase orders categorized by urgency (`IMMEDIATE`, `HIGH`, `NORMAL`).
4. **Near-Expiry Batch Alert Center**:
   - Scans active batch inventories and classifies items into:
     - 🔴 **Critical Expiry** (&lt;30 days): Immediate quarantine or supplier return.
     - 🟡 **Warning Expiry** (31–60 days): FEFO promotional discounting or branch transfer.
     - 🔵 **Approaching Expiry** (61–90 days): Inbound overlap restrictions.
   - Computes expected consumption rate to estimate potential financial capital at risk.
5. **Epidemic Shock & Lead Time Disruption Simulator**:
   - Interactive sliders to simulate disease outbreaks (1.0x to 2.5x demand surge) and shipping disruptions (+0 to +7 days delay).
   - Dynamically recalculates safety stocks, days of coverage, and purchase order capital requirements in real time.
6. **Modern Dark Glassmorphic Web Dashboard**:
   - Built with Vanilla CSS, responsive layouts, Chart.js visualizations, and an asynchronous FastAPI backend.

---

## 📊 Machine Learning Model Comparison Scorecard

Evaluated on 10,050 daily records across 10 essential pharmaceutical categories (80% Train, 20% Chronological Test holdout):

| Model Architecture | Test MAE | Test RMSE | Test $R^2$ Score | Train $R^2$ Score | Training Time (s) | Evaluation Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Linear Regression (Ridge)** | 10.206 | 13.737 | 0.9093 | 0.9057 | 0.07s | Baseline linear trend |
| **Random Forest Regressor** 🏆 | **8.531** | **11.618** | **0.9351** | **0.9598** | 3.82s | **★ CHAMPION MODEL (Best $R^2$ & RMSE)** |
| **XGBoost Regressor** | 8.652 | 11.746 | 0.9337 | 0.9465 | 0.34s | High-performance gradient boosted trees |

> **Selection**: **Random Forest** achieved the highest $R^2$ accuracy (0.9351) and lowest test RMSE (11.618), closely followed by **XGBoost** (0.9337). Random Forest is selected and serialized as `models/best_model.joblib`.

---

## 📁 Repository Structure

```
ML_Project/
├── app.py                      # FastAPI web server and REST API endpoints
├── run_pipeline.py             # Pipeline runner (data generation, training, validation)
├── test_endpoints.py           # Automated HTTP endpoint integration tests
├── requirements.txt            # Python dependencies
├── data/                       # Generated pharmaceutical datasets
│   ├── medicines.csv           # Master catalogue (SKU, category, lead time, MOQ, unit price)
│   ├── historical_demand.csv   # Multi-year historical daily transactions
│   └── inventory_batches.csv   # Active batches with manufacturing & expiry dates
├── src/
│   ├── data_generator.py       # Realistic pharmaceutical transactional data generator
│   ├── feature_engineering.py  # Lag features, rolling statistics, cyclical encodings
│   ├── model_trainer.py        # Compares Linear Regression, Random Forest, and XGBoost
│   ├── inventory_engine.py     # Safety stock, dynamic ROP, EOQ, near-expiry alerts
│   └── forecast_service.py     # Multi-horizon forecast engine and unified orchestration
├── models/
│   ├── best_model.joblib       # Serialized champion model
│   ├── all_models.joblib       # All fitted model estimators
│   ├── model_metrics.json      # Comparative MAE, RMSE, R² scores
│   └── feature_cols.json       # Feature ordering specification
└── static/
    ├── index.html              # Responsive glassmorphic dashboard
    ├── style.css               # Medical dark theme styling
    └── app.js                  # Frontend controllers, Chart.js integrations, modal flows
```

---

## ⚡ Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Full ML Pipeline
Generates data, trains and benchmarks the models, and computes inventory health:
```bash
python run_pipeline.py
```

### 3. Start the Web Dashboard
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser and navigate to:
**`http://127.0.0.1:8000`**

---

## 🔌 REST API Endpoints

- `GET /api/dashboard`: Aggregated dashboard summary (KPIs, inventory health, reorders, expiry alerts, model metrics).
- `GET /api/medicines`: Returns medicine SKU catalogue.
- `GET /api/forecast/{medicine_id}?days_forecast=30`: Historical actuals vs multi-day ML projections with confidence bounds.
- `POST /api/simulate`: Real-time scenario simulation (outbreak multiplier, lead time transit delays).
- `POST /api/reorder/confirm`: Dispatch simulated purchase orders.
- `GET /api/export/reorders`: Generates downloadable CSV report of recommended purchase orders.
