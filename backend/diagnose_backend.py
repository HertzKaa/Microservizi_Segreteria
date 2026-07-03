#!/usr/bin/env python3
"""
Script di diagnostica per il backend
Esegui questo per vedere qual è il problema esatto
"""

import sys
import os

print("🔍 DIAGNOSTICA DEL BACKEND\n")

# 1. Verifica file ontologia
print("1️⃣  Verifico file ontologia...")
required_files = ["Protege0-.rdf", "Protege0-.ttl"]
rdf_exists = os.path.exists("../ontology/Protege0-.rdf")
ttl_exists = os.path.exists("../ontology/Protege0-.ttl")

if rdf_exists:
    print(f"   ✅ Protege0-.rdf trovato ({os.path.getsize('../ontology/Protege0-.rdf') / 1024:.1f} KB)")
else:
    print(f"   ❌ Protege0-.rdf NON trovato")
    if ttl_exists:
        print(f"   ⚠️  VEDI? Protege0-.ttl esiste ma .rdf no")
        print(f"   💡 Soluzione: esegui `python convert_turtle.py`")

if ttl_exists:
    print(f"   ✅ Protege0-.ttl trovato ({os.path.getsize('../ontology/Protege0-.ttl') / 1024:.1f} KB)")
else:
    print(f"   ❌ Protege0-.ttl NON trovato")

# 2. Verifica dipendenze
print("\n2️⃣  Verifico dipendenze Python...")
dependencies = ['flask', 'flask_cors', 'owlready2', 'rdflib']
missing = []

for dep in dependencies:
    try:
        __import__(dep.replace('_', '-'))
        print(f"   ✅ {dep}")
    except ImportError:
        print(f"   ❌ {dep} MANCANTE")
        missing.append(dep)

if missing:
    print(f"\n   💡 Installa le dipendenze:")
    print(f"   pip install {' '.join(missing)}")

# 3. Tenta di caricare l'ontologia
print("\n3️⃣  Tenta di caricare l'ontologia...")
try:
    from owlready2 import get_ontology

    if not rdf_exists:
        print(f"   ❌ ERRORE: Protege0-.rdf non esiste!")
        print(f"   💡 Soluzione:")
        print(f"      1. pip install rdflib")
        print(f"      2. python convert_turtle.py")
        sys.exit(1)

    onto = get_ontology(f"file:///{os.path.abspath('../ontology/Protege0-.rdf')}").load()
    print(f"   ✅ Ontologia caricata!")

    # Verifica classi
    required_classes = [
        "Student", "IndianStudent", "IranianStudent",
        "EligibleIndianUndergraduateStudent",
        "EligibleIndianPostgraduateStudent"
    ]

    missing_classes = []
    for cls_name in required_classes:
        if cls_name not in onto:
            missing_classes.append(cls_name)

    if missing_classes:
        print(f"   ⚠️  Classi mancanti: {missing_classes}")
    else:
        print(f"   ✅ Tutte le classi richieste sono presenti")

except Exception as e:
    print(f"   ❌ ERRORE nel caricamento ontologia: {e}")
    print(f"   💡 Soluzione: esegui `python convert_turtle.py`")
    sys.exit(1)

# 4. Tenta di avviare Flask
print("\n4️⃣  Test Flask...")
try:
    from flask import Flask
    app = Flask(__name__)
    print(f"   ✅ Flask funziona")
except Exception as e:
    print(f"   ❌ ERRORE Flask: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ DIAGNOSTICA COMPLETATA!")
print("="*60)
print("\n🚀 Puoi ora avviare il backend con:")
print("   python app.py\n")

