"""Inference requires an actual saved, fine-tuned bundle and preserves original text."""

import json
from pathlib import Path


def decode_spans(text, offsets, labels):
    if len(offsets) != len(labels):
        raise ValueError("Prediction/offset length mismatch")
    spans: list[dict] = []
    current: list[int] | None = None

    def finish():
        nonlocal current
        if current is not None:
            start, end = current
            spans.append({"start": start, "end": end, "text": text[start:end], "labels": ["TAG"]})
            current = None

    for (start, end), label in zip(offsets, labels, strict=True):
        if start == end:
            continue
        if not 0 <= start < end <= len(text) or label not in (0, 1, 2):
            raise ValueError("Invalid prediction")
        if label == 2:
            finish()
        elif label == 0 or current is None or any(not c.isspace() for c in text[current[1] : start]):
            finish()
            current = [start, end]  # isolated I treated as a new entity, explicitly tested
        else:
            current[1] = end
    finish()
    return spans


class Predictor:
    def __init__(self, model_dir, device="cpu", allow_smoke=False):
        path = Path(model_dir)
        required = ["training_provenance.json", "config.json", "tokenizer_config.json", "model.safetensors"]
        if any(not (path / name).is_file() for name in required):
            raise FileNotFoundError("Trained model bundle incomplete; no base-model or rules fallback")
        self.provenance = json.loads((path / required[0]).read_text(encoding="utf-8"))
        if self.provenance.get("run_type") != "full" and not allow_smoke:
            raise ValueError("Smoke checkpoint is not a full trained model")
        from transformers import AutoModelForTokenClassification, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, use_fast=True)
        if not self.tokenizer.is_fast:
            raise ValueError("Fast tokenizer required for original-text offsets")
        self.model = (
            AutoModelForTokenClassification.from_pretrained(path, local_files_only=True).to(device).eval()
        )
        if self.model.config.id2label != {0: "B-TAG", 1: "I-TAG", 2: "O"}:
            raise ValueError("Unexpected label mapping")
        self.device = device

    def predict(self, text):
        return self.predict_details(text)["entities"]

    def predict_details(self, text):
        import torch

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Nonempty input required")
        if self.provenance.get("alignment_strategy") == "character-words-word-ids-v1":
            from .process import tokenize_with_offsets

            encoded = tokenize_with_offsets(
                self.tokenizer, text, self.model.config.max_position_embeddings, return_tensors="pt"
            )
            offsets = encoded.pop("offset_mapping")
            encoded.pop("special_tokens_mask")
        else:
            # Existing verified bundles explicitly retain their original offset strategy.
            encoded = self.tokenizer(text, return_offsets_mapping=True, return_tensors="pt", truncation=False)
            offsets = encoded.pop("offset_mapping")[0].tolist()
        if encoded["input_ids"].shape[1] > self.model.config.max_position_embeddings:
            raise ValueError("Input too long; explicit windowing required")
        with torch.inference_mode():
            labels = (
                self.model(**{k: v.to(self.device) for k, v in encoded.items()})
                .logits[0]
                .argmax(-1)
                .cpu()
                .tolist()
            )
        return {
            "original_text": text,
            "token_offsets": offsets,
            "entities": decode_spans(text, offsets, labels),
            "model_sha256": self.provenance["model_sha256"],
        }

    def extract(self, text):
        return [s["text"] for s in self.predict(text)]

    def predict_batch(self, texts):
        """Bounded sequential inference preserves input order and the real model version."""
        if not isinstance(texts, list) or not 1 <= len(texts) <= 128:
            raise ValueError("Batch must contain 1–128 texts")
        return [
            {"spans": self.predict(text), "model_sha256": self.provenance["model_sha256"]} for text in texts
        ]
