import unittest
from pathlib import Path

from src.requirement_three import run_term_ranking
from src.term_ranking import (
    bucket_sort_frequency,
    count_frequencies,
    counting_sort_frequency,
    is_descending_by_frequency,
    radix_sort_frequency,
)


class TermRankingTests(unittest.TestCase):
    def test_count_frequencies_keeps_first_appearance_order(self):
        self.assertEqual(
            count_frequencies(["ia", "texto", "ia", "modelo", "texto", "ia"]),
            [("ia", 3), ("texto", 2), ("modelo", 1)],
        )

    def test_three_sorts_match_and_descend(self):
        items = [("first", 2), ("second", 5), ("third", 2), ("fourth", 11), ("fifth", 5)]
        expected = [("fourth", 11), ("second", 5), ("fifth", 5), ("first", 2), ("third", 2)]
        for algorithm in (counting_sort_frequency, radix_sort_frequency, bucket_sort_frequency):
            ranking = algorithm(items)
            self.assertEqual(ranking, expected)
            self.assertTrue(is_descending_by_frequency(ranking))

    def test_empty_input(self):
        for algorithm in (counting_sort_frequency, radix_sort_frequency, bucket_sort_frequency):
            self.assertEqual(algorithm([]), [])

    def test_complete_requirement_uses_the_abstract_corpus(self):
        results = run_term_ranking(Path("data/processed/abstracts.json"), repetitions=1)
        self.assertEqual(results["total_articles"], 20)
        self.assertTrue(results["validation"].startswith("Los tres rankings"))


if __name__ == "__main__":
    unittest.main()
