╔════════════════════════════════════════════════════════════════════════════════╗
║                 🎓 VERIFICA AMMISSIONE - QUICK START GUIDE                       ║
╚════════════════════════════════════════════════════════════════════════════════╝

✅ TUTTO È PRONTO! Ecco come avviare l'applicazione:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1️⃣  - Crea l'Ambiente Virtuale (prima volta)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2️⃣  - Attiva l'Ambiente Virtuale (sempre)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apri il terminale integrato di IntelliJ (PowerShell) nella cartella root del progetto e esegui:

    .\.venv\Scripts\Activate.ps1

[✓ Dovresti vedere (.venv) all'inizio del prompt]

Se ottieni errore sulla politica di esecuzione:

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Poi riprova:

    .\.venv\Scripts\Activate.ps1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3️⃣  - Installa le Dipendenze (prima volta)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Con l'ambiente virtuale ATTIVATO (vedi (.venv) nel prompt):

    pip install -r requirements.txt

[⏳ Questo impiega ~2-3 minuti]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4️⃣  - Converti il File Ontologia (IMPORTANTE - prima volta)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Con l'ambiente virtuale attivato, entra nella cartella backend ed esegui la conversione:

    cd C:\Projects\Microservizi_Segreteria\backend
    python convert_turtle.py

[⏳ Questo impiega ~5 secondi]

Output atteso:
    ✅ Grafo caricato: 413 triple
    ✅ File salvato: 50.01 KB

⚠️  IMPORTANTE: Se non esegui questo step, il backend darà errore!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 5️⃣  - Avvia il Backend (sempre)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Rimani nella cartella backend con l'ambiente virtuale attivato:

    python app.py

[✓ Dovresti vedere "Running on http://127.0.0.1:5000"]

⚠️  NON CHIUDERE QUESTO TERMINALE! Mantenerlo aperto per tutto il tempo che usi l'app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 6️⃣  - Apri il Form nel Browser (nuovo terminale)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apri un NUOVO terminale in IntelliJ (cliccando sul tasto + del pannello Terminal):

    cd "C:\Projects\Microservizi_Segreteria\frontend"
    ..\.venv\Scripts\Activate.ps1
    python -m http.server 8000

Poi apri il browser e vai a:

    http://localhost:8000/admission_verification_form.html

✨ L'app è ora pronta! Inizia compilando il form.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📂 STRUTTURA FILE AGGIORNATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ backend/app.py                      → Backend Flask + owlready2
✓ backend/convert_turtle.py           → Script di conversione ontologia
✓ frontend/admission_verification_form.html → Frontend form (indipendente!)
✓ ontology/Protege0-.ttl              → Ontologia OWL originale
✓ requirements.txt                    → Dipendenze Python (nella root)
✓ SETUP_INSTRUCTIONS.md               → Guida completa con troubleshooting

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧪 TEST RAPIDO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Prova con questi dati:

    Nome: Marco Rossi
    Corso: Magistrale (Postgraduate)
    Paese: India
    Titolo: Honours Bachelor
    Durata: 4
    GPA: 75
    Scala: Su 100

Clicca "Verifica Ammissione" e dovresti vedere un risultato!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ QUICK REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Backend URL:        http://localhost:5000
Frontend URL:       http://localhost:8000/admission_verification_form.html
API Health Check:   http://localhost:5000/health

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ PROBLEMI?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. "(.venv) non appare nel prompt"
   └─→ Significa che l'ambiente virtuale NON è attivato
   └─→ Esegui: .\.venv\Scripts\Activate.ps1 (se sei nella root) o ..\.venv\Scripts\Activate.ps1 (se sei in una sottocartella)

2. "Cannot be loaded because running scripts is disabled"
   └─→ Esegui: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

3. "Impossibile connettersi al backend"
   └─→ Assicurati che `python app.py` sia in esecuzione in un altro terminale dentro la cartella backend
   └─→ Verifica che il terminale del backend abbia (.venv) attivo

4. "ModuleNotFoundError: No module named 'owlready2'"
   └─→ Non hai attivato venv!
   └─→ Torna nella root, esegui: .\.venv\Scripts\Activate.ps1
   └─→ Poi reinstalla: pip install -r requirements.txt

5. "Port 5000 already in use"
   └─→ Chiudi altri processi Python o cambia porta in app.py
   └─→ Modifica la riga: app.run(debug=True, host='0.0.0.0', port=5001)

Per più dettagli, vedi: SETUP_INSTRUCTIONS.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔌 AL TERMINE (Disattiva l'Ambiente Virtuale)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quando hai terminato di usare l'app, nel terminale esegui:

    deactivate

Il (.venv) scomparirà dal prompt.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 BUON LAVORO! 🎉