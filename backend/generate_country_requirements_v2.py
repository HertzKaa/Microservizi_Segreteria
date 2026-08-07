import os
import json
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
req_json_path = os.path.join(script_dir, "minimum_requirements", "requirements.json")
out_json_path = os.path.join(script_dir, "country_requirements.json")

with open(req_json_path, "r", encoding="utf-8") as f:
    source_data = json.load(f)

iso_map = {
    'INTERNATIONAL BACCALAUREATE (IB)': ('International Baccalaureate (IB)', 'IB'),
    'EUROPEAN BACCALAUREATE (EB)': ('European Baccalaureate (EB)', 'EU'),
    'AFGHANISTAN': ('Afghanistan', 'AF'),
    'ALBANIA': ('Albania', 'AL'),
    'ALGERIA': ('Algeria', 'DZ'),
    'ARABIA SAUDITA': ('Arabia Saudita', 'SA'),
    'AUSTRALIA': ('Australia', 'AU'),
    'AZERBAIGIAN': ('Azerbaigian', 'AZ'),
    'BANGLADESH': ('Bangladesh', 'BD'),
    'BRASILE': ('Brasile', 'BR'),
    'CAMERUN': ('Camerun', 'CM'),
    'CINA': ('Cina', 'CN'),
    'CIPRO': ('Cipro', 'CY'),
    'COLOMBIA': ('Colombia', 'CO'),
    'COREA del SUD (REPUBBLICA di COREA)': ('Corea del Sud', 'KR'),
    'EGITTO': ('Egitto', 'EG'),
    'ETIOPIA': ('Etiopia', 'ET'),
    'FILIPPINE': ('Filippine', 'PH'),
    'FRANCIA': ('Francia', 'FR'),
    'GAMBIA': ('Gambia', 'GM'),
    'GERMANIA': ('Germania', 'DE'),
    'GHANA': ('Ghana', 'GH'),
    'GIORDANIA': ('Giordania', 'JO'),
    'GRECIA': ('Grecia', 'GR'),
    'INDIA': ('India', 'IN'),
    'INDONESIA': ('Indonesia', 'ID'),
    'IRAN': ('Iran', 'IR'),
    'IRAQ': ('Iraq', 'IQ'),
    'IRLANDA': ('Irlanda', 'IE'),
    'ISRAELE': ('Israele', 'IL'),
    'KAZAKISTAN': ('Kazakistan', 'KZ'),
    'LIBANO': ('Libano', 'LB'),
    'MALESIA': ('Malesia', 'MY'),
    'MALTA': ('Malta', 'MT'),
    'MAROCCO': ('Marocco', 'MA'),
    'MOLDAVIA': ('Moldavia', 'MD'),
    'NIGERIA': ('Nigeria', 'NG'),
    'PAESI BASSI': ('Paesi Bassi', 'NL'),
    'PAKISTAN': ('Pakistan', 'PK'),
    'POLONIA': ('Polonia', 'PL'),
    'REGNO UNITO (INGHILTERRA, GALLES E IRLANDA DEL NORD)': ('Regno Unito', 'GB'),
    'REGNO UNITO (SCOZIA)': ('Regno Unito (Scozia)', 'GB'),
    'ROMANIA': ('Romania', 'RO'),
    'RUSSIA': ('Russia', 'RU'),
    'SANTA SEDE': ('Santa Sede', 'VA'),
    'SERBIA': ('Serbia', 'RS'),
    'SIRIA': ('Siria', 'SY'),
    'SOMALIA': ('Somalia', 'SO'),
    'SPAGNA': ('Spagna', 'ES'),
    'SRI LANKA': ('Sri Lanka', 'LK'),
    'SUDAN': ('Sudan', 'SD'),
    'TUNISIA': ('Tunisia', 'TN'),
    'TURCHIA': ('Turchia', 'TR'),
    'UCRAINA': ('Ucraina', 'UA'),
    'UGANDA': ('Uganda', 'UG'),
    'USA': ('USA', 'US'),
    'UZBEKISTAN': ('Uzbekistan', 'UZ'),
    'VIETNAM': ('Vietnam', 'VN'),
    'YEMEN': ('Yemen', 'YE')
}

all_scales_defs = {
    "Base100": { "value": "Base100", "label_it": "Su 100", "label_en": "On 100" },
    "Base20":  { "value": "Base20",  "label_it": "Su 20",  "label_en": "On 20" },
    "Base10":  { "value": "Base10",  "label_it": "Su 10",  "label_en": "On 10" },
    "Base8":   { "value": "Base8",   "label_it": "Su 8",   "label_en": "On 8" },
    "Base5":   { "value": "Base5",   "label_it": "Su 5",   "label_en": "On 5" },
    "Base4":   { "value": "Base4",   "label_it": "Su 4",   "label_en": "On 4" }
}

EXCLUDE_PATTERNS = [
    r'ulteriori requisiti',
    r'requisiti di ammissione',
    r'requisito non richiesto',
    r'uno dei seguenti',
    r'entrambi i requisiti',
    r'tutti i requisiti',
    r'nel caso di iscrizione',
    r'note:',
    r'notes:',
    r'per maggiori',
    r'per ulteriori',
    r'per accedere',
    r'allegato',
    r'circolare',
    r'http://',
    r'https://',
    r'www\.',
    r'positivo superamento delle tre materie',
    r'theory of knowledge',
    r'con superamento di',
    r'con valutazione'
]

def is_header_or_instruction(text):
    if not text:
        return True
    t = text.strip().lower()
    if t.endswith(':') and len(t) < 40:
        return True
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, t):
            return True
    return False

def make_clean_key(text):
    text = re.sub(r'^[●○\-\*\•\s]+', '', text)
    words = re.findall(r'[a-zA-Z0-9]+', text)
    if not words:
        return "Qual"
    # Skip leading numbers or short stop words if possible
    key_words = [w.capitalize() for w in words if len(w) > 1 or w.isupper()]
    if not key_words:
        key_words = [w.capitalize() for w in words]
    key = "".join(key_words[:6])
    return key if key else "Qual"

def clean_label(text):
    lbl = re.sub(r'^[●○\-\*\•\s]+', '', text).strip()
    return lbl

def extract_duration(dur_str):
    if not dur_str or dur_str == "Requisito non richiesto":
        return None
    m = re.search(r'\b(\d{1,2})\b', dur_str)
    if m:
        return int(m.group(1))
    return None

def extract_gpas_from_string(voto_str):
    """Estrae tutte le coppie (valore, scala) trovate nel testo."""
    if not voto_str or voto_str == "Requisito non richiesto":
        return []
    
    results = []
    
    # Matching pattern like "75 su 100", "3.0 su 4.0", "3.5 su 5.0", "15 su 20"
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*su\s*(100|20|10|8|5|4)(?:\.0)?', voto_str, re.IGNORECASE)
    for val_str, scale_num in matches:
        results.append((float(val_str), f"Base{scale_num}"))
        
    # Matching percentage like "60%"
    pct_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', voto_str)
    for val_str in pct_matches:
        results.append((float(val_str), "Base100"))
        
    return results

output_reqs = {}

for item in source_data:
    raw_country = item.get("country", "")
    country_name, code = iso_map.get(raw_country, (raw_country.title(), "UN"))

    tri = item.get("triennale", {})
    mag = item.get("magistrale", {})

    # Detect all GPA scales explicitly used
    tri_voto_raw = tri.get("voto_minimo", "")
    mag_voto_raw = mag.get("voto_minimo", "")
    
    tri_gpas = extract_gpas_from_string(tri_voto_raw)
    mag_gpas = extract_gpas_from_string(mag_voto_raw)
    
    used_scales = set()
    for _, s in tri_gpas:
        used_scales.add(s)
    for _, s in mag_gpas:
        used_scales.add(s)
        
    # Standard scale defaults based on country if none detected
    if not used_scales:
        if country_name in ["Iran", "Francia", "Tunisia", "Marocco", "Algeria", "Camerun"]:
            used_scales.add("Base20")
        elif country_name in ["USA", "Canada", "Filippine", "Pakistan", "Bangladesh", "Sudan", "Somalia"]:
            used_scales.add("Base4")
            used_scales.add("Base100")
        elif country_name in ["Spagna", "Italia", "Colombia", "Brasile", "Messico", "Argentina"]:
            used_scales.add("Base10")
            used_scales.add("Base100")
        else:
            used_scales.add("Base100")
            used_scales.add("Base4")

    # Order scales nicely
    ordered_scales = ["Base100", "Base20", "Base10", "Base8", "Base5", "Base4"]
    gpa_scales_list = [all_scales_defs[s] for s in ordered_scales if s in used_scales]

    # Process Triennale (Undergraduate)
    tri_titoli_raw = tri.get("titoli_richiesti", "")
    tri_altri_raw = tri.get("altri_requisiti", "")
    
    undergrad_quals = []
    undergrad_eligible = []
    
    lines_tri = []
    if tri_titoli_raw and tri_titoli_raw != "Requisito non richiesto":
        lines_tri.extend(tri_titoli_raw.split('\n'))
    elif tri_altri_raw and tri_altri_raw != "Requisito non richiesto":
        lines_tri.extend(tri_altri_raw.split('\n'))

    for line in lines_tri:
        line_clean = clean_label(line)
        if not line_clean or is_header_or_instruction(line_clean):
            continue
            
        key = make_clean_key(line_clean)
        count = 1
        original_key = key
        while any(q["key"] == key for q in undergrad_quals):
            count += 1
            key = f"{original_key}{count}"

        undergrad_quals.append({
            "key": key,
            "label": line_clean,
            "requiresDuration": False
        })
        undergrad_eligible.append(key)

    undergrad_min_gpa = {}
    for val, scale in tri_gpas:
        undergrad_min_gpa[scale] = val

    # Process Magistrale (Postgraduate)
    mag_titoli_raw = mag.get("titoli_richiesti", "")
    mag_altri_raw = mag.get("altri_requisiti", "")
    mag_dur_raw = mag.get("durata_minima", "")
    
    postgrad_quals = []
    postgrad_eligible = []
    min_dur_map = {}
    
    mag_dur_val = extract_duration(mag_dur_raw)

    lines_mag = []
    if mag_titoli_raw and mag_titoli_raw != "Requisito non richiesto":
        lines_mag.extend(mag_titoli_raw.split('\n'))
    elif mag_altri_raw and mag_altri_raw != "Requisito non richiesto":
        lines_mag.extend(mag_altri_raw.split('\n'))

    for line in lines_mag:
        line_clean = clean_label(line)
        if not line_clean or is_header_or_instruction(line_clean):
            continue
            
        key = make_clean_key(line_clean)
        count = 1
        original_key = key
        while any(q["key"] == key for q in postgrad_quals):
            count += 1
            key = f"{original_key}{count}"

        req_dur = mag_dur_val is not None
        postgrad_quals.append({
            "key": key,
            "label": line_clean,
            "requiresDuration": req_dur
        })
        postgrad_eligible.append(key)
        if req_dur:
            min_dur_map[key] = mag_dur_val

    postgrad_min_gpa = {}
    for val, scale in mag_gpas:
        postgrad_min_gpa[scale] = val

    # Keep special custom mappings for India and Iran if they match
    if country_name == "India":
        gpa_scales_list = [all_scales_defs["Base100"], all_scales_defs["Base10"], all_scales_defs["Base8"], all_scales_defs["Base4"]]
    elif country_name == "Iran":
        gpa_scales_list = [all_scales_defs["Base20"]]

    output_reqs[country_name] = {
        "country_code": code,
        "gpa_scales": gpa_scales_list,
        "qualifications": {
            "Undergraduate": undergrad_quals,
            "Postgraduate": postgrad_quals
        },
        "thresholds": {
            "Undergraduate": {
                "eligible_qualifications": undergrad_eligible,
                "min_gpa": undergrad_min_gpa
            },
            "Postgraduate": {
                "eligible_qualifications": postgrad_eligible,
                "min_duration": min_dur_map,
                "min_gpa": postgrad_min_gpa
            }
        },
        "raw_details": {
            "Undergraduate": tri,
            "Postgraduate": mag
        }
    }

# Write output to country_requirements.json
with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump(output_reqs, f, indent=4, ensure_ascii=False)

print(f"Successfully generated updated country_requirements.json with {len(output_reqs)} countries!")
