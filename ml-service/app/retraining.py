import os
import pickle
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from app.parser import parse_raw_address
from app.standardizer import standardize_parsed_components, format_canonical_address
from app.features import extract_features

# Resolve paths relative to the ml-service package root (this file lives in app/),
# NOT the current working directory -- this used to break depending on where you
# ran `uvicorn`/`python` from. Env vars still override for container deployments.
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../ml-service
MODEL_PATH = os.environ.get('MODEL_PATH', os.path.join(_PACKAGE_ROOT, 'models', 'lgbm_model.pkl'))
BASE_DATA_PATH = os.environ.get('TRAINING_DATA_PATH', os.path.join(_PACKAGE_ROOT, 'data', 'training_data.csv'))

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

def load_base_training_data() -> pd.DataFrame:
    """Loads base dataset from csv if exists, extracting features."""
    if not os.path.exists(BASE_DATA_PATH):
        # Create empty base DataFrame
        return pd.DataFrame(columns=FEATURE_ORDER + ['is_correct'])
        
    try:
        df = pd.read_csv(BASE_DATA_PATH)
        rows = []
        for _, row in df.iterrows():
            raw = str(row['raw_address'])
            canonical = str(row['canonical_address'])
            is_correct = int(row.get('is_correct', 1)) # standard is 1 (correct pairs)
            
            parsed = parse_raw_address(raw)
            cc = standardize_parsed_components(parsed)
            std_addr = format_canonical_address(cc)
            
            feat = extract_features(raw, std_addr, parsed, cc)
            feat['is_correct'] = is_correct
            rows.append(feat)
            
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error loading base training data: {e}")
        return pd.DataFrame(columns=FEATURE_ORDER + ['is_correct'])

def retrain_model(feedback_data: list) -> dict:
    """
    Retrains the LightGBM classifier using base data + new feedback.
    Saves the new model artifact.
    """
    # 1. Parse feedback data and extract features
    feedback_rows = []
    for item in feedback_data:
        raw = item.get('raw_address', '')
        pred = item.get('original_prediction', '')
        decision = item.get('human_decision', '')
        corrected = item.get('corrected_address', '')
        
        parsed = parse_raw_address(raw)
        cc = standardize_parsed_components(parsed)
        std_addr = format_canonical_address(cc)
        
        # If accepted, our prediction was correct
        if decision == 'accepted':
            feat = extract_features(raw, pred, parsed, cc)
            feat['is_correct'] = 1
            feedback_rows.append(feat)
        elif decision == 'corrected':
            # The prediction was wrong (class 0)
            feat_wrong = extract_features(raw, pred, parsed, cc)
            feat_wrong['is_correct'] = 0
            feedback_rows.append(feat_wrong)
            
            # The correction is correct (class 1)
            parsed_corr = parse_raw_address(corrected)
            cc_corr = standardize_parsed_components(parsed_corr)
            std_corr = format_canonical_address(cc_corr)
            feat_corr = extract_features(raw, std_corr, parsed_corr, cc_corr)
            feat_corr['is_correct'] = 1
            feedback_rows.append(feat_corr)
        elif decision == 'rejected':
            feat_wrong = extract_features(raw, pred, parsed, cc)
            feat_wrong['is_correct'] = 0
            feedback_rows.append(feat_wrong)
            
    df_feedback = pd.DataFrame(feedback_rows)
    df_base = load_base_training_data()
    
    # Combine datasets
    df_all = pd.concat([df_base, df_feedback], ignore_index=True)
    if len(df_all) < 10:
        # Not enough samples to train, but we will force train or return metrics
        pass
        
    X = df_all[FEATURE_ORDER]
    y = df_all['is_correct'].astype(int)
    
    # Split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )
    
    # Train LightGBM
    clf = LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=5,
        random_state=42,
        verbosity=-1
    )
    clf.fit(X_train, y_train)
    
    # Predict & Evaluate
    preds = clf.predict(X_val)
    accuracy = float(accuracy_score(y_val, preds))
    precision = float(precision_score(y_val, preds, zero_division=0))
    recall = float(recall_score(y_val, preds, zero_division=0))
    f1 = float(f1_score(y_val, preds, zero_division=0))
    
    # Save Model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(clf, f)
        
    # Reload model in model.py's cache so the next /standardize call uses it immediately
    import app.model as model_module
    with open(MODEL_PATH, 'rb') as f:
        model_module._model = pickle.load(f)
        
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'training_samples': len(df_all)
    }
