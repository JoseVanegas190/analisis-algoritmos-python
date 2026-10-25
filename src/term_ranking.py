"""Ranking de términos con algoritmos de ordenamiento no comparativos propios."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter_ns


TermFrequency = tuple[str, int]
SortAlgorithm = Callable[[list[TermFrequency]], list[TermFrequency]]


def count_frequencies(tokens: list[str]) -> list[TermFrequency]:
    """Cuenta términos con un diccionario y conserva su primer orden de aparición."""
    counts: dict[str, int] = {}
    for token in tokens:
        # Si es la primera vez, get devuelve 0. Si ya existía, suma una aparición.
        # Un diccionario mantiene el orden en que se insertaron las palabras.
        counts[token] = counts.get(token, 0) + 1
    return list(counts.items())


# Algoritmo Counting Sort
def counting_sort_frequency(items: list[TermFrequency]) -> list[TermFrequency]:
    """Ordena por frecuencia descendente mediante conteo y posiciones indexadas."""
    if not items:
        return []
    maximum = 0
    for _, frequency in items:
        if frequency > maximum:
            maximum = frequency

    # Índice = frecuencia. Por ejemplo, counts[5] guarda cuántos términos
    # aparecieron exactamente cinco veces. No comparamos un término con otro.
    counts = [0] * (maximum + 1)
    for _, frequency in items:
        counts[frequency] += 1

    # positions[frecuencia] dice en qué casilla comienza ese grupo dentro de
    # la salida. Recorremos de máximo a cero para obtener orden descendente.
    positions = [0] * (maximum + 1)
    next_position = 0
    for frequency in range(maximum, -1, -1):
        positions[frequency] = next_position
        next_position += counts[frequency]

    ordered: list[TermFrequency] = [("", 0)] * len(items)
    for term, frequency in items:
        # Ubicamos el término directamente, avanzamos la posición de su grupo
        # y conservamos el orden de llegada cuando dos frecuencias empatan.
        position = positions[frequency]
        ordered[position] = (term, frequency)
        positions[frequency] += 1
    return ordered


def _radix_pass_descending(items: list[TermFrequency], divisor: int) -> list[TermFrequency]:
    """Una pasada estable de Radix Sort; agrupa por el dígito indicado sin comparar."""
    counts = [0] * 10
    for _, frequency in items:
        # divisor=1 mira unidades; 10 mira decenas; 100 mira centenas.
        digit = (frequency // divisor) % 10
        counts[digit] += 1

    # Igual que Counting Sort, pero solo hay diez posibles dígitos. De 9 a 0
    # hace que esta pasada coloque primero el dígito más grande.
    positions = [0] * 10
    next_position = 0
    for digit in range(9, -1, -1):
        positions[digit] = next_position
        next_position += counts[digit]

    ordered: list[TermFrequency] = [("", 0)] * len(items)
    for term, frequency in items:
        digit = (frequency // divisor) % 10
        # Esta pasada es estable: si dos elementos tienen el mismo dígito,
        # salen en el orden en que llegaron de la pasada anterior.
        position = positions[digit]
        ordered[position] = (term, frequency)
        positions[digit] += 1
    return ordered

# Algoritmo Radix Sort
def radix_sort_frequency(items: list[TermFrequency]) -> list[TermFrequency]:
    """Radix Sort LSD descendente para frecuencias enteras no negativas."""
    if not items:
        return []
    maximum = 0
    for _, frequency in items:
        if frequency > maximum:
            maximum = frequency

    ordered = list(items)
    divisor = 1
    while divisor <= maximum:
        # LSD significa que comenzamos por el dígito menos significativo.
        # La estabilidad hace que, al terminar, el número completo quede ordenado.
        ordered = _radix_pass_descending(ordered, divisor)
        divisor *= 10
    return ordered

# Algoritmo Bucket Sort
def bucket_sort_frequency(items: list[TermFrequency]) -> list[TermFrequency]:
    """Bucket Sort por frecuencia: cada índice de bucket representa un conteo."""
    if not items:
        return []
    maximum = 0
    for _, frequency in items:
        if frequency > maximum:
            maximum = frequency

    # Cada bucket es una lista. El bucket 5 recibe todos los términos con
    # frecuencia 5; no hay decisión basada en comparar dos términos.
    buckets: list[list[TermFrequency]] = [[] for _ in range(maximum + 1)]
    for item in items:
        buckets[item[1]].append(item)

    ordered: list[TermFrequency] = []
    # Leer las cajas desde la frecuencia mayor produce el ranking descendente.
    for frequency in range(maximum, -1, -1):
        for item in buckets[frequency]:
            ordered.append(item)
    return ordered


def is_descending_by_frequency(items: list[TermFrequency]) -> bool:
    """Valida con un recorrido que ningún conteo aumente en el ranking."""
    for index in range(1, len(items)):
        if items[index - 1][1] < items[index][1]:
            return False
    return True


def benchmark_sort(
    algorithm: SortAlgorithm, items: list[TermFrequency], repetitions: int = 30
) -> tuple[list[TermFrequency], float]:
    """Mide el promedio real de ejecuciones, en milisegundos, sin alterar la entrada."""
    if repetitions < 1:
        raise ValueError("repetitions debe ser al menos 1")
    total_nanoseconds = 0
    result: list[TermFrequency] = []
    for _ in range(repetitions):
        # perf_counter_ns ofrece una medición de alta resolución en nanosegundos.
        # La lista de entrada no cambia, por lo que cada corrida es comparable.
        started_at = perf_counter_ns()
        result = algorithm(items)
        total_nanoseconds += perf_counter_ns() - started_at
    return result, total_nanoseconds / repetitions / 1_000_000
