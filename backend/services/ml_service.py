import os
import logging
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

# Stato del servizio ML
model_artifact = None
is_model_loaded = False

def load_ml_model(force_reload=False):
    """Carica l'artefatto del modello di Machine Learning dal file joblib"""
    global model_artifact, is_model_loaded
    
    if is_model_loaded and model_artifact is not None and not force_reload:
        return True
    
    # Percorsi possibili del modello salvato
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'machineLearning', 'admission_model.joblib'),
        os.path.join(os.path.dirname(__file__), '..', 'machineLearning', 'admission_model.joblib'),
        'machineLearning/admission_model.joblib'
    ]
    
    model_path = None
    for p in possible_paths:
        abs_p = os.path.abspath(p)
        if os.path.exists(abs_p):
            model_path = abs_p
            break
            
    if not model_path:
        logger.warning("File admission_model.joblib non trovato. Il servizio ML sarà disabilitato.")
        is_model_loaded = False
        return False
        
    try:
        model_artifact = joblib.load(model_path)
        logger.info(f"Modello ML caricato con successo da: {model_path}")
        is_model_loaded = True
        return True
    except Exception as e:
        logger.error(f"Errore durante il caricamento del modello ML: {e}", exc_info=True)
        is_model_loaded = False
        return False

def convert_gpa_to_percentage(gpa, gpa_scale):
    """Converte il GPA in percentuale normalizzata [0.0, 1.0]"""
    if gpa is None:
        return 0.0
        
    gpa = float(gpa)
    if gpa_scale == "Base20":
        return min(max(gpa / 20.0, 0.0), 1.0)
    elif gpa_scale == "Base10":
        return min(max(gpa / 10.0, 0.0), 1.0)
    elif gpa_scale == "Base8":
        return min(max(gpa / 8.0, 0.0), 1.0)
    elif gpa_scale == "Base4":
        return min(max(gpa / 4.0, 0.0), 1.0)
    elif gpa_scale == "Base100":
        return min(max(gpa / 100.0, 0.0), 1.0)
    else:
        # Default se la scala non è riconosciuta (es. se la percentuale è già tra 0 e 1 o 0 e 100)
        return min(max(gpa / 100.0, 0.0), 1.0) if gpa > 1.0 else min(max(gpa, 0.0), 1.0)

def evaluate_ml_admission(country, course, birth_year=None, age=None, gpa=None, gpa_scale=None, gender="M"):
    """
    Valuta l'ammissibilità di uno studente da Iran o India usando il modello Decision Tree.
    Ritorna un dict con:
      - 'evaluatable': bool (True se valutabile da ML)
      - 'admitted': bool (True se approvato dal modello ML)
      - 'score': float (probabilità di approvazione [0..1])
      - 'explanation': str (dettagli motivazionali)
    """
    global model_artifact, is_model_loaded
    
    load_ml_model()
    if not is_model_loaded or model_artifact is None:
        return {
            'evaluatable': False,
            'admitted': False,
            'score': 0.0,
            'explanation': 'Modello ML non disponibile.'
        }

    country_upper = str(country).upper().strip()
    if country_upper not in ['IRAN', 'INDIA']:
        return {
            'evaluatable': False,
            'admitted': False,
            'score': 0.0,
            'explanation': f"Il modello ML è attualmente addestrato per candidati provenienti da Iran e India (ricevuto: {country})."
        }

    clf = model_artifact['classifier']
    feature_names = model_artifact['feature_names']
    media_eta_series = model_artifact['media_eta_corso_series']
    std_eta_series = model_artifact['std_eta_corso_series']
    target_smooth = model_artifact['target_smooth']
    global_mean = model_artifact['global_mean']
    voto_mean_smooth = model_artifact['voto_mean_smooth']
    voto_stats = model_artifact['voto_stats']
    global_voto_mean = model_artifact['global_voto_mean']
    global_voto_std = model_artifact['global_voto_std']
    label_encoders = model_artifact['label_encoders']

    # 1. Determinazione tipo corso di codice per il modello (es. 'LM' per Postgraduate, 'L2' per Undergraduate)
    tipo_corso_cod = 'LM' if course in ['Postgraduate', 'Magistrale', 'LM'] else 'L2'
    
    # 2. Calcolo Età
    current_year = datetime.now().year
    if birth_year is not None and str(birth_year).isdigit():
        calculated_age = current_year - int(birth_year)
    elif age is not None and str(age).isdigit():
        calculated_age = int(age)
    else:
        # Default stimato in base al tipo di corso se l'età non è fornita
        calculated_age = 25 if tipo_corso_cod == 'LM' else 21

    # Media e Std per tipo corso
    mean_age_course = media_eta_series.get(tipo_corso_cod, 25.0)
    std_age_course = std_eta_series.get(tipo_corso_cod, 4.0)
    if pd.isna(std_age_course) or std_age_course == 0:
        std_age_course = 1.0

    eta_diff_corso = calculated_age - mean_age_course
    eta_norm_corso = (calculated_age - mean_age_course) / std_age_course

    # 3. Voto percentuale e normalizzato
    voto_pct = convert_gpa_to_percentage(gpa, gpa_scale)
    
    cit_key = country_upper
    c_mean = voto_mean_smooth.get(cit_key, global_voto_mean)
    c_std = voto_stats.loc[cit_key, 'std'] if (voto_stats is not None and cit_key in voto_stats.index) else global_voto_std
    c_count = voto_stats.loc[cit_key, 'count'] if (voto_stats is not None and cit_key in voto_stats.index) else 0

    if pd.isna(c_std) or c_std == 0 or c_count < 5:
        std_val = global_voto_std if (not pd.isna(global_voto_std) and global_voto_std > 0) else 1.0
    else:
        std_val = c_std

    voto_norm = (voto_pct - c_mean) / std_val
    media_voto_naz = c_mean
    cittadinanza_encoded = target_smooth.get(cit_key, global_mean)

    # 4. Costruzione del dizionario di input per tutte le feature del DecisionTree
    input_data = {}
    for feat in feature_names:
        if feat == 'ETA_NORM_CORSO':
            input_data[feat] = eta_norm_corso
        elif feat == 'ETA_DIFF_CORSO':
            input_data[feat] = eta_diff_corso
        elif feat == 'VOTO_NORM':
            input_data[feat] = voto_norm
        elif feat == 'MEDIA_VOTO_NAZ':
            input_data[feat] = media_voto_naz
        elif feat == 'CITTADINANZA_ENCODED':
            input_data[feat] = cittadinanza_encoded
        elif feat == 'SESSO':
            # 1 per M, 0 per F se in LabelEncoder o numerico
            input_data[feat] = 1 if str(gender).upper().startswith('M') else 0
        elif feat == 'TIPO_CORSO_COD':
            if 'TIPO_CORSO_COD' in label_encoders:
                le = label_encoders['TIPO_CORSO_COD']
                val = tipo_corso_cod if tipo_corso_cod in le.classes_ else le.classes_[0]
                input_data[feat] = le.transform([val])[0]
            else:
                input_data[feat] = 1
        elif feat in label_encoders:
            le = label_encoders[feat]
            # Usa il valore predefinito la prima classe valida
            input_data[feat] = le.transform([le.classes_[0]])[0]
        else:
            input_data[feat] = 0.0

    df_input = pd.DataFrame([input_data])[feature_names]

    # 5. Esecuzione predizione ML e valutazione continua del profilo (Curva Sigmoide Liscia)
    import math
    prediction = int(clf.predict(df_input)[0])
    probabilities = clf.predict_proba(df_input)[0]
    raw_score = float(probabilities[1]) if len(probabilities) > 1 else float(prediction)
    
    # Calcolo dello scostamento dell'età sulla soglia di flesso (v0 = 0.45 per ammettere votazioni dal 50% in su)
    age_shift = 0.0
    if float(eta_diff_corso) > 4.0:
        age_shift = (float(eta_diff_corso) - 4.0) * 0.02
    
    v0 = 0.45 + age_shift
    k = 7.5
    
    # Sigmoide continua e liscia: nessuna discontinuità o salto tra voti vicini (es. 49% vs 50% o 79% vs 80%)
    sigmoid_score = 1.0 / (1.0 + math.exp(-k * (voto_pct - v0)))
    
    # Integrazione col modello ensemble
    score = float(min(max(0.75 * sigmoid_score + 0.25 * raw_score, 0.01), 0.99))
    
    # Ammissibilità accademica: idoneo se voto_pct >= 45% (o score >= 50%) ed età entro i limiti di tolleranza
    admitted = bool((voto_pct >= 0.45 or prediction == 1) and float(eta_diff_corso) <= 6.0)

    if not admitted:
        if voto_pct < 0.45:
            explanation = (f"Candidato non idoneo secondo il modello decisionale per {country}. "
                           f"La votazione conseguita ({voto_pct*100:.1f}% su scala {gpa_scale}) risulta insufficiente "
                           f"rispetto ai requisiti accademici di ammissibilità.")
        else:
            explanation = (f"Candidato non idoneo secondo il modello decisionale per {country}. "
                           f"Valutazione basata sulle soglie di età relativa ({float(eta_diff_corso):+.1f} anni rispetto alla media del corso) "
                           f"e sulla competitività del voto normalizzato.")
    else:
        explanation = (f"Candidato idoneo secondo il modello decisionale per {country}. "
                       f"Profilo competitivo per voto accademico ({voto_pct*100:.1f}% su scala {gpa_scale}) "
                       f"ed età ponderata rispetto al corso (scostamento {float(eta_diff_corso):+.1f} anni).")

    # 6. Controllo criticità sotto-età (Warning)
    min_age_required = 17 if tipo_corso_cod == 'L2' else 20
    has_age_warning = bool(calculated_age < min_age_required)
    age_warning_message = ""
    if has_age_warning:
        age_warning_message = (f"Criticità Età: Il candidato ha un'età calcolata di {calculated_age} anni "
                               f"(inferiore all'età minima consigliata di {min_age_required} anni per l'accesso a un corso {course}).")

    return {
        'evaluatable': True,
        'admitted': bool(admitted),
        'score': round(float(score), 4),
        'explanation': str(explanation),
        'has_age_warning': has_age_warning,
        'age_warning_message': age_warning_message,
        'details': {
            'country': str(country_upper),
            'course_type': str(tipo_corso_cod),
            'calculated_age': int(calculated_age),
            'eta_diff_corso': round(float(eta_diff_corso), 2),
            'voto_percentage': round(float(voto_pct * 100), 2),
            'gpa_scale': str(gpa_scale),
            'voto_norm': round(float(voto_norm), 2)
        }
    }
