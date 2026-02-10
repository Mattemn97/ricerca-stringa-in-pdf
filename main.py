#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ricerca di una stringa all'interno di uno o più PDF (anche ricorsiva).
Supporta sia ricerca semplice che ricerca tramite REGEX.

- Analizza singolo PDF o cartella (con sottocartelle)
- Usa PyPDF2 per estrarre il testo
- Barra di progresso (tqdm)
- Supporto REGEX opzionale
- Genera:
      • File con la stringa.txt
      • File senza stringa.txt
"""

import os
import re
from tqdm import tqdm
from PyPDF2 import PdfReader


# ---------------- Estrazione testo PDF ----------------
def extract_text_from_pdf(pdf_path):
    """Estrae il testo da un PDF. Ritorna stringa vuota in caso di errore."""
    try:
        reader = PdfReader(pdf_path)
        text = []
        for page in reader.pages:
            try:
                text.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(text)
    except Exception:
        return ""


# ---------------- Ricerca stringa normale ----------------
def search_simple(text, needle):
    """Ricerca semplice (case-insensitive)."""
    return needle.lower() in text.lower()


# ---------------- Ricerca tramite REGEX ----------------
def search_regex(text, pattern):
    """Ricerca REGEX (case-insensitive)."""
    try:
        return re.search(pattern, text, re.IGNORECASE) is not None
    except re.error:
        return False


# ---------------- Ricerca in PDF ----------------
def search_in_pdf(pdf_path, needle, use_regex):
    """Ritorna True se la stringa (o regex) è presente nel PDF."""
    text = extract_text_from_pdf(pdf_path)
    if use_regex:
        return search_regex(text, needle)
    else:
        return search_simple(text, needle)


# ---------------- Scansione ricorsiva ----------------
def get_all_pdfs_recursive(folder_path):
    """Ritorna lista di TUTTI i PDF dentro la cartella (ricorsivamente)."""
    pdfs = []
    for root, _, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdfs.append(os.path.join(root, f))
    return pdfs


# ---------------- Flusso guidato ----------------
def guided_flow():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("— Ricerca stringa/REGEX nei PDF (ricorsiva) —\n")

    # 1) Vuoi usare REGEX?
    use_regex = input("Vuoi usare una REGEX? [s/N]: ").strip().lower() in ("s", "si", "y", "yes")

    # 2) Inserimento criterio
    if use_regex:
        needle = input("1) Inserisci la REGEX da cercare: ").strip()
    else:
        needle = input("1) Inserisci la stringa da cercare: ").strip()

    if not needle:
        print("❌ Nessun valore inserito. Interrompo.")
        return

    # 3) Percorso
    while True:
        path = input("\n2) Inserisci percorso PDF o cartella: ").strip()
        if os.path.isfile(path) and path.lower().endswith(".pdf"):
            pdf_files = [path]
            break
        elif os.path.isdir(path):
            pdf_files = get_all_pdfs_recursive(path)
            if not pdf_files:
                print("❌ Nessun PDF trovato (nemmeno nelle sottocartelle). Riprova.")
                continue
            break
        else:
            print("❌ Percorso non valido. Riprova.")

    print(f"\n📄 PDF trovati: {len(pdf_files)}\n")

    # 4) File output
    out_yes = "File con la stringa.txt"
    out_no = "File senza stringa.txt"

    found = []
    not_found = []

    # 5) Analisi
    desc = "Analisi PDF (REGEX)" if use_regex else "Analisi PDF"
    for pdf in tqdm(pdf_files, desc=desc, unit="file"):
        if search_in_pdf(pdf, needle, use_regex):
            found.append(pdf)
        else:
            not_found.append(pdf)

    # 6) Scrittura risultati
    with open(out_yes, "w", encoding="utf-8") as f:
        for p in found:
            f.write(p + "\n")

    with open(out_no, "w", encoding="utf-8") as f:
        for p in not_found:
            f.write(p + "\n")

    # 7) Report
    print("\n— RISULTATO —")
    print(f"✔ File con la stringa/regex: {len(found)} → {out_yes}")
    print(f"✘ File senza: {len(not_found)} → {out_no}")
    print("\nFatto! Report generati.")
    input("\nPremi un tasto per proseguire...")


# ---------------- Entrypoint ----------------
if __name__ == "__main__":
    guided_flow()
