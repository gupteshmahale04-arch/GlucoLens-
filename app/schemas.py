from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Gender(str, Enum):
    female = "Female"
    male = "Male"
    other = "Other"


class SmokingHistory(str, Enum):
    no_info = "No Info"
    current = "current"
    ever = "ever"
    former = "former"
    never = "never"
    not_current = "not current"


class PatientInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "gender": "Male", "age": 50, "hypertension": 1, "heart_disease": 0,
        "smoking_history": "never", "bmi": 31.5, "HbA1c_level": 7.0, "blood_glucose_level": 180}})

    gender: Gender
    age: float = Field(..., ge=0, le=120, description="Age in years")
    hypertension: int = Field(..., ge=0, le=1, description="1 if the patient has hypertension")
    heart_disease: int = Field(..., ge=0, le=1, description="1 if the patient has heart disease")
    smoking_history: SmokingHistory
    bmi: float = Field(..., ge=10, le=100, description="Body-mass index (kg/m²)")
    HbA1c_level: float = Field(..., ge=3, le=15, description="Average blood sugar over ~3 months (%)")
    blood_glucose_level: float = Field(..., ge=50, le=500, description="Blood glucose (mg/dL)")


class Driver(BaseModel):
    feature: str
    label: str
    value: str
    impact: float = Field(..., description="Contribution to the log-odds (positive raises risk)")
    direction: str = Field(..., description="'increases' or 'decreases' risk relative to an average patient")


class PredictionResponse(BaseModel):
    prediction: int = Field(..., description="1 = diabetes predicted, 0 = not predicted")
    label: str
    probability: float = Field(..., description="Probability of diabetes, 0-1")
    risk_level: str = Field(..., description="low | moderate | high | very high")
    drivers: List[Driver]
    warnings: List[str] = []
    model_version: str
    disclaimer: str


class BatchRequest(BaseModel):
    patients: List[PatientInput] = Field(..., min_length=1, max_length=500)


class BatchResponse(BaseModel):
    count: int
    results: List[PredictionResponse]


class Metrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion: dict
    train_rows: int
    test_rows: int
    positive_rate: float


class ModelInfo(BaseModel):
    name: str
    version: str
    algorithm: str
    features: List[str]
    class_weight: Optional[str]
    metrics: Metrics
    ranges: dict
    feature_importance: List[dict]


class Health(BaseModel):
    status: str
    model_loaded: bool
    version: str
