import os
import logging
from datetime import datetime
from owlready2 import get_ontology, onto_path, sync_reasoner, destroy_entity
from config import ONTOLOGY_FILES

logger = logging.getLogger(__name__)

# Stato dell'ontologia
onto = None
onto_loaded = False

def load_ontology():
    """Carica l'ontologia OWL dal file locale"""
    global onto, onto_loaded
    
    ontology_file = None
    for file in ONTOLOGY_FILES:
        if os.path.exists(file):
            ontology_file = file
            break

    if not ontology_file:
        logger.error(f"File ontologia non trovato: {' o '.join(ONTOLOGY_FILES)}")
        raise FileNotFoundError(f"Impossibile trovare: {' o '.join(ONTOLOGY_FILES)}")

    logger.info(f"Caricamento ontologia da: {ontology_file}")

    # Configura il percorso
    if "." not in onto_path:
        onto_path.append(".")

    try:
        full_path = os.path.abspath(ontology_file)
        if os.name == 'nt':
            # Su Windows usiamo il percorso assoluto pulito
            file_url = full_path
        else:
            file_url = f"file://{full_path}"

        logger.info(f"Caricamento ontologia da: {full_path}")
        logger.info(f"URL file: {file_url}")

        onto = get_ontology(file_url).load()
        logger.info("Ontologia caricata con successo")

        try:
            num_classes = len(list(onto.classes()))
            logger.info(f"Ontologia contiene {num_classes} classi")
        except Exception as e:
            logger.warning(f"Impossibile contare le classi: {e}")

        onto_loaded = True
        return onto
    except Exception as e:
        logger.error(f"Errore nel caricamento dell'ontologia: {str(e)}", exc_info=True)
        raise

def get_current_ontology():
    """Restituisce l'ontologia correntemente caricata o tenta di caricarla"""
    global onto, onto_loaded
    if not onto_loaded or onto is None:
        load_ontology()
    return onto

def create_individuals_and_check(student_name, country, course,
                                 qual_class_name, duration, gpa, gpa_scale):
    """
    Crea gli individui temporanei, esegue il reasoner e verifica l'ammissione dello studente
    """
    current_onto = get_current_ontology()
    
    try:
        # Determinazione delle classi ontologiche
        student_class = "IranianStudent" if country == "Iran" else "IndianStudent"
        course_class = "PostgraduateCourse" if course == "Postgraduate" else "UndergraduateCourse"

        # Nomi unici per evitare collisioni in caso di richieste contemporanee
        student_individual_name = f"Student_{student_name}_{datetime.now().timestamp()}"
        course_individual_name = f"Course_{course}_{datetime.now().timestamp()}"
        qual_individual_name = f"Qualification_{student_name}_{datetime.now().timestamp()}"

        logger.info(f"Creazione individui: {student_individual_name}, {course_individual_name}, {qual_individual_name}")

        with current_onto:
            # 1. Crea l'individuo Course
            course_ind = current_onto[course_class](course_individual_name)
            logger.info(f"Corso creato: {course_individual_name} ({course_class})")

            # 2. Crea l'individuo Qualification
            qual_class = current_onto[qual_class_name]
            qual_ind = qual_class(qual_individual_name)
            logger.info(f"Qualifica creata: {qual_individual_name} ({qual_class_name})")

            # 3. Aggiungi proprietà alla qualifica (duration e GPA)
            if duration:
                qual_ind.hasDurationInYears = [float(duration)]
                logger.info(f"Durata impostata: {duration} anni")

            if gpa:
                gpa_property_name = f"hasGPA_{gpa_scale}"
                gpa_property = current_onto[gpa_property_name]
                gpa_property[qual_ind].append(float(gpa))
                logger.info(f"GPA impostato: {gpa} ({gpa_property_name})")

            # 4. Crea l'individuo Student
            student_class_onto = current_onto[student_class]
            student_ind = student_class_onto(student_individual_name)
            logger.info(f"Studente creato: {student_individual_name} ({student_class_onto.name})")

            # 5. Collega le relazioni
            student_ind.hasAppliedFor.append(course_ind)
            student_ind.hasQualification.append(qual_ind)
            logger.info(f"Relazioni collegate per lo studente {student_individual_name}")

            # 6. Sincronizza il reasoner (HermiT)
            logger.info("Esecuzione del reasoner...")
            sync_reasoner(infer_property_values=True)
            logger.info("Reasoner completato")

            # 7. Verifica l'ammissione attraverso le classi di eligibilità dedotte
            eligibility_classes = [
                "EligibleIndianUndergraduateStudent",
                "EligibleIndianPostgraduateStudent",
                "EligibleIranianUndergraduateStudent",
                "EligibleIranianPostgraduateStudent"
            ]

            admitted = False
            for elig_class_name in eligibility_classes:
                elig_class = current_onto[elig_class_name]
                if student_ind in elig_class.instances():
                    admitted = True
                    logger.info(f"Studente ammesso in classe: {elig_class_name}")
                    break

            if not admitted:
                logger.info("Studente NON ammesso in alcuna classe di eligibilità logica")

            # 8. Pulisci l'ontologia eliminando gli individui temporanei
            logger.info("Eliminazione degli individui temporanei...")
            destroy_entity(student_ind)
            destroy_entity(course_ind)
            destroy_entity(qual_ind)

            # Rinsincronizza dopo la distruzione delle entità temporanee
            sync_reasoner(infer_property_values=True)
            logger.info("Pulizia completata e ontologia sincronizzata")

            return admitted

    except Exception as e:
        logger.error(f"Errore durante la creazione e il controllo degli individui: {str(e)}", exc_info=True)
        raise


def check_admission_batch_ontology(students_to_reason):
    """
    Esegue la verifica ontologica in batch per una lista di studenti.
    students_to_reason è una lista di dizionari con i campi:
      - 'index': indice originale del record
      - 'name': nome dello studente (sanitizzato con underscore)
      - 'country': 'India' o 'Iran'
      - 'course': 'Undergraduate' o 'Postgraduate'
      - 'qual_class_name': nome della classe di qualifica ontologica
      - 'duration': durata (intero o None)
      - 'gpa': gpa (float)
      - 'gpa_scale': scala gpa (stringa)
    Ritorna un dizionario che mappa l'indice dello studente all'esito booleano di ammissione.
    """
    if not students_to_reason:
        return {}

    current_onto = get_current_ontology()
    results = {}
    created_entities = []

    try:
        timestamp = datetime.now().timestamp()
        
        with current_onto:
            for idx, student in enumerate(students_to_reason):
                name = student['name']
                country = student['country']
                course = student['course']
                qual_class_name = student['qual_class_name']
                duration = student['duration']
                gpa = student['gpa']
                gpa_scale = student['gpa_scale']
                original_index = student['index']

                student_class = "IranianStudent" if country == "Iran" else "IndianStudent"
                course_class = "PostgraduateCourse" if course == "Postgraduate" else "UndergraduateCourse"

                student_individual_name = f"Student_{name}_{timestamp}_{idx}"
                course_individual_name = f"Course_{course}_{timestamp}_{idx}"
                qual_individual_name = f"Qualification_{name}_{timestamp}_{idx}"

                # 1. Crea l'individuo Course
                course_ind = current_onto[course_class](course_individual_name)
                # 2. Crea l'individuo Qualification
                qual_class = current_onto[qual_class_name]
                qual_ind = qual_class(qual_individual_name)

                # 3. Aggiungi proprietà alla qualifica
                if duration:
                    qual_ind.hasDurationInYears = [float(duration)]
                if gpa:
                    gpa_property_name = f"hasGPA_{gpa_scale}"
                    gpa_property = current_onto[gpa_property_name]
                    gpa_property[qual_ind].append(float(gpa))

                # 4. Crea l'individuo Student
                student_class_onto = current_onto[student_class]
                student_ind = student_class_onto(student_individual_name)

                # 5. Collega le relazioni
                student_ind.hasAppliedFor.append(course_ind)
                student_ind.hasQualification.append(qual_ind)

                # Memorizza i riferimenti per la verifica e la pulizia
                created_entities.append({
                    'index': original_index,
                    'student_ind': student_ind,
                    'course_ind': course_ind,
                    'qual_ind': qual_ind
                })

            # 6. Sincronizza il reasoner una sola volta per tutti gli studenti
            logger.info(f"Esecuzione batch del reasoner per {len(students_to_reason)} studenti...")
            sync_reasoner(infer_property_values=True)
            logger.info("Reasoner batch completato")

            # 7. Verifica l'ammissione per ciascuno
            eligibility_classes = [
                "EligibleIndianUndergraduateStudent",
                "EligibleIndianPostgraduateStudent",
                "EligibleIranianUndergraduateStudent",
                "EligibleIranianPostgraduateStudent"
            ]

            for entity in created_entities:
                admitted = False
                student_ind = entity['student_ind']
                for elig_class_name in eligibility_classes:
                    elig_class = current_onto[elig_class_name]
                    if student_ind in elig_class.instances():
                        admitted = True
                        break
                results[entity['index']] = admitted

            # 8. Pulisci l'ontologia eliminando tutti gli individui temporanei
            logger.info("Eliminazione in batch degli individui temporanei...")
            for entity in created_entities:
                destroy_entity(entity['student_ind'])
                destroy_entity(entity['course_ind'])
                destroy_entity(entity['qual_ind'])

            # Rinsincronizza dopo la distruzione delle entità per mantenere l'ontologia pulita
            sync_reasoner(infer_property_values=True)
            logger.info("Pulizia batch completata e ontologia sincronizzata")

        return results

    except Exception as e:
        logger.error(f"Errore durante la verifica ontologica in batch: {str(e)}", exc_info=True)
        # Assicuriamoci di pulire in ogni caso se abbiamo creato qualcosa
        try:
            with current_onto:
                for entity in created_entities:
                    try: destroy_entity(entity['student_ind'])
                    except: pass
                    try: destroy_entity(entity['course_ind'])
                    except: pass
                    try: destroy_entity(entity['qual_ind'])
                    except: pass
                sync_reasoner(infer_property_values=True)
        except Exception as cleanup_error:
            logger.error(f"Errore durante la pulizia di emergenza in batch: {str(cleanup_error)}")
        raise

