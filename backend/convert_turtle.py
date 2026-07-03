#!/usr/bin/env python3
"""
Script per convertire Protege0-.ttl (Turtle) in RDF/XML
rdflib legge Turtle e owlready2 legge RDF/XML meglio
"""

import os
from rdflib import Graph

print("🔄 Conversione Turtle → RDF/XML\n")

# File di input e output
ttl_file = "../ontology/Protege0-.ttl"
rdf_file = "../ontology/Protege0-.rdf"

if not os.path.exists(ttl_file):
    print(f"❌ ERRORE: {ttl_file} non trovato!")
    exit(1)

print(f"1️⃣  Leggendo {ttl_file}...")
try:
    g = Graph()
    g.parse(ttl_file, format="turtle")
    print(f"   ✅ Grafo caricato: {len(g)} triple")
except Exception as e:
    print(f"   ❌ ERRORE nel parsing Turtle: {e}")
    exit(1)

print(f"\n2️⃣  Salvando in formato RDF/XML ({rdf_file})...")
try:
    g.serialize(destination=rdf_file, format="xml")
    file_size = os.path.getsize(rdf_file)
    print(f"   ✅ File salvato: {file_size / 1024:.2f} KB")
except Exception as e:
    print(f"   ❌ ERRORE nel salvataggio: {e}")
    exit(1)

print(f"\n✅ CONVERSIONE COMPLETA!")
print(f"\n💡 Il backend userà automaticamente {rdf_file}")

