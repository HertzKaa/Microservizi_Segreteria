import os
import sys
import json
import re
import pdfplumber

def clean_line(line):
    return line.strip()

def reconstruct_text(text):
    if not text:
        return ""
    
    raw_lines = [line.strip() for line in text.split('\n') if line.strip()]
    reconstructed_lines = []
    
    # Standard list markers used in the document
    list_markers = ('●', '○', 'o ', '*', '–', '-', '•', '', '1. ', '2. ', '3. ')
    continuation_words = (
        'con', 'di', 'o', 'e', 'a', 'da', 'su', 'per', 'del', 'dei', 'degli', 
        'della', 'delle', 'al', 'ai', 'agli', 'alla', 'alle', 'nel', 'nei', 
        'negli', 'nella', 'nelle', 'col', 'coi', 'sul', 'sulla', 'sulle',
        'with', 'of', 'and', 'or', 'to', 'for', 'at', 'by', 'from', 'in', 'on', 'an', 'a'
    )
    
    for line in raw_lines:
        if not reconstructed_lines:
            reconstructed_lines.append(line)
            continue
            
        prev_line = reconstructed_lines[-1]
        is_new_item = False
        
        if line.startswith(list_markers):
            is_new_item = True
        elif line.startswith(("[Per", "Note:", "Notes:", "Ulteriori", "Sistema")):
            is_new_item = True
        else:
            prev_ends_with_punc = prev_line.endswith(('.', ':', ';'))
            curr_starts_with_lower = line[0].islower() if line else False
            
            prev_words = prev_line.split()
            prev_last_word = prev_words[-1].lower().strip(".,:;()[]") if prev_words else ""
            prev_ends_with_continuation = prev_last_word in continuation_words
            
            if prev_ends_with_continuation or curr_starts_with_lower or not prev_ends_with_punc:
                is_new_item = False
            else:
                is_new_item = True
                
        if is_new_item:
            reconstructed_lines.append(line)
        else:
            reconstructed_lines[-1] = reconstructed_lines[-1] + " " + line
            
    reconstructed_lines = [" ".join(line.split()) for line in reconstructed_lines]
    return "\n".join(reconstructed_lines)

def split_requirements(line):
    line = line.strip()
    duration = None
    grade = None
    
    # 1. Extract duration (1 or 2 digits, preceded by a punctuation/separator, followed by word boundary or end of line)
    dur_match = re.search(r'[\s]*[\-–—/:/]+[\s]*((?:almeno\s+)?\b\d{1,2}\b[\s\S]*?ann[io](?:\s+o\s+più)?)(?:\b|$)', line, re.IGNORECASE)
    if dur_match:
        duration = dur_match.group(1).strip()
        line = line[:dur_match.start()].strip() + " " + line[dur_match.end():].strip()
        line = line.strip()

    # 2. Extract grade/score
    grade_match = re.search(r'[\s,]*\(?\b(con\s+(?:un\s+|una\s+|il\s+|la\s+|di\s+)?(?:voto|valutazione|punteggio|votazione|risultato|media)\b[\s\S]*?|with\s+(?:an?\s+)?(?:average|score|result|final)\b[\s\S]*?)\)?$', line, re.IGNORECASE)
    if grade_match:
        grade = grade_match.group(1).strip()
        line = line[:grade_match.start()].strip()
        
    title = re.sub(r'[\s\-–—/,]+$', '', line).strip()
    return title, duration, grade

def clean_bullets(line):
    cleaned = re.sub(r'^[●○\-\*\•\s]+', '', line)
    cleaned = re.sub(r'^o\s+', '', cleaned)
    return cleaned.strip()

def categorize_requirements(req_text):
    if not req_text or req_text == "N/A" or req_text.strip() == "":
        return {
            "titoli_richiesti": "Requisito non richiesto",
            "voto_minimo": "Requisito non richiesto",
            "durata_minima": "Requisito non richiesto",
            "altri_requisiti": "Requisito non richiesto"
        }
        
    reconstructed = reconstruct_text(req_text)
    lines = [line.strip() for line in reconstructed.split('\n') if line.strip()]
    
    titoli = []
    voti = []
    durata = []
    altri = []
    
    grade_start_words = ("voto", "votazione", "valutazione", "gpa", "media", "punteggio", "punti", "average", "score", "marks")
    duration_start_words = ("durata", "scolarità", "anni", "years")
    
    for line in lines:
        cleaned = clean_bullets(line)
        if not cleaned:
            continue
            
        line_lower = cleaned.lower()
        
        is_meta_or_condition = (
            "devono essere soddisfatti" in line_lower or
            "uno dei seguenti" in line_lower or
            "requisiti devono essere" in line_lower or
            "tutti i requisiti" in line_lower or
            "opzioni presenti al link" in line_lower or
            "unipd.it" in line_lower or
            "maggiori informazioni" in line_lower or
            "allegato" in line_lower or
            "circolare" in line_lower or
            "legalizzazione" in line_lower or
            "sito web" in line_lower or
            "cittadinanza" in line_lower or
            "lingua italiana" in line_lower or
            "italiana sarà richiesta" in line_lower or
            "note:" in line_lower or
            "notes:" in line_lower or
            "accreditati" in line_lower or
            "accreditata" in line_lower or
            line_lower.startswith("gli istituti") or
            line_lower.startswith("i candidati")
        )
        
        if is_meta_or_condition:
            altri.append(line)
            continue
            
        title, dur, grd = split_requirements(cleaned)
        
        if dur:
            durata.append(dur)
        if grd:
            voti.append(grd)
            
        if title:
            title_lower = title.lower()
            is_dur = any(title_lower.startswith(word) for word in duration_start_words)
            is_vot = any(word in title_lower for word in grade_start_words)
            
            if is_dur:
                durata.append(title)
            elif is_vot:
                voti.append(title)
            else:
                titoli.append(title)
                
    def format_list(lst):
        if not lst:
            return "Requisito non richiesto"
        seen = set()
        unique_lst = []
        for x in lst:
            x_clean = clean_bullets(x)
            if x_clean not in seen:
                seen.add(x_clean)
                unique_lst.append(x)
        return "\n".join(unique_lst)
        
    return {
        "titoli_richiesti": format_list(titoli),
        "voto_minimo": format_list(voti),
        "durata_minima": format_list(durata),
        "altri_requisiti": format_list(altri)
    }

def parse_requirements():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, "Padova_requirements.pdf")
    json_path = os.path.join(script_dir, "requirements.json")
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        sys.exit(1)
        
    raw_countries = []
    
    with pdfplumber.open(pdf_path) as pdf:
        # Page 1 table: International Qualifications (2-column layout)
        page1 = pdf.pages[0]
        page1_tables = page1.extract_tables()
        for table in page1_tables:
            for row in table:
                if len(row) < 2:
                    continue
                col_qual = row[0]
                col_req = row[1]
                if not col_qual or not col_req or "QUALIFICHE INTERNAZIONALI" in col_qual:
                    continue
                qual_name = " ".join(col_qual.strip().split())
                raw_countries.append({
                    "country": qual_name,
                    "raw_triennale": col_req,
                    "raw_magistrale": "N/A"
                })
        
        # Pages 2 to 15 tables: Country-wise requirements (3-column layout)
        current_country = None
        for page_idx in range(1, len(pdf.pages)):
            page = pdf.pages[page_idx]
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if len(row) < 3:
                        continue
                    
                    col_country = row[0]
                    col_triennale = row[1]
                    col_magistrale = row[2]
                    
                    # Skip header rows
                    if col_country and "SISTEMA" in col_country and "EDUCATIVO" in col_country:
                        continue
                    
                    # Check if continuation of previous country
                    if not col_country or col_country.strip() == "":
                        if current_country is not None:
                            if col_triennale:
                                current_country["raw_triennale"] += "\n" + col_triennale
                            if col_magistrale:
                                current_country["raw_magistrale"] += "\n" + col_magistrale
                        else:
                            print(f"Warning: Continuation row on page {page_idx+1} has no active country: {row}")
                    else:
                        # New country row
                        country_name = " ".join(col_country.strip().split())
                        current_country = {
                            "country": country_name,
                            "raw_triennale": col_triennale if col_triennale else "",
                            "raw_magistrale": col_magistrale if col_magistrale else ""
                        }
                        raw_countries.append(current_country)
                        
    # Post-process: reconstruct and categorize requirements
    data = []
    for item in raw_countries:
        tri_cat = categorize_requirements(item["raw_triennale"])
        mag_cat = categorize_requirements(item["raw_magistrale"])
        data.append({
            "country": item["country"],
            "triennale": tri_cat,
            "magistrale": mag_cat
        })
        
    # Write output to JSON file
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully processed PDF. Extracted and categorized {len(data)} items and saved to {json_path}")

if __name__ == "__main__":
    parse_requirements()
