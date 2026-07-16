import os

# Configurazione del percorso in cui viene salvato l'elenco degli studenti registrati in formato Turtle (.ttl)
TTL_FILE_PATH = "students_registered.ttl"

# Percorsi dei file dell'ontologia (cercati in sequenza)
ONTOLOGY_FILES = ["../ontology/Protege0-.rdf", "../ontology/Protege0-.ttl"]

# Mapping dei titoli di studio per paese e tipologia di corso (con flag di obbligatorietà durata)
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

# Soglie minime (Thresholds) di ammissione codificate per Paese e Livello
# (Allineate meticolosamente con le classi di idoneità logica in Protégé)
ADMISSION_THRESHOLDS = {
    "India": {
        "Undergraduate": {
            "eligible_qualifications": ["AllIndiaSeniorSchool", "IndianSchoolCert", "IntermediateExam", "HigherSecondarySchool", "HigherSecondaryPartII"],
            "min_gpa": {
                "Base100": 50.0  # Voto minimo per diplomati indiani
            }
        },
        "Postgraduate": {
            "eligible_qualifications": ["HonoursBachelor", "ProfessionalBachelor", "PassGeneralBachelor", "MasterDegree", "PostgraduateBachelor"],
            "min_duration": {
                "HonoursBachelor": 3,
                "ProfessionalBachelor": 4,      # Un Professional Bachelor richiede almeno 4 anni
                "PassGeneralBachelor": 3,
                "PostgraduateBachelor": 1,
                "MasterDegree": 1
            },
            "min_gpa": {
                "Base100": 60.0,
                "Base10": 6.0,
                "Base8": 5.0,
                "Base4": 2.5
            }
        }
    },
    "Iran": {
        "Undergraduate": {
            # DiplomMotevasete (11 anni) non è ammesso alla triennale se non integrato con Kardani o Pish-Daneshgahi
            "eligible_qualifications": ["SecondaryEdu2018", "Kardani"],
            "min_gpa": {
                "Base20": 10.0  # Voto minimo su 20 in Iran per l'undergraduate
            }
        },
        "Postgraduate": {
            "eligible_qualifications": ["Karshenasi", "KarshenasiNapayvasteh"],
            "min_duration": {
                "Karshenasi": 4,
                "KarshenasiNapayvasteh": 2     # Karshenasi Napayvasteh richiede minimo 2 anni
            },
            "min_gpa": {
                "Base20": 12.0                  # Voto minimo su 20 in Iran per l'ammissione magistrale
            }
        }
    }
}
