import re

# Standard mapping dictionary configurations
DIRECTIONALS = {
    'n': 'North', 's': 'South', 'e': 'East', 'w': 'West',
    'ne': 'Northeast', 'nw': 'Northwest', 'se': 'Southeast', 'sw': 'Southwest',
    'north': 'North', 'south': 'South', 'east': 'East', 'west': 'West',
    'northeast': 'Northeast', 'northwest': 'Northwest', 'southeast': 'Southeast', 'southwest': 'Southwest'
}

SUFFIX_MAP = {
    'st': 'Street', 'street': 'Street',
    'ave': 'Avenue', 'avenue': 'Avenue',
    'rd': 'Road', 'road': 'Road',
    'ln': 'Lane', 'lane': 'Lane',
    'dr': 'Drive', 'drive': 'Drive',
    'ct': 'Court', 'court': 'Court',
    'pl': 'Place', 'place': 'Place',
    'blvd': 'Boulevard', 'boulevard': 'Boulevard',
    'pkwy': 'Parkway', 'parkway': 'Parkway',
    'wy': 'Way', 'way': 'Way',
    'ter': 'Terrace', 'terrace': 'Terrace'
}

UNIT_MAP = {
    'apt': 'Apartment', 'apartment': 'Apartment',
    'ste': 'Suite', 'suite': 'Suite',
    'unit': 'Unit', '#': 'Unit',
    'fl': 'Floor', 'floor': 'Floor'
}

STATE_MAP = {
    'al': 'Alabama', 'ak': 'Alaska', 'az': 'Arizona', 'ar': 'Arkansas', 'ca': 'California',
    'co': 'Colorado', 'ct': 'Connecticut', 'de': 'Delaware', 'fl': 'Florida', 'ga': 'Georgia',
    'hi': 'Hawaii', 'id': 'Idaho', 'il': 'Illinois', 'in': 'Indiana', 'ia': 'Iowa',
    'ks': 'Kansas', 'ky': 'Kentucky', 'la': 'Louisiana', 'me': 'Maine', 'md': 'Maryland',
    'ma': 'Massachusetts', 'mi': 'Michigan', 'mn': 'Minnesota', 'ms': 'Mississippi', 'mo': 'Missouri',
    'mt': 'Montana', 'ne': 'Nebraska', 'nv': 'Nevada', 'nh': 'New Hampshire', 'nj': 'New Jersey',
    'nm': 'New Mexico', 'ny': 'New York', 'nc': 'North Carolina', 'nd': 'North Dakota', 'oh': 'Ohio',
    'ok': 'Oklahoma', 'or': 'Oregon', 'pa': 'Pennsylvania', 'ri': 'Rhode Island', 'sc': 'South Carolina',
    'sd': 'South Dakota', 'tn': 'Tennessee', 'tx': 'Texas', 'ut': 'Utah', 'vt': 'Vermont',
    'va': 'Virginia', 'wa': 'Washington', 'wv': 'West Virginia', 'wi': 'Wisconsin', 'wy': 'Wyoming'
}

ORDINAL_MAP = {
    'first': '1st', 'second': '2nd', 'third': '3rd', 'fourth': '4th', 'fifth': '5th',
    'sixth': '6th', 'seventh': '7th', 'eighth': '8th', 'ninth': '9th', 'tenth': '10th',
    'eleventh': '11th', 'twelfth': '12th'
}

def normalize_ordinal(text: str) -> str:
    """Normalizes ordinal numbers/texts (e.g., Thirty Fourth -> 34th)."""
    if not text:
        return ""
    text_lower = text.lower().strip()
    
    # Check simple ordinal mappings
    if text_lower in ORDINAL_MAP:
        return ORDINAL_MAP[text_lower]
        
    # Check numeric conversion, e.g. "34" -> "34th"
    if text_lower.isdigit():
        val = int(text_lower)
        if 11 <= (val % 100) <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(val % 10, 'th')
        return f"{val}{suffix}"
        
    return text

def normalize_component(key: str, val: str) -> str:
    """Normalizes a specific address component using lookups."""
    if not val:
        return ""
    val_clean = val.lower().strip().replace('.', '')
    
    if key == 'pre_directional' or key == 'post_directional':
        return DIRECTIONALS.get(val_clean, val.strip().capitalize())
    elif key == 'street_suffix':
        return SUFFIX_MAP.get(val_clean, val.strip().capitalize())
    elif key == 'unit_type':
        return UNIT_MAP.get(val_clean, val.strip().capitalize())
    elif key == 'state_abbr':
        return val.strip().upper()
    elif key == 'state':
        return STATE_MAP.get(val_clean, val.strip().capitalize())
    
    return val.strip()

def standardize_parsed_components(parsed: dict) -> dict:
    """
    Apply rule-based normalization, ordinal conversions, and fill structure.
    """
    # Map raw libpostal components to canonical components
    house_number = parsed.get('house_number', '')
    pre_directional = parsed.get('pre_directional', '')
    street_name = parsed.get('road', '')
    street_suffix = parsed.get('street_suffix', '') # Wait, libpostal puts entire street in 'road', e.g. "west 34th street"
    post_directional = parsed.get('post_directional', '')
    unit_type = parsed.get('unit_type', '') or ('apartment' if 'level' in parsed or 'staircase' in parsed else '')
    unit_number = parsed.get('unit', '') or parsed.get('level', '') or parsed.get('staircase', '')
    city = parsed.get('city', '') or parsed.get('suburb', '')
    state_raw = parsed.get('state', '')
    zip_code = parsed.get('postcode', '')

    # Try parsing pre_directional, suffix, etc., from road if not explicitly parsed
    # Simple regex parsing for road name
    road_parts = street_name.strip().split()
    if len(road_parts) > 1 and not pre_directional:
        first_word = road_parts[0].lower().replace('.', '')
        if first_word in DIRECTIONALS:
            pre_directional = road_parts[0]
            road_parts = road_parts[1:]
            
    if len(road_parts) > 1 and not street_suffix:
        last_word = road_parts[-1].lower().replace('.', '')
        if last_word in SUFFIX_MAP:
            street_suffix = road_parts[-1]
            road_parts = road_parts[:-1]
    
    street_name = " ".join(road_parts)

    # Ordinal normalization on street name (e.g. "34" -> "34th", "thirty fourth" -> "34th")
    words = street_name.split()
    for idx, w in enumerate(words):
        norm_w = normalize_ordinal(w)
        if norm_w != w:
            words[idx] = norm_w
    street_name = " ".join(words)

    # Normalize components
    norm_pre_dir = normalize_component('pre_directional', pre_directional)
    norm_post_dir = normalize_component('post_directional', post_directional)
    norm_suffix = normalize_component('street_suffix', street_suffix)
    norm_unit_type = normalize_component('unit_type', unit_type)
    
    state_abbr = ""
    state_name = ""
    if state_raw:
        state_clean = state_raw.lower().strip().replace('.', '')
        if len(state_clean) == 2:
            state_abbr = state_clean.upper()
            state_name = STATE_MAP.get(state_clean, state_raw.capitalize())
        else:
            state_name = state_raw.capitalize()
            # find abbr
            for abbr, full in STATE_MAP.items():
                if full.lower() == state_clean:
                    state_abbr = abbr.upper()
                    break
            if not state_abbr:
                state_abbr = state_raw[:2].upper()

    canonical = {
        'house_number': house_number.strip().capitalize(),
        'pre_directional': norm_pre_dir,
        'street_name': street_name.strip().title(),
        'street_suffix': norm_suffix,
        'post_directional': norm_post_dir,
        'unit_type': norm_unit_type,
        'unit_number': unit_number.strip().upper(),
        'city': city.strip().title(),
        'state': state_name,
        'state_abbr': state_abbr,
        'zip_code': zip_code.strip()
    }

    return canonical

def format_canonical_address(cc: dict) -> str:
    """Formats standardized components into a single coherent address string."""
    parts = []
    
    # Street portion
    street_parts = [
        cc.get('house_number'),
        cc.get('pre_directional'),
        cc.get('street_name'),
        cc.get('street_suffix'),
        cc.get('post_directional')
    ]
    street_str = " ".join([p for p in street_parts if p])
    if street_str:
        parts.append(street_str)
        
    # Unit portion
    unit_parts = [cc.get('unit_type'), cc.get('unit_number')]
    unit_str = " ".join([p for p in unit_parts if p])
    if unit_str:
        parts.append(unit_str)
        
    # City/State/Zip
    city = cc.get('city')
    state = cc.get('state_abbr') or cc.get('state')
    zip_code = cc.get('zip_code')
    
    loc_parts = []
    if city:
        loc_parts.append(city)
    if state:
        loc_parts.append(state)
        
    loc_str = ", ".join(loc_parts)
    if zip_code:
        loc_str = f"{loc_str} {zip_code}".strip()
        
    if loc_str:
        parts.append(loc_str)
        
    return ", ".join(parts)
