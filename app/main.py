import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .model_service import ModelService, VERSION
from .schemas import (BatchRequest, BatchResponse, Health, ModelInfo, PatientInput, PredictionResponse)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("diabetes-api")
STATIC = Path(__file__).resolve().parent.parent / "static"
service: ModelService | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global service
    service = ModelService()
    log.info("Model loaded (v%s)", VERSION)
    yield


app = FastAPI(
    title="Diabetes Risk Prediction API",
    version=VERSION,
    description=("Predict diabetes risk from routine health measurements using a trained "
                 "**logistic-regression** model.\n\n> ⚠️ Educational demo — not a medical device."),
    lifespan=lifespan,
    openapi_tags=[{"name": "Prediction", "description": "Run the model"},
                  {"name": "Meta", "description": "Health & model details"}],
)
app.add_middleware(GZipMiddleware, minimum_size=800)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


@app.middleware("http")
async def common_headers(request: Request, call_next):
    rid = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
    t0 = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - t0) * 1000
    response.headers.update({
        "X-Request-ID": rid, "X-Process-Time-ms": f"{ms:.1f}",
        "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
    })
    if request.url.path.startswith("/api"):
        log.info("%s %s -> %s %.1fms [%s]", request.method, request.url.path, response.status_code, ms, rid)
        response.headers["Cache-Control"] = "no-store"
    return response


def svc() -> ModelService:
    if service is None:
        raise HTTPException(503, "Model not loaded")
    return service


@app.get("/api/health", response_model=Health, tags=["Meta"], summary="Liveness / readiness probe")
def health():
    return Health(status="ok" if service else "starting", model_loaded=service is not None, version=VERSION)


@app.get("/api/model-info", response_model=ModelInfo, tags=["Meta"], summary="Model metadata, metrics and coefficients")
def model_info():
    return svc().info()


@app.post("/api/predict", response_model=PredictionResponse, tags=["Prediction"], summary="Predict for one patient")
def predict(patient: PatientInput):
    return svc().predict([patient])[0]


@app.post("/api/predict/batch", response_model=BatchResponse, tags=["Prediction"], summary="Predict for up to 500 patients")
def predict_batch(req: BatchRequest):
    res = svc().predict(req.patients)
    return BatchResponse(count=len(res), results=res)


app.mount("/assets", StaticFiles(directory=STATIC), name="assets")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")
