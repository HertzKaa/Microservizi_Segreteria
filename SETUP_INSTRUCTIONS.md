# 🎓 Sistema di Verifica Ammissione - OWL Reasoner

Web app per la verifica dell'ammissione tramite ontologia OWL e reasoner HermiT.

**Stack tecnologico:**
- Backend: Python 3.8+ con Flask
- Reasoning: owlready2 (con HermiT integrato)
- Frontend: HTML5 + Vanilla JavaScript
- CORS: Comunicazione cross-origin

---

## 📋 Prerequisiti

- **Python 3.8 o superiore** installato
- **Pip** (package manager Python)
- L'ontologia: `Protege0-.ttl` (fornito nel progetto)

---

## 🚀 Installazione e Setup

### Passo 1: Crea l'Ambiente Virtuale (venv)

Apri un terminale PowerShell nella cartella del progetto e esegui:

```powershell
cd "C:\Users\claud\IdeaProjects\Microservizi Segreteria"
python -m venv venv
```

**Output atteso:**
```
(La cartella venv verrà creata nel progetto)
```

⚠️ Se ottieni "python: The term 'python' is not recognized", prova con:
```powershell
python3 -m venv venv
```

O se nemmeno quello funziona:
```powershell
py -m venv venv
```

### Passo 2: Attiva l'Ambiente Virtuale

Sempre nel terminale PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

**Output atteso:**
```
(venv) PS C:\Users\claud\IdeaProjects\Microservizi Segreteria>
```

⚠️ **IMPORTANTE:** Vedrai `(venv)` all'inizio del prompt. Se non lo vedi, l'ambiente non è attivato!

Se ottieni un errore di permessi tipo `cannot be loaded because running scripts is disabled`:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Poi riprova a eseguire `.\venv\Scripts\Activate.ps1`

### Passo 3: Installa le Dipendenze

**Con l'ambiente virtuale ATTIVATO** (vedi il `(venv)` nel prompt), esegui:

```powershell
pip install -r requirements.txt
```

**Output atteso:**
```
Successfully installed Flask-2.3.3 Flask-CORS-4.0.0 owlready2-0.46 Werkzeug-2.3.7 rdflib-7.6.0
```

### Passo 4: Converti il File Ontologia (IMPORTANTE!)

L'ontologia è in formato Turtle (.ttl) e va convertita in RDF/XML (.rdf) per miglior compatibilità:

```powershell
python convert_turtle.py
```

**Output atteso:**
```
🔄 Conversione Turtle → RDF/XML

1️⃣  Leggendo Protege0-.ttl...
   ✅ Grafo caricato: 413 triple

2️⃣  Salvando in formato RDF/XML (Protege0-.rdf)...
   ✅ File salvato: 50.01 KB

✅ CONVERSIONE COMPLETA!
```

⚠️ **IMPORTANTE:** Se non esegui questo step, il backend darà errore!

### Passo 5: Verifica i File Necessari

Assicurati che nella cartella del progetto ci siano:
- ✅ `app.py` (backend Flask)
- ✅ `admission_verification_form.html` (frontend form)
- ✅ `Protege0-.rdf` (ontologia OWL in RDF/XML - generato dal passo 4)
- ✅ `Protege0-.ttl` (ontologia originale in Turtle)
- ✅ `requirements.txt` (dipendenze)
- ✅ `convert_turtle.py` (script di conversione)

```powershell
ls
```

---

## ▶️ Avvio dell'Applicazione

### Passo 1: Attiva l'Ambiente Virtuale (ogni volta!)

Dal terminale PowerShell nella cartella del progetto:

```powershell
.\venv\Scripts\Activate.ps1
```

**Verifica:** Dovresti vedere `(venv)` all'inizio del prompt

### Passo 2: (Facoltativo) Testa l'Ontologia

Per verificare che tutto sia a posto, esegui:

```powershell
python test_ontology.py
```

**Output atteso:** Tutte le classi dovrebbero essere trovate con ✅

### Passo 3: Avvia il Backend Flask

Sempre con l'ambiente virtuale attivato:

```powershell
python app.py
```

**Output atteso:**
```
WARNING in app.run application to run on http://127.0.0.1:5000
Press CTRL+C to quit
Restarting with reloader
* Debugger is active!
* Debugger PIN: 123-456-789
```

✅ **Il backend è ora attivo su `http://localhost:5000`**

### Passo 4: Apri il Frontend nel Browser

Senza chiudere il terminale con il backend, apri il file HTML nel browser (in un NUOVO terminale restando con venv attivato):

**Opzione 1 - File locale:**
```
Double-click su admission_verification_form.html
```

**Opzione 2 - Tramite browser (consigliato):**
1. Apri il browser (Chrome, Firefox, Edge, ecc.)
2. Naviga a: `file:///C:/Users/claud/IdeaProjects/Microservizi%20Segreteria/admission_verification_form.html`

**Opzione 3 - Con un server locale (ancora meglio):**
```powershell
# Se hai Python3, puoi usare:
python -m http.server 8000

# Poi vai a: http://localhost:8000/admission_verification_form.html
```

---

## 🧪 Test dell'Applicazione

### Test 1: Studente Indiano - Undergraduate
1. **Nome:** Marco Rossi
2. **Corso:** Triennale (Undergraduate)
3. **Paese:** India
4. **Titolo:** All-India Senior School
5. **Durata:** Non richiesta
6. **GPA:** 75 (Su 100)
7. Clicca **"Verifica Ammissione"**

**Risultato atteso:** ❌ Non Ammesso (manca una qualifica valida per l'undergraduate)

### Test 2: Studente Indiano - Postgraduate (Honours Bachelor)
1. **Nome:** Animesh Kumar
2. **Corso:** Magistrale (Postgraduate)
3. **Paese:** India
4. **Titolo:** Honours Bachelor
5. **Durata:** 4 (anni)
6. **GPA:** 75 (Su 100)
7. Clicca **"Verifica Ammissione"**

**Risultato atteso:** ✅ Ammesso (se i criteri dell'ontologia sono soddisfatti)

### Test 3: Studente Iraniano - Undergraduate
1. **Nome:** Farshad Ahmadi
2. **Corso:** Triennale (Undergraduate)
3. **Paese:** Iran
4. **Titolo:** Diplom-e-Motevasete
5. **Durata:** Non richiesta
6. **GPA:** 17 (Su 20)
7. Clicca **"Verifica Ammissione"**

**Risultato atteso:** ✅ Ammesso (se i criteri sono soddisfatti)

---

## 🔌 Disattivare l'Ambiente Virtuale

Quando hai finito di usare l'app, puoi disattivare l'ambiente virtuale eseguendo:

```powershell
deactivate
```

**Risultato:** Il `(venv)` scomparirà dal prompt

## 📚 Struttura del Progetto

```
Microservizi Segreteria/
├── venv/                            # Ambiente virtuale (ignorare)
├── app.py                           # Backend Flask + owlready2
├── admission_verification_form.html # Frontend (nuovo form indipendente)
├── Protege0-.ttl                    # Ontologia OWL
├── requirements.txt                 # Dipendenze Python
├── SETUP_INSTRUCTIONS.md            # Guida completa
└── README_QUICK_START.txt           # Quick start
```

---

## 🔧 Come Funziona

### Flow dell'Applicazione

1. **Frontend Compila il Form**
   - L'utente inserisce i dati accademici
   - JavaScript valida e prepara il JSON

2. **Invio Dati al Backend**
   ```javascript
   fetch('http://localhost:5000/check-admission', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify(data)
   })
   ```

3. **Backend Elabora l'Ontologia**
   - Carica `Protege0-.ttl` con owlready2
   - Crea individui temporanei: Student, Course, Qualification
   - Configura le proprietà (durata, GPA, ecc.)
   - Esegue il reasoner (HermiT via sync_reasoner())
   - Verifica se lo studente appartiene a una classe di eligibilità
   - Elimina gli individui temporanei (pulizia)

4. **Backend Ritorna il Risultato**
   ```json
   {
       "admitted": true/false,
       "student": "Nome",
       "country": "India/Iran",
       "course": "Undergraduate/Postgraduate"
   }
   ```

5. **Frontend Mostra il Risultato**
   - ✅ Ammesso (con box verde)
   - ❌ Non Ammesso (con box rosso)

---

## 📡 Endpoints API

### `GET /health`
Verifica la salute del backend

**Response:**
```json
{ "status": "ok", "message": "Backend is running" }
```

### `POST /check-admission`
Verifica l'ammissione dello studente

**Request:**
```json
{
    "name": "Mario Rossi",
    "course": "Undergraduate",
    "country": "India",
    "qualification": "HonoursBachelor",
    "duration": 4,
    "gpa": 75,
    "gpaScale": "Base100"
}
```

**Response (Ammesso):**
```json
{
    "admitted": true,
    "student": "Mario_Rossi",
    "country": "India",
    "course": "Undergraduate"
}
```

**Response (Non Ammesso):**
```json
{
    "admitted": false,
    "student": "Mario_Rossi",
    "country": "India",
    "course": "Undergraduate"
}
```

### `GET /qualifications?country=India&course=Undergraduate`
Ottiene le qualifiche disponibili

**Response:**
```json
{
    "qualifications": [
        {
            "key": "AllIndiaSeniorSchool",
            "label": "All-India Senior School",
            "requiresDuration": false
        }
    ]
}
```

### `GET /gpa-scales?country=India`
Ottiene le scale GPA disponibili

**Response:**
```json
{
    "scales": [
        { "value": "Base100", "label": "Su 100" },
        { "value": "Base10", "label": "Su 10" },
        { "value": "Base8", "label": "Su 8" },
        { "value": "Base4", "label": "Su 4" }
    ]
}
```

---

## 🐛 Risoluzione dei Problemi

### ❌ "python: The term 'python' is not recognized"
- **Soluzione:** Usa uno di questi comandi:
  ```powershell
  python3 -m venv venv
  # oppure
  py -m venv venv
  # oppure cerca Python nelle variabili d'ambiente
  ```

### ❌ "Cannot be loaded because running scripts is disabled on this system"
- **Soluzione:** Esegui questo comando UNA VOLTA:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
  Poi riprova l'attivazione: `.\venv\Scripts\Activate.ps1`

### ❌ "(venv) non appare nel prompt dopo Activate.ps1"
- **Soluzione:** L'ambiente non è attivato correttamente. Riprova dall'inizio:
  ```powershell
  deactivate  # Se era attivo
  .\venv\Scripts\Activate.ps1
  python --version  # Verifica che Python funzioni
  ```

### ❌ "ModuleNotFoundError: No module named 'owlready2'"
- **Causa:** Dimenticato di attivate venv o pip ha installato in locale
- **Soluzione 1:** Attiva venv: `.\venv\Scripts\Activate.ps1`
- **Soluzione 2:** Reinstalla: `pip install -r requirements.txt`

### ❌ "Impossibile connettersi al backend"
- **Causa probabile:** Venv non attivato, backend non avviato
- **Soluzione:**
  1. Apri un terminale PowerShell nella cartella del progetto
  2. `.\venv\Scripts\Activate.ps1` (attiva venv)
  3. `python app.py` (avvia il backend)
  4. Verifica che veda "Running on http://127.0.0.1:5000"

### ❌ "File ontologia non trovato: Protege0-.ttl"
- **Soluzione:** Assicurati che `Protege0-.ttl` sia nella stessa cartella di `app.py`

### ❌ "Port 5000 already in use"
- **Soluzione:** Cambia la porta in `app.py` riga 188:
  ```python
  app.run(debug=True, host='0.0.0.0', port=5001)  # Cambia a 5001
  ```
  E aggiorna `BACKEND_URL` nel form HTML a `http://localhost:5001`

### ⚠️ Le requests sono lente
- Owlready2 + HermiT impiegano qualche secondo su ontologie complesse
- È normale! Il reasoner sta lavorando sottofondo

---

## 📖 Note Importanti

### 1. **Isolamento della Logica**
Il form `admission_verification_form.html` è **completamente indipendente** da `student_ontology_form.html`:
- ✅ Ha il suo stile CSS personalizzato
- ✅ Ha la sua logica JavaScript
- ✅ Comunica solo con il backend

### 2. **Pulizia dell'Ontologia**
Il backend **elimina automaticamente** gli individui temporanei dopo ogni verifica:
- Evita l'inquinamento dell'ontologia in memoria
- Garantisce coerenza tra le richieste successive
- È fondamentale per evitare effetti collaterali

### 3. **Reasoner HermiT**
owlready2 usa il reasoner HermiT:
- Inferisce le classi implicite
- Verifica la consistency dell'ontologia
- È automaticamente integrato, nessuna configurazione richiesta

---

## 🚢 Deploy in Produzione

Per deployare su server remoto (es. Heroku, AWS, ecc.):

1. Installa Gunicorn: `pip install gunicorn`
2. Esegui: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
3. Configura CORS per il dominio produttivo:
   ```python
   from flask_cors import CORS
   CORS(app, resources={r"/api/*": {"origins": "https://example.com"}})
   ```

---

## 📞 Supporto

Se hai problemi:
1. Controlla i log nel terminale (Flask mostra messaggi dettagliati)
2. Apri la console del browser (F12) e guarda gli errori JavaScript
3. Verifica che tutti i file siano nella cartella corretta

---

**Buon lavoro! 🚀**

