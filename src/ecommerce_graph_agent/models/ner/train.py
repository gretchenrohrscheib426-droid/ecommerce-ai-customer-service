"""Explicit smoke/full training. Frozen test set is never loaded here."""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .process import LABELS, tokenize_record


def train(root, run_type, run_name=None):
    import numpy as np
    import torch
    from datasets import Dataset
    from seqeval.metrics import f1_score, precision_score, recall_score
    from seqeval.scheme import IOB2
    from torch.utils.tensorboard import SummaryWriter
    from transformers import (
        AutoModelForTokenClassification,
        AutoTokenizer,
        DataCollatorForTokenClassification,
        Trainer,
        TrainingArguments,
        set_seed,
    )
    from transformers.integrations import TensorBoardCallback

    root = Path(root)
    base = root / "artifacts/local/models/bert-base-chinese"
    split = root / "data/private/ner-v1"
    name = run_name or f"ner-{run_type}"
    if not name.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Run name must contain only letters, digits, - or _")
    output = root / "artifacts/local" / name
    if output.exists():
        raise FileExistsError("Choose a fresh versioned output; existing training must not be overwritten")
    output.mkdir(parents=True)
    start = datetime.now(timezone.utc)
    set_seed(42)
    torch.set_num_threads(6)
    tokenizer = AutoTokenizer.from_pretrained(base, local_files_only=True, use_fast=True)
    if not tokenizer.is_fast:
        raise ValueError("Fast tokenizer required")
    dataset = {}
    for name in ("train", "validation"):
        content = (split / f"{name}.json").read_bytes()
        manifest = json.loads((split / "manifest.json").read_text(encoding="utf-8"))
        if hashlib.sha256(content).hexdigest() != manifest["splits"][name]["sha256"]:
            raise ValueError("Frozen split hash changed")
        rows = json.loads(content)
        if run_type == "smoke":
            rows = rows[:8]
        dataset[name] = Dataset.from_list([tokenize_record(tokenizer, row) for row in rows])
    model = AutoModelForTokenClassification.from_pretrained(
        base,
        local_files_only=True,
        num_labels=3,
        id2label=dict(enumerate(LABELS)),
        label2id={v: k for k, v in enumerate(LABELS)},
    )

    def metrics(result):
        pred, gold = result
        pred = np.argmax(pred, axis=-1)
        actual = [[LABELS[int(v)] for v in ys if v != -100] for ys in gold]
        inferred = [
            [LABELS[int(p)] for p, y in zip(ps, ys, strict=True) if y != -100]
            for ps, ys in zip(pred, gold, strict=True)
        ]
        return {
            name: fn(actual, inferred, mode="strict", scheme=IOB2, zero_division=0)
            for name, fn in [("precision", precision_score), ("recall", recall_score), ("f1", f1_score)]
        }

    smoke = run_type == "smoke"
    args = TrainingArguments(
        output_dir=str(output / "checkpoints"),
        num_train_epochs=10,
        max_steps=2 if smoke else -1,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        learning_rate=5e-5,
        weight_decay=0.0,
        logging_steps=1 if smoke else 20,
        eval_strategy="steps",
        eval_steps=1 if smoke else 20,
        save_strategy="steps",
        save_steps=1 if smoke else 20,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        seed=42,
        data_seed=42,
        dataloader_num_workers=0,
        report_to=[],
        fp16=False,
        bf16=False,
        use_cpu=not torch.cuda.is_available(),
        disable_tqdm=True,
    )
    provenance = {
        "run_type": run_type,
        "started_at": start.isoformat(),
        "sys.executable": sys.executable,
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "torch": torch.__version__,
        "seed": 42,
        "base_model": json.loads((base / "download_provenance.json").read_text(encoding="utf-8"))
        if (base / "download_provenance.json").exists()
        else str(base),
        "split_manifest_sha256": hashlib.sha256((split / "manifest.json").read_bytes()).hexdigest(),
        "split_counts": {k: len(v) for k, v in dataset.items()},
        "mixed_precision": False,
        "test_set_loaded": False,
        "validation_metric": "seqeval strict IOB2 entity F1",
        "alignment_strategy": "character-words-word-ids-v1",
        "truncation": "refused",
        "reproducibility": "fixed seed; GPU floating point results can vary by driver/hardware",
        "arguments": args.to_dict(),
    }
    (output / "run.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        data_collator=DataCollatorForTokenClassification(tokenizer),
        processing_class=tokenizer,
        compute_metrics=metrics,
        callbacks=[TensorBoardCallback(tb_writer=SummaryWriter(str(output / "tensorboard")))],
    )
    result = trainer.train()
    best = output / "best_model"
    trainer.save_model(str(best))
    tokenizer.save_pretrained(best)
    trainer.save_state()
    provenance.update(
        ended_at=datetime.now(timezone.utc).isoformat(),
        elapsed_seconds=(datetime.now(timezone.utc) - start).total_seconds(),
        global_step=trainer.state.global_step,
        epochs_completed=trainer.state.epoch,
        best_checkpoint=trainer.state.best_model_checkpoint,
        best_validation_f1=trainer.state.best_metric,
        train_metrics=result.metrics,
        model_sha256=hashlib.sha256((best / "model.safetensors").read_bytes()).hexdigest(),
        dependency_lock_sha256=hashlib.sha256(
            (root / "envs/locks/public/public-pip-win64.txt").read_bytes()
        ).hexdigest(),
    )
    (best / "training_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    (output / "result.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "run_type": run_type,
                "global_step": trainer.state.global_step,
                "best_validation_f1": trainer.state.best_metric,
                "output": str(best),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(os.environ.get("ECOMMERCE_ROOT", Path.cwd())))
    parser.add_argument("--run-type", choices=["smoke", "full"], required=True)
    parser.add_argument("--run-name")
    args = parser.parse_args()
    train(args.root, args.run_type, args.run_name)
