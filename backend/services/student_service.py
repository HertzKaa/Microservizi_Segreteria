import os
import logging
import threading
from config import ADMISSION_THRESHOLDS, TTL_FILE_PATH

logger = logging.getLogger(__name__)

# Lock per garantire la scrittura thread-safe sul file unico
file_lock = threading.Lock()

def check_rejection_reason(country, course, qualification, duration, gpa, gpa_scale):
    """
    Analizza i dati dello studente rispetto alle soglie configurate e
    restituisce una stringa con la motivazione dettagliata dell'eventuale esclusione.
    """
    rules = ADMISSION_THRESHOLDS.get(country, {}).get(course, {})
    if not rules:
        return "Criteri formali non configurati per questo tipo di corso."

    # 1. Controllo dei titoli di studio abilitanti per il livello di corso
    eligible_quals = rules.get("eligible_qualifications", [])
    if eligible_quals and qualification not in eligible_quals:
        if country == "Iran" and course == "Undergraduate" and qualification == "DiplomMotevasete":
            return "Il titolo 'DiplomMotevasete' (11 anni di scolarità) non è sufficiente. In Italia sono richiesti almeno 12 anni (es. DiplomMotevasetePreUniversitary o il diploma post-2018/19)."
        return f"Il titolo '{qualification}' non è abilitante per l'accesso a un corso {course} per studenti provenienti da {country}."

    # 2. Controllo della media voti (GPA)
    min_gpa_rules = rules.get("min_gpa", {})
    if gpa_scale in min_gpa_rules:
        required_gpa = min_gpa_rules[gpa_scale]
        if gpa is not None and gpa < required_gpa:
            return f"Media voti (GPA) insufficiente: ottenuto {gpa}, richiesto minimo {required_gpa} ({gpa_scale})."

    # 3. Controllo della durata del titolo di studio
    min_dur_rules = rules.get("min_duration", {})
    if min_dur_rules:
        if isinstance(min_dur_rules, dict):
            required_dur = min_dur_rules.get(qualification)
        else:
            required_dur = min_dur_rules

        if required_dur is not None:
            if duration is not None and duration < required_dur:
                return f"Durata del titolo insufficiente per '{qualification}': inseriti {duration} anni, richiesto minimo {required_dur}."

    return "Requisiti formali superati, ma idoneità negata dal ragionatore logico (vincoli ontologici non soddisfatti)."


def append_student_to_ttl(name, course, country, qualification_title, duration, gpa, gpa_scale):
    """
    Genera le triple RDF in formato Turtle per il nuovo studente e le appende
    in modo thread-safe nel file di archivio condiviso sul server.
    """
    file_exists = os.path.exists(TTL_FILE_PATH)

    # Sanitizzazione URI (spazi -> underscore)
    student_uri = name.replace(' ', '_')
    course_uri = f"Course_{course.replace(' ', '_')}"
    cert_uri = f"Cert_{student_uri}"
    
    # Allineamento con il frontend (Magistrale -> PostgraduateCourse, altro -> UndergraduateCourse)
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

    # Generazione triple del Corso
    turtle_chunk += f":{course_uri} rdf:type owl:NamedIndividual ;\n"
    turtle_chunk += f"    rdf:type :{course_type} ;\n"
    turtle_chunk += f"    :courseName \"{course}\"^^xsd:string .\n"

    # Generazione triple della Qualifica (se presente)
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

    # Scrittura controllata con lock sul file fisico
    with file_lock:
        with open(TTL_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(turtle_chunk)
        logger.info(f"Studente '{name}' aggiunto con successo al file Turtle '{TTL_FILE_PATH}'.")
