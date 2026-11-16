# GlucoLens – Diabetes risk assessment

FastAPI service + web UI around your logistic-regression model (`model/diabetes_prediction.pkl`).

## Run locally
```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```
- App: http://localhost:8000
- Swagger docs: http://localhost:8000/docs · ReDoc: http://localhost:8000/redoc

## Run with Docker
```bash
docker compose up --build
```

## Endpoints
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/predict` | Risk for one patient (probability, risk level, per-feature drivers) |
| POST | `/api/predict/batch` | Up to 500 patients |
| GET | `/api/model-info` | Metrics, confusion matrix, coefficients |
| GET | `/api/health` | Readiness probe |

```bash
curl -X POST localhost:8000/api/predict -H 'Content-Type: application/json' -d '{
 "gender":"Male","age":50,"hypertension":1,"heart_disease":0,"smoking_history":"never",
 "bmi":31.5,"HbA1c_level":7.0,"blood_glucose_level":180}'
```

## Layout
```
app/        FastAPI app (main.py), schemas, model service
static/     index.html, styles.css, app.js (no build step)
model/      diabetes_prediction.pkl, preprocessing.json, build_scaler.py
tests/      pytest suite   ->  pytest -q
```

## Notes
- The `.pkl` contains only the model. `model/preprocessing.json` holds the label encodings and
  StandardScaler statistics, rebuilt from the dataset with the notebook's exact split
  (`random_state=42`, 80/20). Regenerate with `python model/build_scaler.py diabetes_prediction_dataset.csv`.
  Verified: the notebook's sample patient gives 61.7 % and the test metrics match (recall 0.88, precision 0.43).
- scikit-learn is pinned to 1.9.1 because the pickle was saved with it.
- Educational demo, not a medical device.
