# AI & Semantic Web Platform: International Student Admission Verification

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-black.svg?logo=flask)](https://flask.palletsprojects.com/)
[![owlready2](https://img.shields.io/badge/owlready2-0.46-orange.svg)](https://owlready2.readthedocs.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-F7931E.svg?logo=scikit-learn)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-Academic-green.svg)](#)

Sistema integrato full-stack per l'automatizzazione, la verifica formale e la predizione dell'ammissibilità di studenti internazionali a corsi di laurea Triennale (Undergraduate) e Magistrale (Postgraduate). 

Il progetto coniuga **Ingegneria della Conoscenza (Web Semantico / Ontologie OWL con Ragionamento Logico)** e **Machine Learning Supervisionato (Modelli Ensemble)**, affiancati da una dashboard interattiva con gestione dinamica dei requisiti accademici ministeriali per oltre 30 paesi.

---

## 📌 Executive Summary per HR & Valutatori Tecnici

* **Problema:** La valutazione dei titoli di studio internazionali per l'accesso universitario richiede l'analisi complessa di sistemi educativi eterogenei, scale di voto (GPA) difformi, vincoli di scolarità minima (almeno 12 anni per le triennali italiane) e accordi bilaterali.
* **Soluzione Adottata:** Architettura a doppio livello decisionale:
  1. **Livello Deterministico Formale (Ontologia OWL + HermiT Reasoner):** Modella i requisiti formali, le classi di equivalenza e le regole di ammissibilità mediante inferenza deduttiva su grafi di conoscenza.
  2. **Livello Predittivo Accademico (Machine Learning):** Analizza la competitività storica della domanda ponderando votazione normalizzata (Z-Score) ed età relativa rispetto al ciclo accademico.
* **Amministrazione & Scalabilità:** Supporto al caricamento massivo (batch) via file Excel, JSON o serializzazioni Turtle (`.ttl`), esportazione certificata in CSV e pannello di configurazione live dei requisiti minimi di accesso.

---

## 🛠️ Stack Tecnologico

| Ambito | Tecnologie e Librerie | Ruolo nel Progetto |
| :--- | :--- | :--- |
| **Backend** | Python, Flask, Flask-CORS, Werkzeug | REST API, orchestration microservizi, threading lock |
| **Web Semantico** | Protégé, OWL, RDF/XML, Turtle, `owlready2`, `rdflib` | Modellazione ontologica, inferenza con ragionatore logico HermiT |
| **Machine Learning** | `scikit-learn`, `joblib`, `pandas`, `numpy` | Feature engineering, Z-Score normalization, Random Forest & Decision Tree |
| **Data Processing** | `pdfplumber`, `openpyxl`, `pandas` | Estrazione e parsing requisiti da PDF ministeriali, ingestione Excel/CSV |
| **Frontend** | HTML5, CSS Moderno (CSS Custom Properties), Vanilla JS, Flatpickr | UI reattiva, internazionalizzazione (IT/EN), gestione batch e filtri real-time |

---

## 🏛️ Architettura del Sistema

```text
                       ┌─────────────────────────────────────┐
                       │           Web UI Client             │
                       │  (Portal Single Form / Batch View)  │
                       └──────────────────┬──────────────────┘
                                          │ HTTP / JSON / Multipart
                                          ▼
                       ┌─────────────────────────────────────┐
                       │          Flask REST API             │
                       │   (/check-admission, /batch, etc.)  │
                       └──────────┬────────────────┬─────────┘
                                  │                │
            ┌─────────────────────┴──────┐         └────────────────────┐
            ▼                            ▼                              ▼
 ┌──────────────────────┐    ┌──────────────────────┐       ┌──────────────────────┐
 │   Memoria & Criteri  │    │    Ontology Engine   │       │      ML Service      │
 │  (JSON Requirements) │    │  (owlready2 + HermiT)│       │  (Random Forest Clf) │
 └──────────┬───────────┘    └──────────┬───────────┘       └──────────┬───────────┘
            │                           │                              │
            │   Validazione preliminare │   Inferenza logica formale   │   Score di idoneità
            ▼   e durata minima         ▼   sulle classi dedotte       ▼   e scostamento età
       [Fast Reject]             [EligibleStudent Class]          [Academic Probability]
            │                           │                              │
            └───────────────────────────┼──────────────────────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │      Verdetto Integrato     │
                         │   (Ammesso / Non Ammesso +  │
                         │    Spiegazione Dettagliata) │
                         └─────────────────────────────┘
```

---

## 💡 Funzionalità Chiave

### 1. Verifica Ontologica con Ragionatore Logico
* Definizione di individui, proprietà di dato (`hasDurationInYears`, `hasGPA_Base100`, `hasGPA_Base20`, ecc.) e proprietà oggetto (`hasAppliedFor`, `hasQualification`).
* Esecuzione a runtime del **reasoner HermiT** per classificare dinamicamente il candidato nelle classi inferite (es. `EligibleIndianPostgraduateStudent`, `EligibleIranianUndergraduateStudent`).
* Pulizia automatica (`destroy_entity`) post-ragionamento per garantire l'idempotenza e prevenire memory leak o inquinamento del grafo RDF condiviso.

### 2. Pipeline Machine Learning (Studenti India & Iran)
* **Feature Engineering:** Calcolo dello scostamento dell'età rispetto alla media del corso (`ETA_DIFF_CORSO`), Z-Score normalizzato del GPA per nazionalità (`VOTO_NORM`) e Target Encoding lisciato (`target_smooth`).
* **Modellazione:** Addestramento ensemble (`RandomForestClassifier` combinato con `DecisionTreeClassifier`) calibrato per gestire classi sbilanciate e prevenire discriminazioni anagrafiche non realistiche.
* **Explainable AI:** Generazione automatica di un report motivazionale trasparente associato a ciascuna decisione, integrato da warning specifici per candidati sotto-età.

### 3. Gestione Dati Massivi & Export Segreteria
* Supporto al caricamento simultaneo di coorti studentesche da file `.xlsx`, `.json` o `.ttl`.
* Toolbar con ricerca full-text per nome, ordinamento alfabetico/esito e filtri multi-stato.
* Esportazione del report finale in formato CSV con codifica UTF-8 con BOM per la perfetta compatibilità con Microsoft Excel.

### 4. Gestione Dinamica dei Requisiti Paese
* Modulo CRUD completo per aggiungere, modificare o eliminare i criteri minimi d'accesso, le scale GPA accettate e le qualifiche abilitanti senza dover riavviare l'applicazione backend.

---

## 📂 Struttura del Repository

```text
├── backend/
│   ├── app.py                      # Entrypoint Flask e configurazione CORS
│   ├── config.py                   # Mapping statici di fallback e percorsi file
│   ├── country_requirements.json   # Database configurazioni e soglie per nazione
│   ├── routes/
│   │   └── admission_routes.py     # Endpoint REST per verifica singola, batch e CRUD
│   ├── services/
│   │   ├── ml_service.py           # Ingestion e inferenza del modello scikit-learn
│   │   ├── ontology_service.py     # Ciclo di vita owlready2, sync HermiT Reasoner
│   │   ├── requirements_service.py # Gestione I/O atomica e thread-safe dei requisiti
│   │   └── student_service.py      # Controlli formali veloci e serializzazione Turtle
│   └── minimum_requirements/
│       └── parse_requirements.py   # Parser automatico PDF -> JSON (PDFPlumber)
├── frontend/
│   ├── admission_verification_form.html      # Portale principale (ML + Ontologia + Admin)
│   ├── admission_verification_ontology.html  # Portale dedicato alla sola verifica logica OWL
│   ├── student_ontology_form.html            # Generatore interattivo di triple RDF/Turtle
│   └── test_students.json                    # Dataset mock per test funzionali rapidi
├── machineLearning/
│   ├── evaluate_model.py           # Script di test, cross-validation 5-fold e metriche
│   └── thresholds                  # Script di addestramento e serializzazione .joblib
├── ontology/
│   ├── Protege0-.rdf               # Ontologia in formato RDF/XML (usata da owlready2)
│   └── Protege0-.ttl               # Ontologia sorgente in sintassi Turtle W3C
├── requirements.txt                # Dipendenze Python
└── SETUP_INSTRUCTIONS.md           # Guida all'avvio locale
```

---

## 🚀 Guida all'Installazione e Avvio

### Prerequisiti
* Python 3.10 o superiore
* Browser moderno (Chrome, Firefox, Safari, Edge)

### 1. Installazione Backend
```bash
# Clonare il repository
git clone [https://github.com/HertzKaa/Microservizi_Segreteria.git](https://github.com/HertzKaa/Microservizi_Segreteria.git)
cd Microservizi_Segreteria

# Creare e attivare l'ambiente virtuale
python -m venv venv
source venv/bin/activate       # Su Linux/macOS
# .\venv\Scripts\Activate.ps1   # Su Windows PowerShell

# Installare le dipendenze
pip install --upgrade pip
pip install -r requirements.txt

# Avviare il server Flask
cd backend
python app.py
```
*Il backend sarà attivo su `http://localhost:5000`.*

### 2. Avvio Frontend
In un secondo terminale, avviare un server statico nella cartella frontend:
```bash
cd frontend
python -m http.server 8000
```
Aprire il browser all'indirizzo:
* **Verifica Integrata (ML + OWL):** `http://localhost:8000/admission_verification_form.html`
* **Verifica Solo Ontologica:** `http://localhost:8000/admission_verification_ontology.html`

> **Credenziali Admin Segreteria:** Per accedere all'area riservata nella pagina di verifica, cliccare su *Accedi come Amministratore* e inserire la password predefinita: `admin`.

---

## 🧪 Metodologia di Test e Valutazione ML

Il modello decisionale integrato è stato validato con partizionamento Train/Test (80/20) e Stratified 5-Fold Cross Validation:

```bash
cd machineLearning
python evaluate_model.py
```

* **Metriche valutate:** Accuracy, Precision, Recall, F1-Score e Confusion Matrix sui casi accademici storici.
* **Pre-requisiti Ontologici:** I vincoli categorici (es. titolo abilitante e durata minima) agiscono come filtro a monte bloccante, prevenendo falsi positivi del modello predittivo.
