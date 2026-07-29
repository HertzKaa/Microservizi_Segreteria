import pandas as pd
import numpy as np
import re
import os
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix

# 1. Caricamento del Dataset
csv_path = 'machineLearning/elenco_domande_pre_admission_titoli.csv'
df = pd.read_csv(csv_path, encoding='latin1', sep=';')

# Normalizzazione categoriche
df['CITTADINANZA'] = df['CITTADINANZA'].astype(str).str.upper().str.strip()
df = df[df['CITTADINANZA'].isin(['IRAN', 'INDIA']) & df['STATO_DOMANDA'].isin(['A', 'R', 'X'])].copy()

df['TARGET'] = df['STATO_DOMANDA'].apply(lambda x: 1 if x == 'A' else 0)

# Calcolo Età e differenza media corso
df['DATA_NASC'] = pd.to_datetime(df['DATA_NASC'], errors='coerce').dt.year
df['ETA'] = 2026 - df['DATA_NASC']
media_eta = df.groupby('TIPO_CORSO_COD')['ETA'].transform('mean')
df['ETA_DIFF_CORSO'] = df['ETA'] - media_eta

# Parsing avanzato del Voto combinando VOTO, BASE_VOTO e VOTO_ALFA
def parse_vote(row):
    v, b = row['VOTO'], row['BASE_VOTO']
    va = str(row['VOTO_ALFA']).strip() if 'VOTO_ALFA' in row and pd.notna(row['VOTO_ALFA']) else ''
    try:
        vf, bf = float(v), float(b)
        if bf > 0 and not pd.isna(vf):
            return vf / bf
    except:
        pass
    if '%' in va:
        m = re.search(r'([\d\.]+)', va)
        if m: return float(m.group(1)) / 100.0
    if '/' in va:
        pts = va.split('/')
        try: return float(pts[0]) / float(pts[1])
        except: pass
    try:
        val = float(va)
        if val <= 1.0: return val
        if val <= 20: return val / 20.0
        if val <= 100: return val / 100.0
    except: pass
    return np.nan

df['VOTO_PCT'] = df.apply(parse_vote, axis=1)
df = df.dropna(subset=['VOTO_PCT']).copy()

# Normalizzazione Voto (Z-Score)
voto_mean = df.groupby('CITTADINANZA')['VOTO_PCT'].transform('mean')
voto_std = df.groupby('CITTADINANZA')['VOTO_PCT'].transform('std')
df['VOTO_NORM'] = (df['VOTO_PCT'] - voto_mean) / voto_std

# Target encoding della cittadinanza
target_smooth = df.groupby('CITTADINANZA')['TARGET'].transform('mean')
df['CITTADINANZA_ENCODED'] = target_smooth

# Encoding altre feature
df['TIPO_CORSO_COD_NUM'] = df['TIPO_CORSO_COD'].apply(lambda x: 1 if x == 'LM' else 0)
df['SESSO_NUM'] = df['SESSO'].apply(lambda x: 1 if str(x).upper().startswith('M') else 0)

feature_cols = ['VOTO_NORM', 'ETA_DIFF_CORSO', 'TIPO_CORSO_COD_NUM', 'CITTADINANZA_ENCODED', 'SESSO_NUM']
X = df[feature_cols].fillna(0)
y = df['TARGET']

print(f"--- DATASET PRONTO PER LA VALUTAZIONE ML ---")
print(f"Campioni Totali: {len(df)} | Ammessi reali (1): {sum(y==1)} | Non Ammessi reali (0): {sum(y==0)}")

# 2. TRAIN-TEST SPLIT (80% Training, 20% Test blind)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

clf = RandomForestClassifier(n_estimators=100, max_depth=4, class_weight='balanced', random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred, zero_division=0)
rec = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)
cm = confusion_matrix(y_test, y_pred)

print("\n--- RISULTATI VALUTAZIONE SU TEST SET (20% Dati mai visti) ---")
print(f"Accuracy (Accuratezza Totale): {acc*100:.2f}%")
print(f"Precision (Precisione Ammissioni): {prec*100:.2f}%")
print(f"Recall (Sensibilità Ammessi): {rec*100:.2f}%")
print(f"F1-Score: {f1*100:.2f}%")

print("\nMatrice di Confusione:")
print(f"Vero Negativo (Bocciati corretti): {cm[0][0]} | Falso Positivo (Erroneamente Ammessi): {cm[0][1]}")
print(f"Falso Negativo (Erroneamente Bocciati): {cm[1][0]} | Vero Positivo (Ammessi corretti): {cm[1][1]}")

# 3. STRATIFIED K-FOLD CROSS-VAL (5-Fold)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(clf, X, y, cv=skf, scoring='accuracy')
cv_f1 = cross_val_score(clf, X, y, cv=skf, scoring='f1')

print(f"\n--- 5-FOLD CROSS VALIDATION ---")
print(f"Accuratezza Media 5-Fold: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")
print(f"F1-Score Medio 5-Fold: {cv_f1.mean()*100:.2f}% (+/- {cv_f1.std()*100:.2f}%)")
