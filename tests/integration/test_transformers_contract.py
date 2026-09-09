"""Optional CPU training API contract with a tiny RANDOM model; not a trained product NER."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("ECOMMERCE_ML_CONTRACT") != "1", reason="Opt-in synthetic ML API contract"
)


def test_current_training_entrypoint_saves_reloadable_model_and_tokenizer(tmp_path):
    import hashlib
    import json
    import shutil

    from transformers import BertConfig, BertForTokenClassification, BertTokenizer

    from ecommerce_graph_agent.models.ner.process import tokenize_record
    from ecommerce_graph_agent.models.ner.train import train

    base = tmp_path / "artifacts/local/models/bert-base-chinese"
    base.mkdir(parents=True)
    vocab = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "防", "漏", "杯"]
    (base / "vocab.txt").write_text("\n".join(vocab), encoding="utf-8")
    tokenizer = BertTokenizer(vocab=str(base / "vocab.txt"))
    tokenizer.save_pretrained(base)
    model = BertForTokenClassification(BertConfig(vocab_size=len(vocab), hidden_size=16,
        num_hidden_layers=1, num_attention_heads=2, intermediate_size=32, num_labels=3,
        id2label={0: "B-TAG", 1: "I-TAG", 2: "O"}, label2id={"B-TAG": 0, "I-TAG": 1, "O": 2}))
    model.save_pretrained(base)
    row = {"id": 1, "text": "防漏杯", "label": [{"start": 0, "end": 2, "text": "防漏", "labels": ["TAG"]}]}
    encoded = tokenize_record(tokenizer, row)
    assert encoded["labels"] == [-100, 0, 1, 2, -100]
    split = tmp_path / "data/private/ner-v1"
    split.mkdir(parents=True)
    manifest = {"splits": {}}
    for name in ["train", "validation"]:
        blob = json.dumps([row]).encode()
        (split / f"{name}.json").write_bytes(blob)
        manifest["splits"][name] = {"sha256": hashlib.sha256(blob).hexdigest()}
    (split / "manifest.json").write_text(json.dumps(manifest))
    # A poison test file proves train() never opens the held-out set.
    (split / "test.json").write_text("MUST NOT BE READ")
    lock = tmp_path / "envs/locks/public/public-pip-win64.txt"
    lock.parent.mkdir(parents=True)
    from pathlib import Path
    shutil.copyfile(Path(__file__).resolve().parents[2] / "envs/locks/public/public-pip-win64.txt", lock)
    train(tmp_path, "smoke", "synthetic-contract")
    best = tmp_path / "artifacts/local/synthetic-contract/best_model"
    loaded = BertForTokenClassification.from_pretrained(best, local_files_only=True)
    restored = BertTokenizer.from_pretrained(best, local_files_only=True)
    assert loaded.config.num_labels == 3
    assert tokenize_record(restored, row)["labels"] == encoded["labels"]
    result = json.loads((best / "training_provenance.json").read_text())
    assert result["global_step"] == 2 and result["test_set_loaded"] is False
    assert (best / "model.safetensors").is_file()
