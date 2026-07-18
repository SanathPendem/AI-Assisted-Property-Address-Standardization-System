import os
import pickle
import numpy as np
import pandas as pd

_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../ml-service
MODEL_PATH = os.environ.get('MODEL_PATH', os.path.join(_PACKAGE_ROOT, 'models', 'lgbm_model.pkl'))
FEATURE_ORDER = [
    'jaccard_similarity',
    'edit_distance_ratio',
    'length_diff_ratio',
    'has_zip',
    'has_house_num',
    'zip_in_raw',
    'directional_expanded',
    'suffix_expanded'
]

_model = None

def get_model():
    """Lazily loads the LightGBM model from disk or returns None if not found."""
    global _model
    if _model is not None:
        return _model
        
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f:
                _model = pickle.load(f)
            print(f"Loaded LightGBM model from {MODEL_PATH}")
        except Exception as e:
            print(f"Error loading LightGBM model: {e}")
            _model = None
    else:
        print(f"No model found at {MODEL_PATH}. Using heuristic fallback for confidence scoring.")
        _model = None
        
    return _model

def predict_confidence(features: dict) -> float:
    """
    Predicts standardisation confidence score.
    Uses LightGBM classifier if loaded; otherwise falls back to a weighted heuristic score.
    """
    model = get_model()
    
    if model is not None:
        try:
            # Construct a DataFrame matching feature order
            df = pd.DataFrame([features])[FEATURE_ORDER]
            # LightGBM predict probability of class 1 (is_correct)
            prob = model.predict_proba(df)[0][1]
            return float(prob)
        except Exception as e:
            print(f"LightGBM prediction failed: {e}. Falling back to heuristic.")
            
    # Heuristic Fallback
    # Combine edit distance (50%), jaccard (30%), components overlap (20%)
    ed = features.get('edit_distance_ratio', 0.5)
    jac = features.get('jaccard_similarity', 0.5)
    has_zip = features.get('has_zip', 0.0)
    zip_in_raw = features.get('zip_in_raw', 0.0)
    has_hn = features.get('has_house_num', 0.0)
    
    # Calculate score
    score = 0.5 * ed + 0.3 * jac + 0.1 * (zip_in_raw if has_zip else 0.5) + 0.1 * has_hn
    
    # Clip to 0..1
    return float(np.clip(score, 0.0, 1.0))
