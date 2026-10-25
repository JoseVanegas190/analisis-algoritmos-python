"""Preprocesamiento transparente de abstracts para los algoritmos clásicos."""

from __future__ import annotations

import re
import unicodedata


# Lista local y deliberadamente pequeña: no descarga recursos ni oculta la lógica.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it",
    "of", "on", "or", "that", "the", "this", "to", "with", "y", "de", "del", "la", "las",
    "el", "los", "en", "un", "una", "para", "por", "con", "que", "se", "su", "sus", "al",
}


def normalise_text(text: str) -> str:
    """Pasa a minúsculas y elimina acentos para comparar términos de forma estable."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    """Tokeniza con una expresión regular y filtros explícitos."""
    words = re.findall(r"[a-z]+", normalise_text(text))
    if not remove_stopwords:
        return words
    return [word for word in words if word not in STOPWORDS]
