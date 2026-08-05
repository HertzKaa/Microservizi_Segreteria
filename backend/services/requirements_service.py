import os
import json
import logging
import threading
from config import ADMISSION_THRESHOLDS, QUALIFICATIONS_MAP

logger = logging.getLogger(__name__)

REQUIREMENTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'country_requirements.json')
requirements_lock = threading.Lock()

# Cache in memoria
_cached_requirements = None

def initialize_default_requirements():
    """Costruisce la configurazione iniziale di default leggendola da config.py"""
    default_reqs = {}
    
    # Lista delle nazioni configurate originariamente
    countries = ["India", "Iran"]
    
    for country in countries:
        # GPA Scales di default
        if country == "Iran":
            scales = [{"value": "Base20", "label_it": "Su 20", "label_en": "On 20"}]
        else:
            scales = [
                {"value": "Base100", "label_it": "Su 100", "label_en": "On 100"},
                {"value": "Base10", "label_it": "Su 10", "label_en": "On 10"},
                {"value": "Base8", "label_it": "Su 8", "label_en": "On 8"},
                {"value": "Base4", "label_it": "Su 4", "label_en": "On 4"}
            ]
            
        default_reqs[country] = {
            "country_code": "IN" if country == "India" else "IR",
            "gpa_scales": scales,
            "qualifications": {
                "Undergraduate": [],
                "Postgraduate": []
            },
            "thresholds": {
                "Undergraduate": {
                    "eligible_qualifications": [],
                    "min_gpa": {}
                },
                "Postgraduate": {
                    "eligible_qualifications": [],
                    "min_duration": {},
                    "min_gpa": {}
                }
            }
        }
        
        # Mappiamo le qualifiche
        for course in ["Undergraduate", "Postgraduate"]:
            if country in QUALIFICATIONS_MAP and course in QUALIFICATIONS_MAP[country]:
                for key, label, req_dur in QUALIFICATIONS_MAP[country][course]:
                    default_reqs[country]["qualifications"][course].append({
                        "key": key,
                        "label": label,
                        "requiresDuration": req_dur
                    })
                    
            if country in ADMISSION_THRESHOLDS and course in ADMISSION_THRESHOLDS[country]:
                rules = ADMISSION_THRESHOLDS[country][course]
                default_reqs[country]["thresholds"][course]["eligible_qualifications"] = rules.get("eligible_qualifications", [])
                default_reqs[country]["thresholds"][course]["min_gpa"] = rules.get("min_gpa", {})
                if "min_duration" in rules:
                    default_reqs[country]["thresholds"][course]["min_duration"] = rules.get("min_duration", {})
                    
    return default_reqs

def load_requirements(force_reload=False):
    """Carica i requisiti dal file JSON. Inizializza se non presente."""
    global _cached_requirements
    
    with requirements_lock:
        if _cached_requirements is not None and not force_reload:
            return _cached_requirements
            
        if not os.path.exists(REQUIREMENTS_FILE):
            logger.info("country_requirements.json non trovato, inizializzazione con i valori di default di config.py...")
            default_reqs = initialize_default_requirements()
            try:
                with open(REQUIREMENTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(default_reqs, f, indent=4, ensure_ascii=False)
                _cached_requirements = default_reqs
            except Exception as e:
                logger.error(f"Impossibile scrivere il file di requisiti di default: {e}")
                return default_reqs
        else:
            try:
                with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as f:
                    _cached_requirements = json.load(f)
            except Exception as e:
                logger.error(f"Errore di lettura da country_requirements.json: {e}. Uso fallback defaults.")
                return initialize_default_requirements()
                
        return _cached_requirements

def save_requirements(reqs):
    """Salva i requisiti nel file JSON in modo atomico e aggiorna la cache."""
    global _cached_requirements
    with requirements_lock:
        try:
            # Scrittura atomica temporanea
            temp_file = REQUIREMENTS_FILE + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(reqs, f, indent=4, ensure_ascii=False)
            if os.path.exists(REQUIREMENTS_FILE):
                os.remove(REQUIREMENTS_FILE)
            os.rename(temp_file, REQUIREMENTS_FILE)
            _cached_requirements = reqs
            return True
        except Exception as e:
            logger.error(f"Errore durante il salvataggio dei requisiti: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False

def get_qualifications_map_dynamic():
    """Genera al volo la mappa QUALIFICATIONS_MAP leggendo i dati JSON correnti"""
    reqs = load_requirements()
    qual_map = {}
    for country, details in reqs.items():
        qual_map[country] = {}
        for course in ["Undergraduate", "Postgraduate"]:
            quals_list = details.get("qualifications", {}).get(course, [])
            qual_map[country][course] = [
                (q["key"], q["label"], q["requiresDuration"]) for q in quals_list
            ]
    return qual_map

def get_admission_thresholds_dynamic():
    """Genera al volo la mappa ADMISSION_THRESHOLDS leggendo i dati JSON correnti"""
    reqs = load_requirements()
    thresholds = {}
    for country, details in reqs.items():
        thresholds[country] = {}
        for course in ["Undergraduate", "Postgraduate"]:
            t_data = details.get("thresholds", {}).get(course, {})
            # Assicuriamoci che min_duration sia mappato correttamente se presente
            course_thresh = {
                "eligible_qualifications": t_data.get("eligible_qualifications", []),
                "min_gpa": t_data.get("min_gpa", {})
            }
            if "min_duration" in t_data:
                course_thresh["min_duration"] = t_data["min_duration"]
            thresholds[country][course] = course_thresh
    return thresholds
