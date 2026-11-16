"""Loads the trained logistic-regression model + preprocessing and serves predictions."""
import json
from pathlib import Path
from typing import List

import joblib
import numpy as np

from .schemas import PatientInput, PredictionResponse, Driver

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
VERSION = "1.0.0"
DISCLAIMER = ("This tool is a machine-learning demo trained on a public dataset. It is not a medical "
              "device and does not provide a diagnosis. Consult a qualified clinician.")

LABELS = {
    "gender": "Gender", "age": "Age", "hypertension": "Hypertension", "heart_disease": "Heart disease",
    "smoking_history": "Smoking history", "bmi": "BMI", "HbA1c_level": "HbA1c level",
    "blood_glucose_level": "Blood glucose",
}


def risk_level(p: float) -> str:
    if p < 0.20: return "low"
    if p < 0.50: return "moderate"
    if p < 0.80: return "high"
    return "very high"


class ModelService:
    def __init__(self) -> None:
        self.model = joblib.load(MODEL_DIR / "diabetes_prediction.pkl")
        meta = json.loads((MODEL_DIR / "preprocessing.json").read_text())
        self.meta = meta
        self.features: List[str] = meta["features"]
        self.encodings = meta["encodings"]
        self.mean = np.array(meta["scaler_mean"])
        self.scale = np.array(meta["scaler_scale"])
        self.coef = self.model.coef_[0]
        self.intercept = float(self.model.intercept_[0])

    # ---- helpers -------------------------------------------------------
    def _row(self, p: PatientInput) -> np.ndarray:
        d = {
            "gender": self.encodings["gender"][p.gender.value],
            "age": p.age, "hypertension": p.hypertension, "heart_disease": p.heart_disease,
            "smoking_history": self.encodings["smoking_history"][p.smoking_history.value],
            "bmi": p.bmi, "HbA1c_level": p.HbA1c_level, "blood_glucose_level": p.blood_glucose_level,
        }
        return np.array([d[f] for f in self.features], dtype=float)

    def _warnings(self, p: PatientInput) -> List[str]:
        out = []
        for key, name, unit in [("age", "Age", ""), ("bmi", "BMI", ""), ("HbA1c_level", "HbA1c", "%"),
                                ("blood_glucose_level", "Blood glucose", " mg/dL")]:
            lo, hi = self.meta["ranges"][key]
            v = getattr(p, key)
            if v < lo or v > hi:
                out.append(f"{name} {v:g}{unit} is outside the training range ({lo:g}–{hi:g}); the estimate may be unreliable.")
        return out

    def _display(self, f: str, p: PatientInput) -> str:
        v = getattr(p, f)
        if f in ("gender", "smoking_history"): return v.value.title() if f == "smoking_history" else v.value
        if f in ("hypertension", "heart_disease"): return "Yes" if v else "No"
        if f == "HbA1c_level": return f"{v:g} %"
        if f == "blood_glucose_level": return f"{v:g} mg/dL"
        return f"{v:g}"

    # ---- public API ----------------------------------------------------
    def predict(self, patients: List[PatientInput]) -> List[PredictionResponse]:
        X = np.vstack([self._row(p) for p in patients])
        Z = (X - self.mean) / self.scale
        contrib = Z * self.coef                       # per-feature log-odds contribution vs. the average patient
        proba = self.model.predict_proba(Z)[:, 1]
        preds = self.model.predict(Z)
        results = []
        for i, p in enumerate(patients):
            drivers = [Driver(feature=f, label=LABELS[f], value=self._display(f, p),
                              impact=round(float(contrib[i, j]), 4),
                              direction="increases" if contrib[i, j] > 0 else "decreases")
                       for j, f in enumerate(self.features)]
            drivers.sort(key=lambda d: abs(d.impact), reverse=True)
            prob = float(proba[i])
            results.append(PredictionResponse(
                prediction=int(preds[i]), label="Diabetes likely" if preds[i] == 1 else "Diabetes unlikely",
                probability=round(prob, 4), risk_level=risk_level(prob), drivers=drivers,
                warnings=self._warnings(p), model_version=VERSION, disclaimer=DISCLAIMER))
        return results

    def info(self) -> dict:
        imp = [{"feature": f, "label": LABELS[f], "coefficient": round(float(c), 4)}
               for f, c in zip(self.features, self.coef)]
        imp.sort(key=lambda d: abs(d["coefficient"]), reverse=True)
        return {"name": "Diabetes Risk Classifier", "version": VERSION,
                "algorithm": "Logistic Regression (L2, lbfgs)", "features": self.features,
                "class_weight": self.model.class_weight, "metrics": self.meta["metrics"],
                "ranges": self.meta["ranges"], "feature_importance": imp}
