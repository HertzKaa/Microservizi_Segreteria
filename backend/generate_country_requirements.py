import os
import json
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
req_json_path = os.path.join(script_dir, "minimum_requirements", "requirements.json")
out_json_path = os.path.join(script_dir, "country_requirements.json")

existing_reqs = {}
if os.path.exists(out_json_path):
    with open(out_json_path, "r", encoding="utf-8") as f:
        existing_reqs = json.load(f)

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

all_scales = [
    { "value": "Base100", "label_it": "Su 100", "label_en": "On 100" },
    { "value": "Base20", "label_it": "Su 20", "label_en": "On 20" },
    { "value": "Base10", "label_it": "Su 10", "label_en": "On 10" },
    { "value": "Base8", "label_it": "Su 8", "label_en": "On 8" },
    { "value": "Base4", "label_it": "Su 4", "label_en": "On 4" }
]

def make_clean_key(text):
    words = re.findall(r'[a-zA-Z0-9]+', text)
    if not words:
        return "Qual"
    key = "".join(w.capitalize() for w in words[:6])
    return key if key else "Qual"

def extract_duration(dur_str):
    if not dur_str or dur_str == "Requisito non richiesto":
        return None
    m = re.search(r'\b(\d{1,2})\b', dur_str)
    if m:
        return int(m.group(1))
    return None

def extract_gpa(voto_str):
    if not voto_str or voto_str == "Requisito non richiesto":
        return None, None
    m_scale = re.search(r'(\d+(?:\.\d+)?)\s*su\s*(100|20|10|8|4)', voto_str, re.IGNORECASE)
    if m_scale:
        val = float(m_scale.group(1))
        scale = f"Base{m_scale.group(2)}"
        return val, scale
    
    m_pct = re.search(r'(\d+(?:\.\d+)?)\s*%', voto_str)
    if m_pct:
        return float(m_pct.group(1)), "Base100"
        
    m_num = re.search(r'\b(\d+(?:\.\d+)?)\b', voto_str)
    if m_num:
        val = float(m_num.group(1))
        if val > 20:
            return val, "Base100"
        elif val > 10:
            return val, "Base20"
        elif val > 4:
            return val, "Base10"
        else:
            return val, "Base4"
            
    return None, None

output_reqs = {}

for item in source_data:
    raw_country = item.get("country", "")
    country_name, code = iso_map.get(raw_country, (raw_country.title(), "UN"))

    if country_name in existing_reqs:
        output_reqs[country_name] = existing_reqs[country_name]
        continue

    tri = item.get("triennale", {})
    tri_titoli_raw = tri.get("titoli_richiesti", "")
    tri_voto_raw = tri.get("voto_minimo", "")
    tri_dur_raw = tri.get("durata_minima", "")
    tri_altri_raw = tri.get("altri_requisiti", "")

    undergrad_quals = []
    undergrad_eligible = []
    
    if tri_titoli_raw and tri_titoli_raw != "Requisito non richiesto":
        lines = [l.strip() for l in tri_titoli_raw.split('\n') if l.strip()]
        for line in lines:
            key = make_clean_key(line)
            count = 1
            original_key = key
            while any(q["key"] == key for q in undergrad_quals):
                count += 1
                key = f"{original_key}{count}"

            undergrad_quals.append({
                "key": key,
                "label": line,
                "requiresDuration": False
            })
            undergrad_eligible.append(key)
    elif tri_altri_raw and tri_altri_raw != "Requisito non richiesto":
        line = tri_altri_raw.split('\n')[0].strip()
        key = make_clean_key(line)
        undergrad_quals.append({
            "key": key,
            "label": line,
            "requiresDuration": False
        })
        undergrad_eligible.append(key)

    tri_gpa_val, tri_gpa_scale = extract_gpa(tri_voto_raw)
    undergrad_min_gpa = {}
    if tri_gpa_val is not None and tri_gpa_scale:
        undergrad_min_gpa[tri_gpa_scale] = tri_gpa_val

    mag = item.get("magistrale", {})
    mag_titoli_raw = mag.get("titoli_richiesti", "")
    mag_voto_raw = mag.get("voto_minimo", "")
    mag_dur_raw = mag.get("durata_minima", "")
    mag_altri_raw = mag.get("altri_requisiti", "")

    postgrad_quals = []
    postgrad_eligible = []
    min_dur_map = {}

    mag_dur_val = extract_duration(mag_dur_raw)

    if mag_titoli_raw and mag_titoli_raw != "Requisito non richiesto":
        lines = [l.strip() for l in mag_titoli_raw.split('\n') if l.strip()]
        for line in lines:
            key = make_clean_key(line)
            count = 1
            original_key = key
            while any(q["key"] == key for q in postgrad_quals):
                count += 1
                key = f"{original_key}{count}"

            req_dur = mag_dur_val is not None
            postgrad_quals.append({
                "key": key,
                "label": line,
                "requiresDuration": req_dur
            })
            postgrad_eligible.append(key)
            if req_dur:
                min_dur_map[key] = mag_dur_val

    elif mag_altri_raw and mag_altri_raw != "Requisito non richiesto":
        line = mag_altri_raw.split('\n')[0].strip()
        key = make_clean_key(line)
        req_dur = mag_dur_val is not None
        postgrad_quals.append({
            "key": key,
            "label": line,
            "requiresDuration": req_dur
        })
        postgrad_eligible.append(key)
        if req_dur:
            min_dur_map[key] = mag_dur_val

    mag_gpa_val, mag_gpa_scale = extract_gpa(mag_voto_raw)
    postgrad_min_gpa = {}
    if mag_gpa_val is not None and mag_gpa_scale:
        postgrad_min_gpa[mag_gpa_scale] = mag_gpa_val

    output_reqs[country_name] = {
        "country_code": code,
        "gpa_scales": all_scales,
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
        }
    }

with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump(output_reqs, f, indent=4, ensure_ascii=False)

print(f"Successfully generated country_requirements.json with {len(output_reqs)} countries!")
