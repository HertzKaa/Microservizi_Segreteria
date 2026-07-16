"""
Backend Flask per la verifica dell'ammissione tramite Ontologia OWL
Stack: Flask + owlready2 + HermiT Reasoner
"""

import logging
from flask import Flask
from flask_cors import CORS
from routes.admission_routes import admission_bp
from services.ontology_service import load_ontology

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inizializza Flask
app = Flask(__name__)
CORS(app)  # Abilita CORS per le richieste dal frontend

# Registra il Blueprint degli endpoint
app.register_blueprint(admission_bp)

@app.before_request
def init_ontology():
    """Inizializza l'ontologia al primo caricamento delle rotte API"""
    try:
        from services.ontology_service import onto_loaded
        if not onto_loaded:
            logger.info("Inizializzazione ontology_service al primo avvio della richiesta...")
            load_ontology()
    except Exception as e:
        logger.error(f"ATTENZIONE: Impossibile caricare l'ontologia al boot: {str(e)}")
        # Non solleviamo l'eccezione, così il server si avvia per consentire test diagnostici o statici
        # raise

if __name__ == '__main__':
    logger.info("Avvio del backend Flask (Refactored)...")
    app.run(debug=True, host='0.0.0.0', port=5000)