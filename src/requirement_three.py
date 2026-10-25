"""Requerimiento de seguimiento: ranking de términos con tres sorts explícitos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .term_ranking import (
    benchmark_sort,
    bucket_sort_frequency,
    count_frequencies,
    counting_sort_frequency,
    is_descending_by_frequency,
    radix_sort_frequency,
)
from .text_processing import tokenize


ALGORITHMS = {
    "counting_sort": counting_sort_frequency,
    "radix_sort": radix_sort_frequency,
    "bucket_sort": bucket_sort_frequency,
}


def load_abstracts(input_path: str | Path) -> list[str]:
    """Carga solo los abstracts válidos; el seguimiento no usa otros metadatos."""
    records = json.loads(Path(input_path).read_text(encoding="utf-8"))
    return [record["abstract"] for record in records if record.get("abstract")]


def _serialise(items: list[tuple[str, int]]) -> list[dict[str, int | str]]:
    return [{"term": term, "frequency": frequency} for term, frequency in items]


def run_term_ranking(
    input_path: str | Path, top_limit: int = 15, repetitions: int = 30
) -> dict:
    """Tokeniza abstracts, mide los tres algoritmos y valida resultados iguales."""
    if top_limit < 1:
        raise ValueError("top_limit debe ser al menos 1")
    abstracts = load_abstracts(input_path)
    tokens: list[str] = []
    for abstract in abstracts:
        # El requisito trabaja sobre abstracts, no sobre títulos ni autores.
        # tokenize normaliza, elimina signos y quita las stopwords locales.
        tokens.extend(tokenize(abstract))
    frequencies = count_frequencies(tokens)

    methods: dict[str, dict] = {}
    reference: list[tuple[str, int]] | None = None
    for name, algorithm in ALGORITHMS.items():
        # Cada algoritmo recibe la misma lista término-frecuencia. Así la
        # comparación de resultados y de tiempos es justa.
        ranking, average_ms = benchmark_sort(algorithm, frequencies, repetitions)
        if not is_descending_by_frequency(ranking):
            raise ValueError(f"{name} no produjo un ranking descendente")
        if reference is None:
            # Counting Sort se guarda como primer resultado de referencia.
            reference = ranking
        elif ranking != reference:
            # Si hay una diferencia, no se publica un resultado engañoso.
            raise ValueError(f"{name} no coincide con el ranking de referencia")
        methods[name] = {
            "average_execution_ms": round(average_ms, 6),
            "top_terms": _serialise(ranking[:top_limit]),
            "full_ranking": _serialise(ranking),
        }

    return {
        "total_articles": len(abstracts),
        "total_tokens": len(tokens),
        "unique_terms": len(frequencies),
        "top_limit": top_limit,
        "repetitions": repetitions,
        "preprocessing": "Solo abstracts; minúsculas, sin acentos, sin puntuación y sin stopwords locales.",
        "tie_policy": "Se conserva el orden de primera aparición del corpus cuando dos frecuencias son iguales.",
        "validation": "Los tres rankings coinciden exactamente y están en frecuencia descendente.",
        "methods": methods,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seguimiento: ranking de términos con sorts propios.")
    parser.add_argument("--input", default="data/processed/abstracts.json")
    parser.add_argument("--output", default="data/processed/term_ranking.json")
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--repetitions", type=int, default=30)
    args = parser.parse_args()

    results = run_term_ranking(args.input, args.top, args.repetitions)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ranking completado para {results['unique_terms']} términos. Resultado: {destination}")


if __name__ == "__main__":
    main()
