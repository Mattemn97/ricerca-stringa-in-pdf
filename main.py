#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modulo per l'analisi e la ricerca testuale (Standard e REGEX) all'interno di documenti PDF.
Include interfaccia CLI basata su 'rich' e logging avanzato.
"""

import re
from pathlib import Path
from typing import List

from PyPDF2 import PdfReader
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

# Importazione del logger aziendale
from custom_logger import logger


# ==========================================
# CORE: Logica di Business
# ==========================================

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Estrae il testo da un file PDF. Ritorna una stringa vuota in caso di errore di lettura.
    
    :param pdf_path: Percorso del file PDF.
    :return: Testo estratto dal documento.
    """
    try:
        reader = PdfReader(str(pdf_path))
        text_blocks: List[str] = []
        
        for page_num, page in enumerate(reader.pages):
            try:
                extracted = page.extract_text()
                if extracted:
                    text_blocks.append(extracted)
            except Exception as e:
                logger.debug(f"Impossibile estrarre il testo dalla pagina {page_num} del file {pdf_path.name}: {e}")
                continue
                
        return "\n".join(text_blocks)
    except Exception as e:
        logger.error(f"Errore durante l'apertura o la lettura del file {pdf_path.name}: {e}")
        return ""


def evaluate_search_criteria(text: str, pattern: str, use_regex: bool) -> bool:
    """
    Valuta se il criterio di ricerca è presente nel testo fornito.
    
    :param text: Il contenuto testuale da analizzare.
    :param pattern: La stringa o l'espressione regolare da cercare.
    :param use_regex: Booleano che determina se utilizzare logica REGEX.
    :return: True se il criterio è soddisfatto, False altrimenti.
    """
    if not text:
        return False

    if use_regex:
        try:
            return re.search(pattern, text, re.IGNORECASE) is not None
        except re.error as e:
            logger.error(f"Errore di sintassi nell'espressione regolare '{pattern}': {e}")
            return False
    else:
        return pattern.lower() in text.lower()


def discover_pdf_files(target_path: Path) -> List[Path]:
    """
    Identifica tutti i documenti PDF presenti nel percorso specificato.
    Se il percorso è una directory, effettua una ricerca ricorsiva.
    
    :param target_path: Percorso del file o della cartella.
    :return: Lista di percorsi (Path) ai file PDF validi.
    """
    if target_path.is_file():
        if target_path.suffix.lower() == ".pdf":
            return [target_path]
        return []
    elif target_path.is_dir():
        return [p for p in target_path.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"]
    return []


# ==========================================
# INTERFACCIA: Logica UI e Flusso di Esecuzione
# ==========================================

def main() -> None:
    """
    Punto di ingresso principale dell'applicazione. Gestisce l'interazione utente,
    la raccolta degli input e la presentazione dei risultati.
    """
    console = Console()
    console.clear()

    # Banner di Benvenuto
    console.print("[bold cyan]--- STRUMENTO DI RICERCA DOCUMENTALE AVANZATA PDF ---[/bold cyan]\n")
    logger.info("Avvio del modulo di ricerca documentale PDF.")

    # 1. Configurazione Criteri di Ricerca
    use_regex = Confirm.ask("Utilizzare espressioni regolari (REGEX) per la ricerca?")
    logger.debug(f"Modalita REGEX selezionata dall'utente: {use_regex}")

    prompt_msg = "Inserire l'espressione regolare da cercare" if use_regex else "Inserire la stringa da cercare"
    search_pattern = Prompt.ask(prompt_msg).strip().strip('"')

    if not search_pattern:
        logger.warning("Esecuzione interrotta: Nessun criterio di ricerca inserito.")
        console.print("[bold red]Errore: Il criterio di ricerca non puo essere vuoto. Operazione annullata.[/bold red]")
        return

    # 2. Configurazione Percorso
    while True:
        path_input = Prompt.ask("Inserire il percorso del file o della cartella da analizzare").strip().strip('"')
        target_path = Path(path_input)

        if target_path.exists():
            break
        
        logger.warning(f"L'utente ha inserito un percorso non valido: {path_input}")
        console.print("[bold red]Errore: Il percorso specificato non esiste. Riprovare.[/bold red]")

    # 3. Identificazione dei file
    logger.info(f"Avvio della scansione per i file PDF nel percorso: {target_path.resolve()}")
    pdf_files = discover_pdf_files(target_path)

    if not pdf_files:
        logger.warning("Scansione terminata: Nessun file PDF rilevato nel percorso.")
        console.print("[bold yellow]Attenzione: Nessun documento PDF trovato nel percorso indicato. Uscita.[/bold yellow]")
        return

    # 4. Tabella di Riepilogo
    summary_table = Table(title="Riepilogo Parametri di Elaborazione", header_style="bold magenta")
    summary_table.add_column("Parametro", style="dim")
    summary_table.add_column("Valore")

    summary_table.add_row("Percorso Selezionato", str(target_path.resolve()))
    summary_table.add_row("Modalita di Ricerca", "Espressione Regolare (REGEX)" if use_regex else "Testo Semplice")
    summary_table.add_row("Criterio di Ricerca", search_pattern)
    summary_table.add_row("Totale Documenti da Analizzare", str(len(pdf_files)))

    console.print("\n")
    console.print(summary_table)
    console.print("\n")

    if not Confirm.ask("Procedere con l'elaborazione dei documenti?"):
        logger.info("L'operazione e stata annullata dall'utente in fase di conferma.")
        console.print("Operazione annullata.")
        return

    # 5. Elaborazione con Barra di Progresso
    found_pdfs: List[Path] = []
    not_found_pdfs: List[Path] = []

    logger.info("Avvio dell'elaborazione massiva dei documenti.")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        
        task_id = progress.add_task("[cyan]Analisi dei documenti in corso...", total=len(pdf_files))

        for pdf_path in pdf_files:
            logger.debug(f"Inizio analisi del file: {pdf_path.name}")
            extracted_content = extract_text_from_pdf(pdf_path)

            if evaluate_search_criteria(extracted_content, search_pattern, use_regex):
                found_pdfs.append(pdf_path)
            else:
                not_found_pdfs.append(pdf_path)

            progress.advance(task_id)

    # 6. Scrittura dei file di Output
    output_found = Path("documenti_con_corrispondenza.txt")
    output_missing = Path("documenti_senza_corrispondenza.txt")

    try:
        with output_found.open("w", encoding="utf-8") as f_out:
            for p in found_pdfs:
                f_out.write(f"{p.resolve()}\n")

        with output_missing.open("w", encoding="utf-8") as f_out:
            for p in not_found_pdfs:
                f_out.write(f"{p.resolve()}\n")
                
        logger.info("Salvataggio dei file di report completato con successo.")
    except Exception as e:
        logger.critical(f"Errore: {e}", exc_info=True)
        console.print("[bold red]Errore critico durante la scrittura dei report di output. Consultare i log.[/bold red]")
        return

    # 7. Report Finale
    logger.info("Elaborazione conclusa con successo.")
    console.print("\n[bold green]--- ELABORAZIONE COMPLETATA ---[/bold green]")
    console.print(f"Documenti contenenti il criterio: [bold cyan]{len(found_pdfs)}[/bold cyan] (Report: {output_found.name})")
    console.print(f"Documenti non contenenti il criterio: [bold cyan]{len(not_found_pdfs)}[/bold cyan] (Report: {output_missing.name})")
    console.print("\nOperazione terminata.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Esecuzione interrotta manualmente dall'utente (KeyboardInterrupt).")
        Console().print("\n[bold yellow]Elaborazione interrotta dall'utente.[/bold yellow]")
    except Exception as unexpected_exception:
        logger.critical(f"Errore: {unexpected_exception}", exc_info=True)
        Console().print("\n[bold red]Si è verificato un errore di sistema irreversibile. Consultare i file di log.[/bold red]")