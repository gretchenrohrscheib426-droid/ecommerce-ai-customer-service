import pytest

from ecommerce_graph_agent.models.ner.process import tokenize_record


class Encoding(dict):
    def word_ids(self):
        return [None, 0, 2, 2, 3, None]


class Tokenizer:
    is_fast = True

    def __call__(self, words, **kwargs):
        assert words == ["A", " ", "防", "水"]
        assert kwargs["is_split_into_words"] and not kwargs["truncation"]
        return Encoding(
            input_ids=[101, 1, 2, 3, 4, 102],
            offset_mapping=[(0, 0), (0, 1), (0, 1), (0, 1), (0, 1), (0, 0)],
            special_tokens_mask=[1, 0, 0, 0, 0, 1],
        )


def test_word_ids_handle_specials_missing_whitespace_and_multiple_tokens():
    row = {"text": "A 防水", "label": [{"start": 2, "end": 4, "text": "防水", "labels": ["TAG"]}]}
    output = tokenize_record(Tokenizer(), row)
    assert output["labels"] == [-100, 2, 0, 1, 1, -100]
    assert "offset_mapping" not in output
    with pytest.raises(ValueError, match="truncation refused"):
        tokenize_record(Tokenizer(), row, max_length=5)
