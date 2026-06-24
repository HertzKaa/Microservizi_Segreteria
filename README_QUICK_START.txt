╔════════════════════════════════════════════════════════════════════════════════╗
║                 🎓 VERIFICA AMMISSIONE - QUICK START GUIDE                       ║
╚════════════════════════════════════════════════════════════════════════════════╝

✅ TUTTO È PRONTO! Ecco come avviare l'applicazione:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1️⃣  - Crea l'Ambiente Virtuale (prima volta)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apri PowerShell nella cartella del progetto e esegui:

    python -m venv venv

[⏳ Questo impiega ~20-30 secondi]

Se ottieni errore, prova:

    python3 -m venv venv
    # oppure
    py -m venv venv

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2️⃣  - Attiva l'Ambiente Virtuale (sempre)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Nel terminale PowerShell, esegui:

    .\venv\Scripts\Activate.ps1

[✓ Dovresti vedere (venv) all'inizio del prompt]

Se ottieni errore sulla politica di esecuzione:

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Poi riprova:

    .\venv\Scripts\Activate.ps1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3️⃣  - Installa le Dipendenze (prima volta)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Con l'ambiente virtuale ATTIVATO (vedi (venv) nel prompt):

    pip install -r requirements.txt

[⏳ Questo impiega ~2-3 minuti]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4️⃣  - Converti il File Ontologia (IMPORTANTE - prima volta)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Con l'ambiente virtuale attivato:

    python convert_turtle.py

[⏳ Questo impiega ~5 secondi]

Output atteso:
    ✅ Grafo caricato: 413 triple
    ✅ File salvato: 50.01 KB

⚠️  IMPORTANTE: Se non esegui questo step, il backend darà errore!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 5️⃣  - Avvia il Backend (sempre)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sempre con l'ambiente virtuale attivato:

    python app.py

[✓ Dovresti vedere "Running on http://127.0.0.1:5000"]

⚠️  NON CHIUDERE QUESTO TERMINALE! Mantenerlo aperto per tutto il tempo che usi l'app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 6️⃣  - Apri il Form nel Browser (nuovo terminale)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apri un NUOVO terminale PowerShell (senza chiudere quello precedente):

    cd "C:\Users\claud\IdeaProjects\Microservizi Segreteria"
    .\venv\Scripts\Activate.ps1
    python -m http.server 8000

Poi apri il browser e vai a:

    http://localhost:8000/admission_verification_form.html

✨ L'app è ora pronta! Inizia compilando il form.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📂 FILE IMPORTANTI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ app.py                              → Backend Flask + owlready2
✓ admission_verification_form.html    → Frontend form (indipendente!)
✓ Protege0-.ttl                       → Ontologia OWL
✓ requirements.txt                    → Dipendenze Python
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

1. "(venv) non appare nel prompt"
   └─→ Significa che l'ambiente virtuale NON è attivato
   └─→ Esegui: .\venv\Scripts\Activate.ps1

2. "Cannot be loaded because running scripts is disabled"
   └─→ Esegui: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

3. "Impossibile connettersi al backend"
   └─→ Assicurati che `python app.py` sia in esecuzione in un altro terminale
   └─→ Verifica che il terminale del backend abbia (venv) attivo

4. "ModuleNotFoundError: No module named 'owlready2'"
   └─→ Non hai attivato venv!
   └─→ Esegui: .\venv\Scripts\Activate.ps1
   └─→ Poi: pip install -r requirements.txt

5. "Port 5000 already in use"
   └─→ Chiudi altri processi Python o cambia porta in app.py
   └─→ Modifica la riga: app.run(debug=True, host='0.0.0.0', port=5001)

Per più dettagli, vedi: SETUP_INSTRUCTIONS.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔌 AL TERMINE (Disattiva l'Ambiente Virtuale)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quando hai terminato di usare l'app, nel terminale esegui:

    deactivate

Il (venv) scomparirà dal prompt.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 BUON LAVORO! 🎉
