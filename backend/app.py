"""
Backend Flask per la verifica dell'ammissione tramite Ontologia OWL
Stack: Flask + owlready2 + HermiT Reasoner
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from owlready2 import *
import os
import logging
from datetime import datetime
import threading
import json

# Tentativo di importare openpyxl per il caricamento massivo tramite file Excel
try:
    import openpyxl
except ImportError:
    openpyxl = None


# Lock per garantire la scrittura thread-safe sul file unico
file_lock = threading.Lock()
TTL_FILE_PATH = "students_registered.ttl"

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
    ontology_files = ["../ontology/Protege0-.rdf", "../ontology/Protege0-.ttl"]
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
            file_url = full_path
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


@app.route('/register-student', methods=['POST'])
def register_student():
    """
    Endpoint per registrare uno studente e appenderlo in un unico file Turtle (.ttl) sul server
    """
    try:
        data = request.get_json()
        logger.info(f"Richiesta di registrazione sul server: {data}")

        required_fields = ['name', 'course', 'country', 'qualificationTitle']
        if not all(field in data for field in required_fields):
            return jsonify({"status": "error", "message": "Campi obbligatori mancanti"}), 400

        name = data.get('name').strip()
        course = data.get('course')
        country = data.get('country')
        qualification_title = data.get('qualificationTitle')
        duration = data.get('duration')
        gpa = data.get('gpa')
        gpa_scale = data.get('gpaScale')

        file_exists = os.path.exists(TTL_FILE_PATH)

        # Sanatizzazione URI (spazi -> underscore)
        student_uri = name.replace(' ', '_')
        course_uri = f"Course_{course.replace(' ', '_')}"
        cert_uri = f"Cert_{student_uri}"
        course_type = "PostgraduateCourse" if course == 'Magistrale' else "UndergraduateCourse"
        student_class = "IndianStudent" if country == 'India' else "IranianStudent"

        turtle_chunk = ""
        if not file_exists:
            # Scrittura dei prefissi standard se il file viene creato per la prima volta
            turtle_chunk += """@prefix : <http://example.org/university-admission#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""

        # Generazione triple dello studente
        turtle_chunk += f"# Studente: {name}\n"
        turtle_chunk += f":{student_uri} rdf:type owl:NamedIndividual ;\n"
        turtle_chunk += f"    rdf:type :{student_class} ;\n"
        turtle_chunk += f"    :hasAppliedFor :{course_uri}"

        if qualification_title != 'NoCertificate':
            turtle_chunk += f" ;\n    :hasQualification :{cert_uri}"

        turtle_chunk += " .\n\n"

        turtle_chunk += f":{course_uri} rdf:type owl:NamedIndividual ;\n"
        turtle_chunk += f"    rdf:type :{course_type} ;\n"
        turtle_chunk += f"    :courseName \"{course}\"^^xsd:string .\n"

        if qualification_title != 'NoCertificate':
            turtle_chunk += f"\n:{cert_uri} rdf:type owl:NamedIndividual ;\n"
            turtle_chunk += f"    rdf:type :{qualification_title}"

            if duration:
                turtle_chunk += f" ;\n    :hasDurationInYears \"{duration}\"^^xsd:integer"

            if gpa and course == 'Magistrale':
                gpa_prop = f"hasGPA_{gpa_scale}"
                turtle_chunk += f" ;\n    :{gpa_prop} \"{gpa}\"^^xsd:decimal"

            turtle_chunk += " .\n"

        turtle_chunk += "\n"

        # Scrittura controllata sul file unico
        with file_lock:
            with open(TTL_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(turtle_chunk)

        logger.info(f"Studente {name} salvato con successo nel file unico sul server.")
        return jsonify({
            "status": "success",
            "message": f"Studente '{name}' salvato con successo sul server nel file unico!"
        }), 200

    except Exception as e:
        logger.error(f"Errore durante il salvataggio: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": f"Errore interno del server: {str(e)}"}), 500

@app.route('/download-registered-ttl', methods=['GET'])
def download_registered_ttl():
    """
    Endpoint per scaricare il file unico degli studenti registrati sul server
    """
    if not os.path.exists(TTL_FILE_PATH):
        return jsonify({"status": "error", "message": "Nessuno studente salvato sul server al momento."}), 404

    return send_file(TTL_FILE_PATH, as_attachment=True, download_name="students_registered.ttl")

@app.route('/clear-registered-ttl', methods=['POST'])
def clear_registered_ttl():
    """
    Endpoint per azzerare il file sul server
    """
    try:
        with file_lock:
            if os.path.exists(TTL_FILE_PATH):
                os.remove(TTL_FILE_PATH)
                logger.info("File unico rimosso con successo dal server.")
            return jsonify({"status": "success", "message": "File di archivio sul server azzerato."}), 200
    except Exception as e:
        logger.error(f"Errore durante la cancellazione del file: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/check-admission-batch', methods=['POST'])
def check_admission_batch():
    """
    Endpoint per il caricamento massivo e la verifica in batch di studenti (JSON o Excel)
    """
    try:
        # Verifica la presenza del file nella richiesta
        if 'file' not in request.files:
            return jsonify({"error": "Nessun file caricato"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "File non selezionato"}), 400

        filename = file.filename.lower()
        students_to_check = []

        # 1. PARSING FILE JSON
        if filename.endswith('.json'):
            try:
                file_content = file.read().decode('utf-8')
                students_to_check = json.loads(file_content)
                # Se è un singolo oggetto anziché un array, lo inseriamo in una lista
                if isinstance(students_to_check, dict):
                    students_to_check = [students_to_check]
            except Exception as e:
                return jsonify({"error": f"Errore di parsing JSON: {str(e)}"}), 400

        # 2. PARSING FILE EXCEL (.xlsx, .xls)
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            if openpyxl is None:
                return jsonify({"error": "Libreria openpyxl non installata sul server. Esegui 'pip install openpyxl'"}), 500

            try:
                wb = openpyxl.load_workbook(file, data_only=True)
                sheet = wb.active

                # Leggiamo la prima riga per mappare le intestazioni delle colonne
                headers = [str(cell.value).strip().lower() if cell.value else "" for cell in sheet[1]]

                # Associazione flessibile delle colonne basata sul nome della colonna
                mapping = {
                    "name": -1, "course": -1, "country": -1,
                    "qualification": -1, "duration": -1, "gpa": -1, "gpaScale": -1
                }

                for idx, h in enumerate(headers):
                    if "name" in h or "nome" in h: mapping["name"] = idx
                    elif "course" in h or "corso" in h: mapping["course"] = idx
                    elif "country" in h or "paese" in h: mapping["country"] = idx
                    elif "qualification" in h or "titolo" in h: mapping["qualification"] = idx
                    elif "duration" in h or "durata" in h: mapping["duration"] = idx
                    elif "gpa" in h or "voto" in h or "media" in h: mapping["gpa"] = idx
                    elif "scale" in h or "scala" in h: mapping["gpaScale"] = idx

                # Se mancano intestazioni chiare, usiamo l'ordine posizionale di default (Colonne A-G)
                if mapping["name"] == -1:
                    logger.info("Intestazioni Excel non riconosciute chiaramente, uso l'ordine posizionale predefinito (A: Nome, B: Corso, C: Paese, D: Qualifica, E: Durata, F: GPA, G: Scala)")
                    mapping = {
                        "name": 0, "course": 1, "country": 2,
                        "qualification": 3, "duration": 4, "gpa": 5, "gpaScale": 6
                    }

                # Scorre le righe a partire dalla seconda (salta l'header)
                for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    if not any(row):  # Salta righe completamente vuote
                        continue

                    try:
                        name_val = row[mapping["name"]] if mapping["name"] < len(row) else None
                        if not name_val:
                            continue  # Salta se manca il nome dello studente

                        student = {
                            "name": str(name_val).strip(),
                            "course": str(row[mapping["course"]]).strip() if mapping["course"] < len(row) and row[mapping["course"]] else "",
                            "country": str(row[mapping["country"]]).strip() if mapping["country"] < len(row) and row[mapping["country"]] else "",
                            "qualification": str(row[mapping["qualification"]]).strip() if mapping["qualification"] < len(row) and row[mapping["qualification"]] else "",
                            "duration": int(row[mapping["duration"]]) if mapping["duration"] < len(row) and row[mapping["duration"]] is not None else None,
                            "gpa": float(row[mapping["gpa"]]) if mapping["gpa"] < len(row) and row[mapping["gpa"]] is not None else 0.0,
                            "gpaScale": str(row[mapping["gpaScale"]]).strip() if mapping["gpaScale"] < len(row) and row[mapping["gpaScale"]] else ""
                        }
                        students_to_check.append(student)
                    except Exception as row_error:
                        logger.warning(f"Errore di lettura alla riga Excel {row_idx}: {str(row_error)}")
                        continue
            except Exception as e:
                return jsonify({"error": f"Errore nella lettura del file Excel: {str(e)}"}), 400
        else:
            return jsonify({"error": "Formato file non supportato. Carica solo file con estensione .json o .xlsx"}), 400

        if not students_to_check:
            return jsonify({"error": "Nessuno studente valido trovato nel file."}), 400

        # 3. ELABORAZIONE DI CIASCUN RECORD TRAMITE RAGIONATORE
        batch_results = []
        for student in students_to_check:
            try:
                name = student.get('name', 'StudenteBatch').replace(' ', '_')
                course = student.get('course')
                country = student.get('country')
                qualification_key = student.get('qualification')
                duration = student.get('duration')
                gpa = float(student.get('gpa', 0))
                gpa_scale = student.get('gpaScale')

                # Validazione minima dei campi necessari
                if not all([name, course, country, qualification_key]):
                    batch_results.append({
                        "name": name.replace('_', ' '),
                        "admitted": False,
                        "error": "Dati incompleti o non mappabili"
                    })
                    continue

                # Cerca la classe ontologica corrispondente alla qualifica
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
                    batch_results.append({
                        "name": name.replace('_', ' '),
                        "course": course,
                        "country": country,
                        "admitted": False,
                        "error": f"Qualifica '{qualification_key}' non valida per {country}/{course}"
                    })
                    continue

                if requires_duration and not duration:
                    batch_results.append({
                        "name": name.replace('_', ' '),
                        "course": course,
                        "country": country,
                        "admitted": False,
                        "error": "Durata corso mancante"
                    })
                    continue

                # Esegui il reasoning per il singolo studente
                admitted = create_individuals_and_check(
                    onto, name, country, course,
                    qual_class_name, duration, gpa, gpa_scale
                )

                batch_results.append({
                    "name": name.replace('_', ' '),
                    "course": course,
                    "country": country,
                    "qualification": qualification_key,
                    "admitted": admitted,
                    "status": "Ammesso" if admitted else "Non Ammesso"
                })

            except Exception as student_error:
                batch_results.append({
                    "name": student.get('name', 'Sconosciuto'),
                    "admitted": False,
                    "error": f"Errore interno di elaborazione: {str(student_error)}"
                })

        return jsonify({
            "status": "success",
            "total": len(batch_results),
            "results": batch_results
        }), 200

    except Exception as e:
        logger.error(f"Errore generale nell'elaborazione batch: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore interno del server: {str(e)}"}), 500


if __name__ == '__main__':
    logger.info("Avvio del backend Flask...")
    app.run(debug=True, host='0.0.0.0', port=5000)