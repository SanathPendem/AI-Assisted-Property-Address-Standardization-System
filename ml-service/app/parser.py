import re

try:
    from postal.parser import parse_address
    HAS_POSTAL = True
except ImportError:
    HAS_POSTAL = False

def parse_raw_address(address_text: str) -> dict:
    """
    Parses a raw address string into components using libpostal.
    Falls back to regex parsing if libpostal C library is unavailable (e.g. running on Windows host).
    """
    if not address_text:
        return {}
        
    if HAS_POSTAL:
        try:
            parsed = parse_address(address_text)
            components = {}
            for value, key in parsed:
                components[key] = value
            return components
        except Exception as e:
            print(f"Error parsing address with libpostal: {e}")
            
    # Regex fallback parser for Windows host environments
    components = {}
    text = address_text.strip()
    
    # House number
    hn = re.search(r'^\d+', text)
    if hn:
        components['house_number'] = hn.group(0)
        
    # ZIP code
    zip_match = re.search(r'\b\d{5}(?:-\d{4})?\b', text)
    if zip_match:
        components['postcode'] = zip_match.group(0)
        
    # Road / Street
    road_match = re.search(r'\b(\d+th|\d+st|\d+nd|\d+rd|[A-Za-z0-9]+)\s+(St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Way|Terr|Terrace|Pl|Place)\b', text, re.I)
    if road_match:
        components['road'] = road_match.group(0)
        
    # Unit
    unit_match = re.search(r'\b(Apt|Apartment|Ste|Suite|Unit|#)\s*([A-Z0-9-]+)\b', text, re.I)
    if unit_match:
        components['unit'] = f"{unit_match.group(1)} {unit_match.group(2)}"
        
    # City / State
    cs_match = re.search(r'\b([A-Za-z\s]+),\s*([A-Z]{2})\b', text)
    if cs_match:
        components['city'] = cs_match.group(1).strip()
        components['state'] = cs_match.group(2).strip()
        
    return components
