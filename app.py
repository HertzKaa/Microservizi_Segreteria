"""
Backend Flask per la verifica dell'ammissione tramite Ontologia OWL
Stack: Flask + owlready2 + HermiT Reasoner
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from owlready2 import *
import os
import logging
from datetime import datetime

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inizializza Flask
app = Flask(__name__)
CORS(app)  # Abilita CORS per le richieste dal frontend

# Variabili globali per l'ontologia
onto = None
onto_path = []  # Inizializza come lista vuota, non None
onto_loaded = False  # Flag per tracciare se l'ontologia è stata caricata

# Mapping dei titoli di studio per paese
QUALIFICATIONS_MAP = {
    "India": {
        "Undergraduate": [
            ("AllIndiaSeniorSchool", "AllIndiaSeniorSchoolCertificate", False),
            ("IndianSchoolCert", "IndianSchoolCertificate", False),
            ("IntermediateExam", "IntermediateExaminationCertificate", False),
            ("HigherSecondarySchool", "HigherSecondarySchoolCertificate", False),
            ("HigherSecondaryPartII", "HigherSecondaryExaminationCertificatePartII", False),
        ],
        "Postgraduate": [
            ("HonoursBachelor", "HonoursBachelorDegree", True),
            ("ProfessionalBachelor", "ProfessionalBachelorDegree", True),
            ("PassGeneralBachelor", "PassGeneralBachelorDegree", False),
            ("MasterDegree", "MasterDegree", False),
            ("PostgraduateBachelor", "PostgraduateBachelorDegree", False),
        ]
    },
    "Iran": {
        "Undergraduate": [
            ("DiplomMotevasete", "DiplomEMotevasete", False),
            ("SecondaryEdu2018", "SecondaryEducationFrom2018", False),
            ("Kardani", "Kardani", False),
        ],
        "Postgraduate": [
            ("Karshenasi", "Karshenasi", True),
            ("KarshenasiNapayvasteh", "KarshenasiNapayvasteh", True),
        ]
    }
}

def load_ontology():
    """Carica l'ontologia OWL dal file locale"""
    global onto, onto_path, onto_loaded

    # Prova prima il file RDF/XML (migliore support), poi Turtle
    ontology_files = ["Protege0-.rdf", "Protege0-.ttl"]
    ontology_file = None
    
    for file in ontology_files:
        if os.path.exists(file):
            ontology_file = file
            break
    
    if not ontology_file:
        logger.error(f"File ontologia non trovato: {' o '.join(ontology_files)}")
        raise FileNotFoundError(f"Impossibile trovare: {' o '.join(ontology_files)}")

    logger.info(f"Caricamento ontologia da: {ontology_file}")

    # Configura il percorso (onto_path è già una lista vuota)
    onto_path.append(".")

    # Carica l'ontologia
    try:
        # Usa il percorso assoluto per evitare problemi di path
        full_path = os.path.abspath(ontology_file)
        
        # Su Windows, converti il percorso correttamente per file://
        if os.name == 'nt':  # Windows
            # Converti backslash in slash e aggiungi il terzo slash
            file_url = f"file:///{full_path.replace(os.sep, '/')}"
        else:  # Linux/Mac
            file_url = f"file://{full_path}"
        
        logger.info(f"Caricamento ontologia da: {full_path}")
        logger.info(f"URL file: {file_url}")
        
        # Carica usando il file URI corretto
        onto = get_ontology(file_url).load()
        logger.info("Ontologia caricata con successo")
        
        # Log info sull'ontologia
        try:
            num_classes = len(list(onto.classes()))
            logger.info(f"Ontologia contiene {num_classes} classi")
        except:
            pass
            
        onto_loaded = True
        return onto
    except Exception as e:
        logger.error(f"Errore nel caricamento dell'ontologia: {str(e)}", exc_info=True)
        raise

@app.before_request
def init_ontology():
    """Inizializza l'ontologia alla prima richiesta"""
    global onto, onto_path, onto_loaded
    if not onto_loaded:
        try:
            load_ontology()
        except Exception as e:
            logger.error(f"Impossibile inizializzare l'ontologia: {str(e)}")
            raise

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint di health check"""
    return jsonify({"status": "ok", "message": "Backend is running"}), 200

@app.route('/check-admission', methods=['POST'])
def check_admission():
    """
    Endpoint principale per la verifica dell'ammissione
    Riceve i dati dello studente in JSON e ritorna l'esito dell'ammissione
    """
    try:
        data = request.get_json()
        logger.info(f"Richiesta ricevuta: {data}")

        # Validazione dei dati ricevuti
        required_fields = ['name', 'course', 'country', 'qualification', 'gpa', 'gpaScale']
        if not all(field in data for field in required_fields):
            return jsonify({
                "admitted": False,
                "error": "Campi obbligatori mancanti"
            }), 400

        # Estrai i dati
        name = data.get('name', 'TestStudent').replace(' ', '_')
        course = data.get('course')  # "Undergraduate" o "Postgraduate"
        country = data.get('country')  # "India" o "Iran"
        qualification_key = data.get('qualification')
        duration = data.get('duration')
        gpa = float(data.get('gpa', 0))
        gpa_scale = data.get('gpaScale')  # "Base100", "Base10", etc.

        # Validazione base
        if course not in ["Undergraduate", "Postgraduate"]:
            return jsonify({"admitted": False, "error": "Corso non valido"}), 400

        if country not in ["India", "Iran"]:
            return jsonify({"admitted": False, "error": "Paese non valido"}), 400

        logger.info(f"Elaborazione: {name} - {country} - {course} - {qualification_key}")

        # Determina la classe di qualifica
        found_qual = False
        qual_class_name = None
        requires_duration = False

        if country in QUALIFICATIONS_MAP and course in QUALIFICATIONS_MAP[country]:
            for key, class_name, requires_dur in QUALIFICATIONS_MAP[country][course]:
                if key == qualification_key:
                    qual_class_name = class_name
                    requires_duration = requires_dur
                    found_qual = True
                    break

        if not found_qual:
            logger.error(f"Qualifica non trovata: {qualification_key}")
            return jsonify({"admitted": False, "error": "Qualifica non valida"}), 400

        # Verifica che la durata sia presente se richiesta
        if requires_duration and not duration:
            return jsonify({"admitted": False, "error": "Durata obbligatoria per questa qualifica"}), 400

        # Crea gli individui nell'ontologia
        admitted = create_individuals_and_check(
            onto, name, country, course,
            qual_class_name, duration, gpa, gpa_scale
        )

        logger.info(f"Risultato ammissione: {admitted}")

        return jsonify({
            "admitted": admitted,
            "student": name,
            "country": country,
            "course": course
        }), 200

    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {str(e)}", exc_info=True)
        return jsonify({
            "admitted": False,
            "error": f"Errore del server: {str(e)}"
        }), 500

def create_individuals_and_check(onto, student_name, country, course,
                                  qual_class_name, duration, gpa, gpa_scale):
    """
    Crea gli individui temporanei, esegue il reasoner e verifica l'ammissione
    """
    try:
        # Determinazione delle classi
        student_class = "IranianStudent" if country == "Iran" else "IndianStudent"
        course_class = "PostgraduateCourse" if course == "Postgraduate" else "UndergraduateCourse"

        # Nomi unici per evitare conflitti con richieste multiple
        student_individual_name = f"Student_{student_name}_{datetime.now().timestamp()}"
        course_individual_name = f"Course_{course}_{datetime.now().timestamp()}"
        qual_individual_name = f"Qualification_{student_name}_{datetime.now().timestamp()}"

        logger.info(f"Creazione individui: {student_individual_name}, {course_individual_name}, {qual_individual_name}")

        # 1. Crea l'individuo Course
        with onto:
            course_ind = onto[course_class](course_individual_name)
            logger.info(f"Corso creato: {course_individual_name} ({course_class})")

            # 2. Crea l'individuo Qualification
            qual_class = onto[qual_class_name]
            qual_ind = qual_class(qual_individual_name)
            logger.info(f"Qualifica creata: {qual_individual_name} ({qual_class_name})")

            # 3. Aggiungi proprietà alla qualifica
            if duration:
                qual_ind.hasDurationInYears = [float(duration)]
                logger.info(f"Durata impostata: {duration} anni")

            if gpa:
                gpa_property_name = f"hasGPA_{gpa_scale}"
                gpa_property = onto[gpa_property_name]
                gpa_property[qual_ind].append(float(gpa))
                logger.info(f"GPA impostato: {gpa} ({gpa_property_name})")

            # 4. Crea l'individuo Student
            student_class = onto[student_class]
            student_ind = student_class(student_individual_name)
            logger.info(f"Studente creato: {student_individual_name} ({student_class.name})")

            # 5. Collega lo studente al corso
            student_ind.hasAppliedFor.append(course_ind)
            logger.info(f"Collegamento creato: {student_individual_name} -> hasAppliedFor -> {course_individual_name}")

            # 6. Collega lo studente alla qualifica
            student_ind.hasQualification.append(qual_ind)
            logger.info(f"Collegamento creato: {student_individual_name} -> hasQualification -> {qual_individual_name}")

            # 7. Sincronizza e esegui il reasoner
            logger.info("Esecuzione del reasoner...")
            sync_reasoner(infer_property_values=True)
            logger.info("Reasoner completato")

            # 8. Verifica l'ammissione
            eligibility_classes = [
                "EligibleIndianUndergraduateStudent",
                "EligibleIndianPostgraduateStudent",
                "EligibleIranianUndergraduateStudent",
                "EligibleIranianPostgraduateStudent"
            ]

            admitted = False
            for elig_class_name in eligibility_classes:
                elig_class = onto[elig_class_name]
                if student_ind in elig_class.instances():
                    admitted = True
                    logger.info(f"Studente ammesso in classe: {elig_class_name}")
                    break

            if not admitted:
                logger.info(f"Studente NON ammesso in alcuna classe di eligibilità")

            # 9. Elimina gli individui per pulire l'ontologia
            logger.info(f"Eliminazione degli individui temporanei...")
            destroy_entity(student_ind)
            destroy_entity(course_ind)
            destroy_entity(qual_ind)

            # Sincronizza di nuovo dopo l'eliminazione
            sync_reasoner(infer_property_values=True)
            logger.info("Pulizia completata, ontologia sincronizzata")

            return admitted

    except Exception as e:
        logger.error(f"Errore durante la creazione degli individui: {str(e)}", exc_info=True)
        raise

@app.route('/qualifications', methods=['GET'])
def get_qualifications():
    """Endpoint per ottenere le qualifiche disponibili per un paese/corso"""
    country = request.args.get('country')
    course = request.args.get('course')

    if country not in QUALIFICATIONS_MAP or course not in QUALIFICATIONS_MAP[country]:
        return jsonify({"qualifications": []}), 400

    quals = QUALIFICATIONS_MAP[country][course]
    return jsonify({
        "qualifications": [
            {"key": key, "label": label, "requiresDuration": requires_duration}
            for key, label, requires_duration in quals
        ]
    }), 200

@app.route('/gpa-scales', methods=['GET'])
def get_gpa_scales():
    """Endpoint per ottenere le scale GPA disponibili per un paese"""
    country = request.args.get('country')

    if country == "Iran":
        scales = [{"value": "Base20", "label": "Su 20"}]
    elif country == "India":
        scales = [
            {"value": "Base100", "label": "Su 100"},
            {"value": "Base10", "label": "Su 10"},
            {"value": "Base8", "label": "Su 8"},
            {"value": "Base4", "label": "Su 4"}
        ]
    else:
        return jsonify({"scales": []}), 400

    return jsonify({"scales": scales}), 200

if __name__ == '__main__':
    logger.info("Avvio del backend Flask...")
    app.run(debug=True, host='0.0.0.0', port=5000)

