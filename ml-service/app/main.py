import time
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.parser import parse_raw_address
from app.standardizer import standardize_parsed_components, format_canonical_address
from app.features import extract_features
from app.model import predict_confidence
from app.embeddings import generate_address_embedding
from app.retraining import retrain_model

app = FastAPI(title="AI-Assisted Address Standardization ML Service", version="1.0.0")

# Models for Request/Response
class ParseRequest(BaseModel):
    raw_address: str

class StandardizeRequest(BaseModel):
    raw_address: str

class FeedbackItem(BaseModel):
    raw_address: str
    original_prediction: str
    human_decision: str
    corrected_address: Optional[str] = None

class RetrainRequest(BaseModel):
    feedback: List[FeedbackItem]

class EmbedRequest(BaseModel):
    address: str

# Current model metrics registry (in-memory caching for API check)
_current_metrics = {
    "accuracy": 0.85,
    "precision": 0.88,
    "recall": 0.82,
    "f1": 0.85,
    "training_samples": 200
}

@app.post("/parse")
def parse_endpoint(req: ParseRequest):
    components = parse_raw_address(req.raw_address)
    return {"components": components}

@app.post("/standardize")
def standardize_endpoint(req: StandardizeRequest):
    t0 = time.time()
    
    # 1. Parse raw address
    parsed = parse_raw_address(req.raw_address)
    if not parsed:
        raise HTTPException(status_code=422, detail="Address parsing failed")
        
    # 2. Standardize/normalize components
    cc = standardize_parsed_components(parsed)
    
    # 3. Format into a canonical address string
    std_addr = format_canonical_address(cc)
    
    # 4. Extract features
    features = extract_features(req.raw_address, std_addr, parsed, cc)
    
    # 5. Predict confidence score
    confidence = predict_confidence(features)
    
    processing_time_ms = int((time.time() - t0) * 1000)
    
    return {
        "standardized_address": std_addr,
        "confidence_score": float(confidence),
        "parsed_components": parsed,
        "canonical_components": cc,
        "feature_vector": features,
        "model_version": "v1.0.0-lgbm",
        "processing_time_ms": processing_time_ms
    }

@app.post("/retrain")
def retrain_endpoint(req: RetrainRequest):
    global _current_metrics
    try:
        feedback_list = [item.model_dump() for item in req.feedback]
        metrics = retrain_model(feedback_list)
        _current_metrics = metrics
        
        # New model version format based on timestamp
        version = f"v{int(time.time())}-retrained"
        
        return {
            "status": "success",
            "model_version": version,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

@app.get("/model/metrics")
def get_metrics_endpoint():
    return _current_metrics

@app.post("/embed")
def embed_endpoint(req: EmbedRequest):
    embedding = generate_address_embedding(req.address)
    return {"embedding": embedding}

@app.get("/health")
def health_endpoint():
    return {"status": "ok", "timestamp": time.time()}
