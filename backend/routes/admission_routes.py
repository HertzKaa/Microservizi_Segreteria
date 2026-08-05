from flask import Blueprint, request, jsonify, send_file
import os
import json
import logging
from rdflib import Graph, URIRef
from config import TTL_FILE_PATH
from services.ontology_service import get_current_ontology, create_individuals_and_check, check_admission_batch_ontology
from services.student_service import check_rejection_reason, append_student_to_ttl, file_lock
from services.ml_service import evaluate_ml_admission
from services.requirements_service import get_qualifications_map_dynamic, get_admission_thresholds_dynamic, load_requirements, save_requirements

# Tentativo di importare openpyxl per il caricamento massivo tramite file Excel

try:
    import openpyxl
except ImportError:
    openpyxl = None

logger = logging.getLogger(__name__)

# Definizione del Blueprint
admission_bp = Blueprint('admission', __name__)

@admission_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint di health check"""
    return jsonify({"status": "ok", "message": "Backend is running"}), 200

@admission_bp.route('/check-admission', methods=['POST'])
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

        reqs = load_requirements()
        if country not in reqs:
            return jsonify({"admitted": False, "error": "Paese non valido"}), 400

        logger.info(f"Elaborazione: {name} - {country} - {course} - {qualification_key}")

        # Determina la classe di qualifica
        found_qual = False
        qual_class_name = None
        requires_duration = False

        qualifications_map = get_qualifications_map_dynamic()
        if country in qualifications_map and course in qualifications_map[country]:
            for key, class_name, requires_dur in qualifications_map[country][course]:
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

        # Controllo in memoria bloccante (GPA, Durata, Qualifica)
        rejection_reason = check_rejection_reason(country, course, qualification_key, duration, gpa, gpa_scale)
        is_rejected_in_memory = not rejection_reason.startswith("Requisiti formali superati")

        if is_rejected_in_memory:
            ontology_admitted = False
            logger.info(f"Studente {name} rifiutato per controlli in memoria: {rejection_reason}. Ammissione ontologica saltata.")
        else:
            # Crea gli individui nell'ontologia e controlla l'ammissione formale
            ontology_admitted = create_individuals_and_check(
                name, country, course,
                qual_class_name, duration, gpa, gpa_scale
            )

        logger.info(f"Risultato ammissione ontologica per {name}: {ontology_admitted}")

        # Valutazione ML per candidati provenienti da Iran e India
        ml_result = None
        if country in ["India", "Iran"]:
            birth_year = data.get('birthYear')
            age = data.get('age')
            gender = data.get('gender', 'M')
            ml_result = evaluate_ml_admission(
                country=country,
                course=course,
                birth_year=birth_year,
                age=age,
                gpa=gpa,
                gpa_scale=gpa_scale,
                gender=gender
            )
            logger.info(f"Risultato modello ML per {country}: {ml_result}")

        # Decisione finale: per Iran ed India è AMMESSO solo se sia i requisiti ontologici formali sia il modello ML danno esito positivo
        final_admitted = bool(ontology_admitted)
        if ml_result and ml_result.get('evaluatable'):
            final_admitted = bool(ontology_admitted) and bool(ml_result.get('admitted'))

        # Calcola il motivo dell'esclusione se non ammesso
        explanation = None
        if is_rejected_in_memory:
            explanation = rejection_reason
        elif not ontology_admitted:
            explanation = check_rejection_reason(country, course, qualification_key, duration, gpa, gpa_scale)
        elif ml_result and ml_result.get('evaluatable') and not ml_result.get('admitted'):
            explanation = ml_result.get('explanation')
        elif final_admitted:
            explanation = "Candidato idoneo sia secondo i vincoli ontologici che il modello decisionale Machine Learning."

        has_age_warning = bool(ml_result.get('has_age_warning', False)) if ml_result else False
        age_warning_message = ml_result.get('age_warning_message', '') if ml_result else ''

        return jsonify({
            "admitted": bool(final_admitted),
            "ontology_admitted": bool(ontology_admitted),
            "ml_evaluation": ml_result,
            "has_age_warning": has_age_warning,
            "age_warning_message": age_warning_message,
            "student": name,
            "country": country,
            "course": course,
            "explanation": explanation
        }), 200

    except Exception as e:
        logger.error(f"Errore durante l'elaborazione: {str(e)}", exc_info=True)
        return jsonify({
            "admitted": False,
            "error": f"Errore del server: {str(e)}"
        }), 500

@admission_bp.route('/qualifications', methods=['GET'])
def get_qualifications():
    """Endpoint per ottenere le qualifiche disponibili per un paese/corso"""
    country = request.args.get('country')
    course = request.args.get('course')

    qualifications_map = get_qualifications_map_dynamic()
    if country not in qualifications_map or course not in qualifications_map[country]:
        return jsonify({"qualifications": []}), 400

    quals = qualifications_map[country][course]
    return jsonify({
        "qualifications": [
            {"key": key, "label": label, "requiresDuration": requires_duration}
            for key, label, requires_duration in quals
        ]
    }), 200

@admission_bp.route('/gpa-scales', methods=['GET'])
def get_gpa_scales():
    """Endpoint per ottenere le scale GPA disponibili per un paese"""
    country = request.args.get('country')

    reqs = load_requirements()
    if country not in reqs:
        return jsonify({"scales": []}), 400

    scales = reqs[country].get("gpa_scales", [])
    # Formatta le scale con il campo 'label' basato sull'italiano di base o il client
    formatted_scales = []
    for s in scales:
        formatted_scales.append({
            "value": s["value"],
            "label": s.get("label_it", s.get("label", s["value"]))
        })
    return jsonify({"scales": formatted_scales}), 200

@admission_bp.route('/register-student', methods=['POST'])
def register_student():
    """
    Endpoint per registrare uno studente e appenderlo nel file Turtle (.ttl) sul server
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

        append_student_to_ttl(
            name, course, country, qualification_title, duration, gpa, gpa_scale
        )

        return jsonify({
            "status": "success",
            "message": f"Studente '{name}' salvato con successo sul server nel file unico!"
        }), 200

    except Exception as e:
        logger.error(f"Errore durante il salvataggio: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": f"Errore interno del server: {str(e)}"}), 500

@admission_bp.route('/download-registered-ttl', methods=['GET'])
def download_registered_ttl():
    """
    Endpoint per scaricare il file unico degli studenti registrati sul server
    """
    if not os.path.exists(TTL_FILE_PATH):
        return jsonify({"status": "error", "message": "Nessuno studente salvato sul server al momento."}), 404

    # Utilizziamo il percorso assoluto per evitare problemi con Flask send_file
    abs_path = os.path.abspath(TTL_FILE_PATH)
    return send_file(abs_path, as_attachment=True, download_name="students_registered.ttl")

@admission_bp.route('/clear-registered-ttl', methods=['POST'])
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

@admission_bp.route('/check-admission-batch', methods=['POST'])
def check_admission_batch():
    """
    Endpoint per il caricamento massivo e la verifica in batch di studenti (JSON, Excel o Turtle)
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
                if isinstance(students_to_check, dict):
                    students_to_check = [students_to_check]
            except Exception as e:
                return jsonify({"error": f"Errore di parsing JSON: {str(e)}"}), 400

        # 2. PARSING FILE EXCEL (.xlsx, .xls)
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            try:
                import pandas as pd
            except ImportError:
                return jsonify({"error": "Libreria pandas non installata sul server."}), 500

            try:
                df = pd.read_excel(file)
                headers = [str(col).strip().lower() for col in df.columns]

                # Associazione flessibile delle colonne basata sul nome della colonna
                mapping = {
                    "name": -1, "course": -1, "country": -1,
                    "qualification": -1, "duration": -1, "gpa": -1, "gpaScale": -1
                }

                # Ordine invertito: controlliamo "scale" prima di "gpa" per evitare conflitti di sottostringhe
                for idx, h in enumerate(headers):
                    if "name" in h or "nome" in h: mapping["name"] = idx
                    elif "course" in h or "corso" in h: mapping["course"] = idx
                    elif "country" in h or "paese" in h: mapping["country"] = idx
                    elif "qualification" in h or "titolo" in h: mapping["qualification"] = idx
                    elif "duration" in h or "durata" in h: mapping["duration"] = idx
                    elif "scale" in h or "scala" in h or "gpascale" in h: mapping["gpaScale"] = idx
                    elif "gpa" in h or "voto" in h or "media" in h: mapping["gpa"] = idx

                # Se mancano intestazioni chiare, usiamo l'ordine posizionale di default (Colonne A-G)
                if mapping["name"] == -1:
                    logger.info("Intestazioni Excel non riconosciute chiaramente, uso l'ordine posizionale predefinito (A: Nome, B: Corso, C: Paese, D: Qualifica, E: Durata, F: GPA, G: Scala)")
                    mapping = {
                        "name": 0, "course": 1, "country": 2,
                        "qualification": 3, "duration": 4, "gpa": 5, "gpaScale": 6
                    }

                # Iterazione efficiente
                for row_tuple in df.itertuples(index=True):
                    row = list(row_tuple)[1:]
                    if not any(pd.notna(val) for val in row):  # Salta righe completamente vuote
                        continue

                    try:
                        name_val = row[mapping["name"]] if mapping["name"] < len(row) else None
                        if pd.isna(name_val) or str(name_val).strip() == "" or str(name_val).lower() == "nan":
                            continue

                        def clean_str(val):
                            if pd.isna(val) or val is None:
                                return ""
                            s = str(val).strip()
                            if s.lower() == "nan":
                                return ""
                            return s

                        course_val = clean_str(row[mapping["course"]])
                        country_val = clean_str(row[mapping["country"]])
                        qualification_val = clean_str(row[mapping["qualification"]])

                        # Parsing sicuro di Duration (tollera celle vuote o stringhe vuote)
                        duration_val = row[mapping["duration"]] if mapping["duration"] < len(row) else None
                        duration_int = None
                        if pd.notna(duration_val) and str(duration_val).strip() != "" and str(duration_val).lower() != "nan":
                            try:
                                duration_int = int(float(duration_val))
                            except (ValueError, TypeError):
                                duration_int = None

                        # Parsing sicuro di GPA (tollera formati diversi)
                        gpa_val = row[mapping["gpa"]] if mapping["gpa"] < len(row) else None
                        gpa_float = 0.0
                        if pd.notna(gpa_val) and str(gpa_val).strip() != "" and str(gpa_val).lower() != "nan":
                            try:
                                gpa_float = float(gpa_val)
                            except (ValueError, TypeError):
                                gpa_float = 0.0

                        # Parsing sicuro di GPAScale
                        gpa_scale_val = clean_str(row[mapping["gpaScale"]])

                        student = {
                            "name": str(name_val).strip(),
                            "course": course_val,
                            "country": country_val,
                            "qualification": qualification_val,
                            "duration": duration_int,
                            "gpa": gpa_float,
                            "gpaScale": gpa_scale_val
                        }
                        students_to_check.append(student)
                    except Exception as row_error:
                        logger.warning(f"Errore di lettura alla riga Excel: {str(row_error)}")
                        continue
            except Exception as e:
                logger.error(f"Errore nella lettura del file Excel con pandas: {str(e)}", exc_info=True)
                return jsonify({"error": f"Errore nella lettura del file Excel: {str(e)}"}), 400

        # 3. PARSING FILE TURTLE (.ttl)
        elif filename.endswith('.ttl'):
            try:
                file_content = file.read().decode('utf-8')
                g = Graph()
                g.parse(data=file_content, format="turtle")

                # Query SPARQL per estrarre gli studenti e le loro relazioni dal file TTL
                sparql_query = """
                PREFIX : <http://example.org/university-admission#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                
                SELECT ?student ?studentClass ?courseType ?qualType ?duration ?gpaProp ?gpa
                WHERE {
                    ?student rdf:type ?studentClass .
                    FILTER (?studentClass IN (:IndianStudent, :IranianStudent))
                    
                    ?student :hasAppliedFor ?course .
                    ?course rdf:type ?courseType .
                    FILTER (?courseType IN (:UndergraduateCourse, :PostgraduateCourse))
                    
                    OPTIONAL {
                        ?student :hasQualification ?cert .
                        ?cert rdf:type ?qualType .
                        FILTER (?qualType != owl:NamedIndividual)
                        
                        OPTIONAL { ?cert :hasDurationInYears ?duration . }
                        OPTIONAL {
                            ?cert ?gpaProp ?gpa .
                            FILTER (STRSTARTS(STR(?gpaProp), "http://example.org/university-admission#hasGPA_"))
                        }
                    }
                }
                """

                qres = g.query(sparql_query)
                for row in qres:
                    student_uri = str(row[0])
                    student_class_uri = str(row[1])
                    course_type_uri = str(row[2])
                    qual_type_uri = str(row[3]) if row[3] is not None else None
                    duration_val = row[4]
                    gpa_prop_uri = str(row[5]) if row[5] is not None else None
                    gpa_val = row[6]

                    # Estrazione dei nomi locali dall'URI completo (tutto ciò che segue il carattere '#')
                    student_name = student_uri.split("#")[-1].replace("_", " ")
                    country = "India" if student_class_uri.split("#")[-1] == "IndianStudent" else "Iran"
                    course = "Postgraduate" if course_type_uri.split("#")[-1] == "PostgraduateCourse" else "Undergraduate"

                    # Mappatura della classe OWL della qualifica nella stringa attesa dal backend
                    qualification_key = "NoCertificate"
                    if qual_type_uri:
                        local_qual_name = qual_type_uri.split("#")[-1]
                        # Ricerchiamo la chiave corrispondente nel nostro qualifications_map
                        qualifications_map = get_qualifications_map_dynamic()
                        for country_name, courses in qualifications_map.items():
                            for course_name, quals in courses.items():
                                for key, class_name, _ in quals:
                                    if class_name == local_qual_name:
                                        qualification_key = key
                                        break
                        if qualification_key == "NoCertificate":
                            qualification_key = local_qual_name

                    # Estrazione della scala del GPA dalla proprietà RDF (es. :hasGPA_Base100 -> Base100)
                    gpa_scale = ""
                    if gpa_prop_uri:
                        gpa_scale = gpa_prop_uri.split("#")[-1].replace("hasGPA_", "")

                    student_dict = {
                        "name": student_name,
                        "course": course,
                        "country": country,
                        "qualification": qualification_key,
                        "duration": int(duration_val) if duration_val is not None else None,
                        "gpa": float(gpa_val) if gpa_val is not None else 0.0,
                        "gpaScale": gpa_scale
                    }
                    students_to_check.append(student_dict)

            except Exception as e:
                logger.error(f"Errore di parsing del file Turtle: {str(e)}", exc_info=True)
                return jsonify({"error": f"Errore nel parsing del file Turtle (.ttl): {str(e)}"}), 400
        else:
            return jsonify({"error": "Formato file non supportato. Carica solo file .json, .xlsx o .ttl"}), 400

        if not students_to_check:
            return jsonify({"error": "Nessuno studente valido trovato nel file."}), 400

        # 4. ELABORAZIONE DI CIASCUN RECORD
        batch_results = []
        students_to_reason = []

        for student in students_to_check:
            try:
                name = student.get('name', 'StudenteBatch').replace(' ', '_')
                course = student.get('course')
                country = student.get('country')
                qualification_key = student.get('qualification')
                duration = student.get('duration')
                gpa = float(student.get('gpa', 0))
                gpa_scale = student.get('gpaScale')

                if not all([name, course, country, qualification_key]):
                    batch_results.append({
                        "name": name.replace('_', ' '),
                        "admitted": False,
                        "error": "Dati incompleti o non mappabili"
                    })
                    continue

                found_qual = False
                qual_class_name = None
                requires_duration = False

                qualifications_map = get_qualifications_map_dynamic()
                if country in qualifications_map and course in qualifications_map[country]:
                    for key, class_name, requires_dur in qualifications_map[country][course]:
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

                # Controllo in memoria bloccante (GPA, Durata, Qualifica)
                rejection_reason = check_rejection_reason(country, course, qualification_key, duration, gpa, gpa_scale)
                is_rejected_in_memory = not rejection_reason.startswith("Requisiti formali superati")

                if is_rejected_in_memory:
                    batch_results.append({
                        "name": name.replace('_', ' '),
                        "course": course,
                        "country": country,
                        "qualification": qualification_key,
                        "admitted": False,
                        "status": "Non Ammesso",
                        "error": rejection_reason
                    })
                else:
                    # Aggiunge alla lista per il ragionamento in batch
                    students_to_reason.append({
                        "index": len(batch_results),
                        "name": name,
                        "country": country,
                        "course": course,
                        "qual_class_name": qual_class_name,
                        "duration": duration,
                        "gpa": gpa,
                        "gpa_scale": gpa_scale
                    })
                    # Placeholder temporaneo nei risultati
                    batch_results.append({
                        "name": name.replace('_', ' '),
                        "course": course,
                        "country": country,
                        "qualification": qualification_key,
                        "admitted": False,
                        "status": "Non Ammesso",
                        "error": None
                    })

            except Exception as student_error:
                batch_results.append({
                    "name": student.get('name', 'Sconosciuto'),
                    "admitted": False,
                    "error": f"Errore interno di lavoro: {str(student_error)}"
                })

        # Eseguiamo il ragionamento in batch per gli studenti che hanno superato i controlli preliminari
        if students_to_reason:
            try:
                reason_results = check_admission_batch_ontology(students_to_reason)
                for original_idx, admitted in reason_results.items():
                    batch_results[original_idx]["admitted"] = admitted
                    batch_results[original_idx]["status"] = "Ammesso" if admitted else "Non Ammesso"
                    if not admitted:
                        batch_results[original_idx]["error"] = "Requisiti formali superati, ma idoneità negata dal ragionatore logico (vincoli ontologici non soddisfatti)."
            except Exception as reason_error:
                logger.error(f"Errore durante il ragionamento in batch: {str(reason_error)}")
                for s in students_to_reason:
                    original_idx = s["index"]
                    batch_results[original_idx]["error"] = f"Errore durante la verifica ontologica: {str(reason_error)}"

        return jsonify({
            "status": "success",
            "total": len(batch_results),
            "results": batch_results
        }), 200

    except Exception as e:
        logger.error(f"Errore generale nell'elaborazione batch: {str(e)}", exc_info=True)
        return jsonify({"error": f"Errore interno del server: {str(e)}"}), 500

@admission_bp.route('/delete-students', methods=['POST'])
def delete_students():
    """
    Rimuove selettivamente solo gli studenti specificati (quelli della sessione corrente)
    dal file Turtle unico sul server senza toccare gli altri.
    """
    try:
        data = request.get_json()
        student_names = data.get('names', []) # Riceve la lista dei nomi da cancellare

        if not student_names:
            return jsonify({"status": "success", "message": "Nessuno studente da eliminare."}), 200

        if not os.path.exists(TTL_FILE_PATH):
            return jsonify({"status": "error", "message": "Nessun archivio studenti trovato sul server."}), 404

        with file_lock:
            # Carica il file di registro corrente come grafo RDF
            g = Graph()
            g.parse(TTL_FILE_PATH, format="turtle")

            for name in student_names:
                # Ricostruisce gli URI degli individui usati nel file Turtle
                student_uri = name.strip().replace(' ', '_')
                student_ref = URIRef(f"http://example.org/university-admission#{student_uri}")
                cert_ref = URIRef(f"http://example.org/university-admission#Cert_{student_uri}")

                # Rimuove dal grafo tutte le triple che descrivono lo studente e la sua qualifica
                g.remove((student_ref, None, None))
                g.remove((cert_ref, None, None))

            # Salva nuovamente il file senza le triple rimosse
            g.serialize(destination=TTL_FILE_PATH, format="turtle")

        logger.info(f"Rimosso/i dal server solo lo/gli studente/i della sessione: {student_names}")
        return jsonify({
            "status": "success",
            "message": "Studenti inseriti in questa sessione rimossi con successo dal server!"
        }), 200

    except Exception as e:
        logger.error(f"Errore durante la rimozione mirata: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": f"Errore sul server: {str(e)}"}), 500

@admission_bp.route('/api/requirements', methods=['GET'])
def get_requirements():
    """Restituisce la struttura JSON con tutte le nazioni configurate e le relative soglie"""
    try:
        reqs = load_requirements(force_reload=True)
        return jsonify(reqs), 200
    except Exception as e:
        logger.error(f"Errore recupero requisiti: {e}")
        return jsonify({"error": str(e)}), 500

@admission_bp.route('/api/requirements', methods=['POST'])
def add_requirement():
    """Aggiunge una nuova nazione con i suoi parametri standardizzati"""
    try:
        data = request.get_json()
        country_name = data.get('country')
        
        if not country_name:
            return jsonify({"error": "Nome nazione mancante"}), 400
            
        reqs = load_requirements()
        if country_name in reqs:
            return jsonify({"error": f"Nazione {country_name} gia esistente"}), 400
            
        # Struttura standard
        reqs[country_name] = {
            "country_code": data.get('country_code', 'XX'),
            "gpa_scales": data.get('gpa_scales', []),
            "qualifications": data.get('qualifications', {"Undergraduate": [], "Postgraduate": []}),
            "thresholds": data.get('thresholds', {
                "Undergraduate": {"eligible_qualifications": [], "min_gpa": {}},
                "Postgraduate": {"eligible_qualifications": [], "min_duration": {}, "min_gpa": {}}
            })
        }
        
        if save_requirements(reqs):
            return jsonify({"message": f"Nazione {country_name} aggiunta con successo", "requirements": reqs[country_name]}), 200
        else:
            return jsonify({"error": "Impossibile salvare i requisiti"}), 500
    except Exception as e:
        logger.error(f"Errore aggiunta requisiti: {e}")
        return jsonify({"error": str(e)}), 500

@admission_bp.route('/api/requirements/<country>', methods=['PUT'])
def update_requirement(country):
    """Aggiorna le soglie/requisiti di una nazione esistente"""
    try:
        data = request.get_json()
        reqs = load_requirements()
        
        if country not in reqs:
            return jsonify({"error": f"Nazione {country} non trovata"}), 404
            
        # Aggiorna i campi passati
        if 'country_code' in data:
            reqs[country]['country_code'] = data['country_code']
        if 'gpa_scales' in data:
            reqs[country]['gpa_scales'] = data['gpa_scales']
        if 'qualifications' in data:
            reqs[country]['qualifications'] = data['qualifications']
        if 'thresholds' in data:
            reqs[country]['thresholds'] = data['thresholds']
            
        if save_requirements(reqs):
            return jsonify({"message": f"Nazione {country} aggiornata con successo", "requirements": reqs[country]}), 200
        else:
            return jsonify({"error": "Impossibile salvare i requisiti"}), 500
    except Exception as e:
        logger.error(f"Errore aggiornamento requisiti per {country}: {e}")
        return jsonify({"error": str(e)}), 500

@admission_bp.route('/api/requirements/<country>', methods=['DELETE'])
def delete_requirement(country):
    """Elimina una nazione e le sue configurazioni di requisiti"""
    try:
        reqs = load_requirements()
        if country not in reqs:
            return jsonify({"error": f"Nazione {country} non trovata"}), 404
            
        del reqs[country]
        if save_requirements(reqs):
            return jsonify({"message": f"Nazione {country} eliminata con successo"}), 200
        else:
            return jsonify({"error": "Impossibile salvare i requisiti"}), 500
    except Exception as e:
        logger.error(f"Errore eliminazione nazione {country}: {e}")
        return jsonify({"error": str(e)}), 500
