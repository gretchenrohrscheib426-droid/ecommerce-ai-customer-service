import unittest

from ecommerce_graph_agent.models.ner.predict import Predictor, decode_spans
from ecommerce_graph_agent.models.ner.process import align_labels, from_utf16, to_utf16, validate_record


def span(text, start, end):
    return {"start": start, "end": end, "text": text[start:end], "labels": ["TAG"]}


class AlignmentTests(unittest.TestCase):
    def test_real_677_overlap_is_rejected(self):
        text = "x" * 15 + "头层牛皮床"
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            validate_record({"text": text, "label": [span(text, 15, 19), span(text, 18, 20)]})

    def test_whitespace_english_subwords_and_emoji_original_offsets(self):
        text = "  手机 AB😀 防水"
        offsets = [(0, 0), (2, 3), (3, 4), (5, 6), (6, 7), (7, 8), (9, 10), (10, 11), (0, 0)]
        gold = [span(text, 5, 8), span(text, 9, 11)]
        labels = align_labels(text, gold, offsets, [1, 0, 0, 0, 0, 0, 0, 0, 1])
        self.assertEqual(labels, [-100, 2, 2, 0, 1, 1, 0, 1, -100])
        self.assertEqual(decode_spans(text, offsets, [2 if x == -100 else x for x in labels]), gold)

    def test_partial_token_and_unrepresented_gold_fail(self):
        with self.assertRaisesRegex(ValueError, "inside tokenizer"):
            align_labels("ABC", [span("ABC", 1, 3)], [(0, 3)], [0])
        with self.assertRaisesRegex(ValueError, "unrepresentable"):
            align_labels("空白", [span("空白", 0, 2)], [(0, 0)], [1])

    def test_repeated_entities_keep_distinct_spans(self):
        text = "防水 防水"
        self.assertEqual(decode_spans(text, [(0, 2), (3, 5)], [0, 0]), [span(text, 0, 2), span(text, 3, 5)])

    def test_isolated_i_and_final_entity(self):
        self.assertEqual(decode_spans("防水", [(0, 1), (1, 2)], [1, 1]), [span("防水", 0, 2)])

    def test_utf16_surrogates(self):
        self.assertEqual(to_utf16("a😀水", 2), 3)
        self.assertEqual(from_utf16("a😀水", 3), 2)
        with self.assertRaises(ValueError):
            from_utf16("a😀水", 2)

    def test_missing_best_model_never_falls_back(self):
        with self.assertRaises(FileNotFoundError):
            Predictor("nonexistent-best-model")


if __name__ == "__main__":
    unittest.main()


def test_batch_order_and_provenance_without_fake_checkpoint():
    from unittest.mock import MagicMock

    import pytest

    from ecommerce_graph_agent.models.ner.predict import Predictor

    predictor = object.__new__(Predictor)
    predictor.provenance = {"model_sha256": "explicit-unit-mock"}
    predictor.predict = MagicMock(side_effect=lambda text: [{"text": text}])
    rows = predictor.predict_batch(["甲", "乙"])
    assert [r["spans"][0]["text"] for r in rows] == ["甲", "乙"]
    assert all(r["model_sha256"] == "explicit-unit-mock" for r in rows)
    with pytest.raises(ValueError):
        predictor.predict_batch([])
