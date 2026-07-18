import difflib

def get_jaccard_similarity(str1: str, str2: str) -> float:
    """Computes token-level Jaccard similarity."""
    a = set(str1.lower().split())
    b = set(str2.lower().split())
    if not a and not b:
        return 1.0
    return len(a.intersection(b)) / len(a.union(b))

def get_levenshtein_ratio(str1: str, str2: str) -> float:
    """Computes Levenshtein-like edit distance ratio using difflib."""
    return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def extract_features(raw_address: str, standardized_address: str, parsed_components: dict, canonical_components: dict) -> dict:
    """
    Extracts features comparing raw input and standardized output.
    These features are used by LightGBM to predict standardisation correctness/confidence.
    """
    raw_clean = raw_address.lower().strip()
    std_clean = standardized_address.lower().strip()
    
    # 1. Jaccard & Levenshtein
    jaccard = get_jaccard_similarity(raw_clean, std_clean)
    lev_ratio = get_levenshtein_ratio(raw_clean, std_clean)
    
    # 2. Length difference ratio
    len_raw = len(raw_clean)
    len_std = len(std_clean)
    len_diff = abs(len_raw - len_std) / max(len_raw, len_std, 1)
    
    # 3. Parsed components flags
    has_zip = 1.0 if canonical_components.get('zip_code') else 0.0
    has_house_num = 1.0 if canonical_components.get('house_number') else 0.0
    
    # Compare raw tokens with standardized components
    raw_tokens = set(raw_clean.replace(',', '').split())
    
    zip_in_raw = 0.0
    zip_val = canonical_components.get('zip_code')
    if zip_val and zip_val in raw_clean:
        zip_in_raw = 1.0
        
    # Did we expand directionals?
    pre_dir = canonical_components.get('pre_directional', '').lower()
    directional_expanded = 0.0
    if pre_dir:
        # e.g., if 'west' is in canonical but only 'w' was in raw
        if pre_dir in std_clean and not pre_dir in raw_clean:
            directional_expanded = 1.0
            
    # Street suffix expansion
    suffix = canonical_components.get('street_suffix', '').lower()
    suffix_expanded = 0.0
    if suffix:
        if suffix in std_clean and not suffix in raw_clean:
            suffix_expanded = 1.0

    features = {
        'jaccard_similarity': float(jaccard),
        'edit_distance_ratio': float(lev_ratio),
        'length_diff_ratio': float(len_diff),
        'has_zip': float(has_zip),
        'has_house_num': float(has_house_num),
        'zip_in_raw': float(zip_in_raw),
        'directional_expanded': float(directional_expanded),
        'suffix_expanded': float(suffix_expanded)
    }
    
    return features
