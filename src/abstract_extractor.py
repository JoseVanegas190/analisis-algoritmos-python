"""Extracción reproducible de abstracts desde artículos PDF.

PyMuPDF solamente se usa para obtener el texto de cada página. La detección del
abstract se implementa aquí con recorridos secuenciales y comparaciones de
cadenas; esto hace que el criterio sea visible y modificable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import pymupdf


@dataclass
class AbstractResult:
    """Resultado de procesar un artículo."""

    file_name: str
    abstract: str | None
    page_found: int | None
    status: str
    title: str = ""
    authors: str = ""


_START_MARKERS = {"abstract", "resumen", "summary"}
_END_MARKERS = {
    "keywords", "key words", "index terms", "index term", "palabras clave",
    "palabras claves", "key terms", "classification", "jel classification",
}


def _normalise_line(line: str) -> str:
    """Reduce espacios y mayúsculas sin borrar la puntuación útil."""
    return " ".join(line.strip().casefold().split())


def _compact_letters(line: str) -> str:
    """Convierte ``A B S T R A C T`` en ``abstract`` para reconocer PDFs maquetados."""
    return "".join(character for character in _normalise_line(line) if character.isalpha())


def _is_start_marker(line: str) -> bool:
    normalised = _normalise_line(line).rstrip(":.")
    return normalised in _START_MARKERS or _compact_letters(line) in _START_MARKERS


def _start_content(line: str) -> str | None:
    """Devuelve el texto que acompaña a ``Abstract:`` o ``None`` si no inicia."""
    if _is_start_marker(line):
        return ""
    match = re.match(r"^\s*(abstract|resumen|summary)\s*[:.\-–—]\s*(.+)$", line, re.IGNORECASE)
    return match.group(2).strip() if match else None


def _is_end_marker(line: str) -> bool:
    normalised = _normalise_line(line)
    compact = _compact_letters(line)
    if normalised.rstrip(":.") in _END_MARKERS:
        return True
    if any(normalised.startswith(marker + ":") for marker in _END_MARKERS):
        return True
    if compact in {marker.replace(" ", "") for marker in _END_MARKERS}:
        return True
    # Encabezados numerados frecuentes: "1. Introduction" y "I. INTRODUCTION".
    return bool(re.match(r"^(?:\d+(?:\.\d+)*|[ivxlcdm]+)\.?\s+introduction\b", normalised))


def extract_abstract_from_text(text: str) -> str | None:
    """Extrae el primer abstract delimitado por su encabezado y una sección posterior.

    El recorrido es lineal: encuentra el marcador inicial, acumula líneas no
    vacías y termina al encontrar palabras clave o la introducción. Si no hay
    delimitador final, conserva el texto hasta un máximo prudente de caracteres.
    """
    lines = text.splitlines()
    collecting = False
    fragments: list[str] = []
    blank_after_content = False
    skipping_leading_keywords = False

    for raw_line in lines:
        line = raw_line.strip()
        if not collecting:
            first_content = _start_content(line)
            if first_content is not None:
                collecting = True
                if first_content:
                    fragments.append(first_content)
            continue

        if _is_end_marker(line):
            # En diseños a dos columnas el lector puede entregar "ABSTRACT",
            # luego la columna de palabras clave y finalmente el abstract.
            # Como aún no hay contenido, se omite ese bloque de metadatos.
            if not fragments:
                skipping_leading_keywords = True
                continue
            break
        if skipping_leading_keywords:
            # Las palabras clave suelen ser renglones cortos; una línea extensa
            # inicia el texto del abstract situado en la otra columna.
            if len(line) < 80:
                continue
            skipping_leading_keywords = False
        # En algunas maquetaciones no se imprime un encabezado de introducción.
        # Un párrafo nuevo después de un abstract ya sustancial marca entonces el
        # comienzo del cuerpo del artículo.
        if line and blank_after_content and sum(len(piece) for piece in fragments) >= 250:
            break
        if line:
            fragments.append(line)
            blank_after_content = False
        elif fragments:
            blank_after_content = True

        # Evita absorber el documento completo en PDFs cuyo texto no conserva
        # encabezados de sección.
        if sum(len(fragment) for fragment in fragments) >= 2_000:
            break

    if not fragments:
        return None

    abstract = " ".join(fragments)
    abstract = re.sub(r"\s+", " ", abstract).strip()
    return abstract or None


def _page_texts(pdf_path: Path, max_pages: int) -> Iterable[tuple[int, str]]:
    """Entrega el texto de las primeras páginas donde normalmente vive el abstract."""
    full_path = str(pdf_path.resolve())
    if os.name == "nt" and len(full_path) >= 248 and not full_path.startswith("\\\\?\\"):
        full_path = "\\\\?\\" + full_path
    with pymupdf.open(full_path) as document:
        limit = min(len(document), max_pages)
        for page_index in range(limit):
            # Los bloques preservan la separación física de columnas. Insertar
            # una línea vacía evita que el cuerpo de un artículo a dos columnas
            # quede pegado al último renglón del abstract.
            blocks = document[page_index].get_text("blocks")
            text = "\n\n".join(block[4].rstrip() for block in blocks)
            yield page_index + 1, text


def _title_from_file_name(file_name: str) -> str:
    """Crea un título legible cuando el PDF no declara uno en sus metadatos."""
    stem = Path(file_name).stem
    return re.sub(r"^\d+\.\s*", "", stem).strip()


def _pdf_metadata(pdf_path: Path) -> tuple[str, str]:
    """Lee únicamente metadatos descriptivos; nunca infiere autores del texto."""
    full_path = str(pdf_path.resolve())
    if os.name == "nt" and len(full_path) >= 248 and not full_path.startswith("\\\\?\\"):
        full_path = "\\\\?\\" + full_path
    with pymupdf.open(full_path) as document:
        metadata = document.metadata or {}
    title = " ".join((metadata.get("title") or "").split())
    authors = " ".join((metadata.get("author") or "").split())
    return title or _title_from_file_name(pdf_path.name), authors


def extract_abstract_from_pdf(pdf_path: str | Path, max_pages: int = 2) -> AbstractResult:
    """Busca un abstract en las primeras ``max_pages`` páginas de un PDF."""
    path = Path(pdf_path)
    if max_pages < 1:
        raise ValueError("max_pages debe ser al menos 1")

    try:
        title, authors = _pdf_metadata(path)
        for page_number, text in _page_texts(path, max_pages):
            abstract = extract_abstract_from_text(text)
            if abstract is not None:
                return AbstractResult(path.name, abstract, page_number, "found", title, authors)
    except (pymupdf.FileDataError, OSError, RuntimeError) as error:
        return AbstractResult(path.name, None, None, f"error: {error}", _title_from_file_name(path.name), "")

    return AbstractResult(path.name, None, None, "not_found", title, authors)


def extract_directory(input_dir: str | Path, max_pages: int = 2) -> list[AbstractResult]:
    """Procesa los PDFs de una carpeta en orden alfabético estable."""
    directory = Path(input_dir)
    pdfs = sorted(directory.glob("*.pdf"), key=lambda path: path.name.casefold())
    return [extract_abstract_from_pdf(pdf, max_pages) for pdf in pdfs]


def save_results(results: Iterable[AbstractResult], output_path: str | Path) -> None:
    """Guarda resultados en JSON UTF-8 para la siguiente etapa del proyecto."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    records = [asdict(result) for result in results]
    destination.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae abstracts de una carpeta de PDFs.")
    parser.add_argument("input_dir", nargs="?", default="data/pdfs")
    parser.add_argument("--output", default="data/processed/abstracts.json")
    parser.add_argument("--max-pages", type=int, default=2)
    args = parser.parse_args()

    results = extract_directory(args.input_dir, args.max_pages)
    save_results(results, args.output)
    found = sum(result.status == "found" for result in results)
    print(f"Abstracts encontrados: {found}/{len(results)}. Resultado: {args.output}")


if __name__ == "__main__":
    main()
