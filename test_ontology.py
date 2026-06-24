#!/usr/bin/env python3
"""
Script di test per verificare che l'ontologia sia caricata correttamente
Esegui questo prima di avviare il backend Flask
"""

import os
import sys

print("🔍 Test di Caricamento Ontologia\n")

# 1. Verifica che il file esista
print("1️⃣  Verifico che il file ontologia esista...")
ontology_files = ["Protege0-.rdf", "Protege0-.ttl"]
ontology_file = None

for file in ontology_files:
    if os.path.exists(file):
        ontology_file = file
        print(f"   ✅ File trovato: {file}")
        file_size = os.path.getsize(file)
        print(f"   📦 Dimensione: {file_size / 1024:.2f} KB")
        break

if not ontology_file:
    print(f"   ❌ ERRORE: Nessun file ontologia trovato")
    print(f"   📂 Directory corrente: {os.getcwd()}")
    print(f"   📂 File disponibili: {os.listdir('.')}")
    sys.exit(1)

print("\n2️⃣  Verifico che owlready2 sia installato...")
try:
    from owlready2 import get_ontology, sync_reasoner
    print("   ✅ owlready2 importato con successo")
except ImportError as e:
    print(f"   ❌ ERRORE: {e}")
    print("   💡 Esegui: pip install owlready2")
    sys.exit(1)

print("\n3️⃣  Carico l'ontologia...")
try:
    onto = get_ontology(f"file://{os.path.abspath(ontology_file)}").load()
    print("   ✅ Ontologia caricata con successo")
except Exception as e:
    print(f"   ❌ ERRORE nel caricamento: {e}")
    sys.exit(1)

print("\n4️⃣  Verifica classi principali nell'ontologia...")
classes_to_check = [
    "Student",
    "IndianStudent",
    "IranianStudent",
    "Course",
    "UndergraduateCourse",
    "PostgraduateCourse",
    "Qualification",
    "EligibleIndianUndergraduateStudent",
    "EligibleIndianPostgraduateStudent",
    "EligibleIranianUndergraduateStudent",
    "EligibleIranianPostgraduateStudent"
]

missing_classes = []
for class_name in classes_to_check:
    try:
        cls = onto[class_name]
        print(f"   ✅ Classe trovata: {class_name}")
    except KeyError:
        print(f"   ⚠️  Classe NON trovata: {class_name}")
        missing_classes.append(class_name)

if missing_classes:
    print(f"\n   ⚠️  AVVISO: {len(missing_classes)} classi non trovate")
    print(f"   Se il form di verifica non funziona, potrebbe essere dovuto a questo")
else:
    print(f"\n   ✅ Tutte le classi principali sono presenti!")

print("\n5️⃣  Verifico proprietà Object...")
try:
    hasAppliedFor = onto["hasAppliedFor"]
    hasQualification = onto["hasQualification"]
    print("   ✅ Proprietà Object trovate")
except KeyError as e:
    print(f"   ⚠️  Proprietà Object mancante: {e}")

print("\n6️⃣  Verifico proprietà Data...")
try:
    hasDurationInYears = onto["hasDurationInYears"]
    hasGPA_Base100 = onto["hasGPA_Base100"]
    print("   ✅ Proprietà Data trovate")
except KeyError as e:
    print(f"   ⚠️  Proprietà Data mancante: {e}")

print("\n" + "="*60)
print("✅ TEST COMPLETATO CON SUCCESSO!")
print("="*60)
print("\n💡 Puoi ora avviare il backend con:\n   python app.py\n")

