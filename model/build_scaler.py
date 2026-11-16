"""Rebuild the StandardScaler + evaluation metrics exactly as in the notebook
(LabelEncoder, 80/20 split with random_state=42, StandardScaler fit on train).
Usage: python model/build_scaler.py path/to/diabetes_prediction_dataset.csv
"""
import json, sys
from pathlib import Path
import joblib, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score

HERE = Path(__file__).parent
df = pd.read_csv(sys.argv[1])
maps = {}
for col in df.select_dtypes(exclude="number").columns:
    le = LabelEncoder(); df[col] = le.fit_transform(df[col])
    maps[col] = {c: int(i) for i, c in enumerate(le.classes_)}
X, y = df.drop("diabetes", axis=1), df["diabetes"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
sc = StandardScaler().fit(Xtr)
model = joblib.load(HERE / "diabetes_prediction.pkl")
pred = model.predict(sc.transform(Xte)); proba = model.predict_proba(sc.transform(Xte))[:, 1]
tn, fp, fn, tp = confusion_matrix(yte, pred).ravel()
meta = {
    "features": list(X.columns), "encodings": maps,
    "scaler_mean": sc.mean_.tolist(), "scaler_scale": sc.scale_.tolist(),
    "ranges": {c: [float(X[c].min()), float(X[c].max())] for c in ["age", "bmi", "HbA1c_level", "blood_glucose_level"]},
    "metrics": {"accuracy": accuracy_score(yte, pred), "precision": precision_score(yte, pred),
                "recall": recall_score(yte, pred), "f1": f1_score(yte, pred), "roc_auc": roc_auc_score(yte, proba),
                "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
                "train_rows": len(Xtr), "test_rows": len(Xte), "positive_rate": float(y.mean())},
}
(HERE / "preprocessing.json").write_text(json.dumps(meta, indent=2))
print(json.dumps(meta["metrics"], indent=2)); print(maps)
# notebook sample patient (bmi=3 as written there)
import numpy as np
p = pd.DataFrame([{"gender":1,"age":50,"hypertension":1,"heart_disease":0,"smoking_history":0,"bmi":3,"HbA1c_level":7,"blood_glucose_level":180}])
print("notebook sample ->", model.predict_proba(sc.transform(p))[0])
