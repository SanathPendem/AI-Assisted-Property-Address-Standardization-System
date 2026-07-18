from postal.parser import parse_address

def parse_raw_address(address_text: str) -> dict:
    """
    Parses a raw address string into components using libpostal.
    Returns a dictionary of normalized component keys.
    """
    if not address_text:
        return {}
        
    try:
        parsed = parse_address(address_text)
        # Convert list of tuples (value, component_name) to dict
        components = {}
        for value, key in parsed:
            components[key] = value
        return components
    except Exception as e:
        print(f"Error parsing address with libpostal: {e}")
        return {}
