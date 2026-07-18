import csv
import os
import random

# Seed for reproducibility
random.seed(42)

BASE_DATA_PATH = 'ml-service/data/training_data.csv'

# Components to assemble realistic addresses
streets = [
    ("Amphitheatre", "Parkway", "Pkwy", "Pkwy."),
    ("Pennsylvania", "Avenue", "Ave", "Ave."),
    ("Broadway", "", "", ""),
    ("Wall", "Street", "St", "St."),
    ("Lexington", "Avenue", "Ave", "Ave."),
    ("Fifth", "Avenue", "Ave", "Ave."),
    ("Main", "Street", "St", "St."),
    ("Oak", "Road", "Rd", "Rd."),
    ("Pine", "Lane", "Ln", "Ln."),
    ("Maple", "Drive", "Dr", "Dr."),
    ("Cedar", "Court", "Ct", "Ct."),
    ("Washington", "Street", "St", "St."),
    ("Elm", "Street", "St", "St."),
    ("Park", "Avenue", "Ave", "Ave."),
    ("Sunset", "Boulevard", "Blvd", "Blvd."),
    ("Peachtree", "Street", "St", "St."),
    ("Michigan", "Avenue", "Ave", "Ave."),
    ("Market", "Street", "St", "St.")
]

cities = [
    ("Mountain View", "CA", "94043"),
    ("Washington", "DC", "20500"),
    ("New York", "NY", "10005"),
    ("Atlanta", "GA", "30303"),
    ("Chicago", "IL", "60601"),
    ("San Francisco", "CA", "94103"),
    ("Seattle", "WA", "98101"),
    ("Boston", "MA", "02108"),
    ("Austin", "TX", "78701"),
    ("Miami", "FL", "33131")
]

directions = [
    ("North", "N", "N."),
    ("South", "S", "S."),
    ("East", "E", "E."),
    ("West", "W", "W.")
]

units = [
    ("Apartment", "Apt", "Apt."),
    ("Suite", "Ste", "Ste."),
    ("Unit", "Unit", "#"),
    ("Floor", "Fl", "Fl.")
]

def generate_address_pairs():
    pairs = []
    
    # 1. Generate 150 correct standardization mappings (class 1)
    for i in range(150):
        # Pick components
        house_num = str(random.randint(1, 9999))
        street_base, street_full, street_abbr1, street_abbr2 = random.choice(streets)
        city, state, zip_code = random.choice(cities)
        
        # Decide optional components
        has_dir = random.random() < 0.4
        has_unit = random.random() < 0.5
        
        dir_full, dir_abbr1, dir_abbr2 = random.choice(directions) if has_dir else ("", "", "")
        unit_full, unit_abbr1, unit_abbr2 = random.choice(units) if has_unit else ("", "", "")
        unit_num = str(random.randint(1, 100)) if has_unit else ""
        
        # Construct Canonical (Standardized) Address
        canonical_parts = [house_num]
        if has_dir:
            canonical_parts.append(dir_full)
        canonical_parts.append(street_base)
        if street_full:
            canonical_parts.append(street_full)
        
        street_part = " ".join(canonical_parts)
        canonical_addr_parts = [street_part]
        
        if has_unit:
            canonical_addr_parts.append(f"{unit_full} {unit_num}")
            
        canonical_addr_parts.append(f"{city}, {state} {zip_code}")
        canonical = ", ".join(canonical_addr_parts)
        
        # Construct Raw address variations (abbreviated, missing zip, lowercase, typos)
        raw_street_suffix = random.choice([street_full, street_abbr1, street_abbr2]) if street_full else ""
        raw_dir = random.choice([dir_full, dir_abbr1, dir_abbr2]) if has_dir else ""
        raw_unit_type = random.choice([unit_full, unit_abbr1, unit_abbr2]) if has_unit else ""
        
        raw_street_parts = [house_num]
        if raw_dir:
            raw_street_parts.append(raw_dir)
        raw_street_parts.append(street_base)
        if raw_street_suffix:
            raw_street_parts.append(raw_street_suffix)
            
        raw_street_str = " ".join(raw_street_parts)
        raw_addr_parts = [raw_street_str]
        
        if has_unit:
            raw_addr_parts.append(f"{raw_unit_type} {unit_num}")
            
        # Variations in city, state, zip
        raw_state = random.choice([state, state.lower(), state + "."])
        raw_zip = random.choice([zip_code, ""]) # 20% missing zip code
        
        loc_str = f"{city}, {raw_state}"
        if raw_zip:
            loc_str += f" {raw_zip}"
            
        raw_addr_parts.append(loc_str)
        
        raw = ", ".join(raw_addr_parts)
        
        # Introduce typos in 15% of raw addresses
        if random.random() < 0.15:
            # simple swap or character drop
            if len(raw) > 10:
                idx = random.randint(5, len(raw) - 5)
                raw = raw[:idx] + raw[idx+1] + raw[idx] + raw[idx+2:]
                
        pairs.append((raw, canonical, 1))

    # 2. Generate 50 mismatched/incorrect pairings (class 0) for boundary negative training
    for i in range(50):
        # Pick components for a raw address
        house_num1 = str(random.randint(1, 9999))
        street_base1, street_full1, _, _ = random.choice(streets)
        city1, state1, zip_code1 = random.choice(cities)
        
        # Pick components for a mismatched canonical address (e.g. wrong city, zip, or street)
        house_num2 = str(random.randint(1, 9999)) if random.random() < 0.3 else house_num1
        street_base2, street_full2, _, _ = random.choice(streets)
        city2, state2, zip_code2 = random.choice(cities)
        
        raw = f"{house_num1} {street_base1} {street_full1}, {city1}, {state1} {zip_code1}"
        canonical = f"{house_num2} {street_base2} {street_full2}, {city2}, {state2} {zip_code2}"
        
        # Ensure they are actually different
        if raw != canonical:
            pairs.append((raw, canonical, 0))
            
    return pairs

def main():
    os.makedirs(os.path.dirname(BASE_DATA_PATH), exist_ok=True)
    pairs = generate_address_pairs()
    
    with open(BASE_DATA_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['raw_address', 'canonical_address', 'is_correct'])
        for raw, canonical, is_correct in pairs:
            writer.writerow([raw, canonical, is_correct])
            
    print(f"Generated {len(pairs)} address pairs at {BASE_DATA_PATH}")

if __name__ == '__main__':
    main()
