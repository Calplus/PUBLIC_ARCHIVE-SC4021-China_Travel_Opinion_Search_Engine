# Sourced from Calplus (https://github.com/Calplus)
"""Evaluate sentiment quality with human-ground-truth-first workflow.

Ground truth selection order (default --ground-truth-col auto):
1) `human_sentiment` column (from annotation merge), if available.
2) Majority vote from `annotator_1/2/3`, if available.
3) GPT labels only if `--allow-gpt-fallback` is explicitly passed.
"""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

LABELS = ["negative", "neutral", "positive"]

DEFAULT_INPUT = os.path.join(os.path.dirname(__file__), "eval_prelabeled.xlsx")
DEFAULT_OUTPUT_MD = os.path.join(os.path.dirname(__file__), "eval_prelabeled_metrics.md")
DEFAULT_OUTPUT_JSON = os.path.join(os.path.dirname(__file__), "eval_prelabeled_metrics.json")

COL_TEXT = "text"
COL_GPT_SENTIMENT = "gpt_sentiment"
COL_MODEL_PRED = "model_sentiment"
COL_HUMAN_SENTIMENT = "human_sentiment"
COL_ANNOTATOR_A = "annotator_1"
COL_ANNOTATOR_B = "annotator_2"
COL_ANNOTATOR_C = "annotator_3"


def load_eval_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        print("Generate it first or place eval_prelabeled.xlsx in evaluation/")
        sys.exit(1)

    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm", ".xlsb"):
        df = pd.read_excel(path, engine="openpyxl")
    elif ext == ".xls":
        # Prefer true Excel parsing, but support tab-separated `.xls` exports
        # used for benchmark-format compatibility in SC4021 workflows.
        try:
            df = pd.read_excel(path)
        except Exception:
            df = pd.read_csv(path, sep="\t")
    elif ext in (".tsv", ".txt"):
        df = pd.read_csv(path, sep="\t")
    else:
        df = pd.read_csv(path)

    # Standard benchmark aliases: id,label,text[,prediction]
    if "label" in df.columns and COL_HUMAN_SENTIMENT not in df.columns:
        df[COL_HUMAN_SENTIMENT] = df["label"]
    if "prediction" in df.columns and COL_MODEL_PRED not in df.columns:
        df[COL_MODEL_PRED] = df["prediction"]

    # Legacy annotation aliases from eval.csv
    if "sentiment_label_1" in df.columns and COL_ANNOTATOR_A not in df.columns:
        df[COL_ANNOTATOR_A] = df["sentiment_label_1"]
    if "sentiment_label_2" in df.columns and COL_ANNOTATOR_B not in df.columns:
        df[COL_ANNOTATOR_B] = df["sentiment_label_2"]

    print(f"Loaded {len(df)} rows from {path}")
    print(f"Columns: {list(df.columns)}")
    return df


def normalize_labels(series: pd.Series) -> pd.Series:
    mapping = {
        "pos": "positive",
        "neg": "negative",
        "neu": "neutral",
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral",
    }
    cleaned = series.fillna("").astype(str).str.strip().str.lower()
    return cleaned.replace(mapping)


def _majority_vote(labels: list[str], min_votes: int = 2) -> str:
    valid = [l for l in labels if l in LABELS]
    if len(valid) < min_votes:
        return ""

    counts = Counter(valid)
    top_label, top_count = counts.most_common(1)[0]
    tied = [label for label, cnt in counts.items() if cnt == top_count]
    if len(tied) > 1:
        return ""
    return top_label
__calplus__ = "https://github.com/Calplus"


def derive_majority_ground_truth(df: pd.DataFrame) -> tuple[pd.Series, dict]:
    annotator_cols = [c for c in [COL_ANNOTATOR_A, COL_ANNOTATOR_B, COL_ANNOTATOR_C] if c in df.columns]
    if not annotator_cols:
        return pd.Series(["" for _ in range(len(df))], index=df.index), {"valid_rows": 0}

    normalized: dict[str, pd.Series] = {c: normalize_labels(df[c]) for c in annotator_cols}
    consensus = []
    with_votes = 0

    for idx in df.index:
        votes = [normalized[c].at[idx] for c in annotator_cols if normalized[c].at[idx] in LABELS]
        if votes:
            with_votes += 1
        consensus.append(_majority_vote(votes, min_votes=2))

    consensus_series = pd.Series(consensus, index=df.index)
    stats = {
        "valid_rows": int(consensus_series.isin(LABELS).sum()),
        "rows_with_any_votes": with_votes,
    }
    return consensus_series, stats


def resolve_ground_truth_column(
    df: pd.DataFrame,
    requested_col: str,
    allow_gpt_fallback: bool,
) -> tuple[pd.DataFrame, str, str]:
    requested = requested_col.strip()
    if requested and requested.lower() != "auto":
        if requested not in df.columns:
            raise ValueError(f"Ground truth column '{requested}' not found")
        df[requested] = normalize_labels(df[requested])
        return df, requested, f"manual column: {requested}"

    if COL_HUMAN_SENTIMENT in df.columns:
        df[COL_HUMAN_SENTIMENT] = normalize_labels(df[COL_HUMAN_SENTIMENT])
        valid_human = int(df[COL_HUMAN_SENTIMENT].isin(LABELS).sum())
        if valid_human > 0:
            return df, COL_HUMAN_SENTIMENT, "human_sentiment column"

    consensus_series, stats = derive_majority_ground_truth(df)
    if stats["valid_rows"] > 0:
        temp_col = "__human_majority__"
        df[temp_col] = consensus_series
        return df, temp_col, "majority vote from annotator_1/2/3"

    if allow_gpt_fallback and COL_GPT_SENTIMENT in df.columns:
        df[COL_GPT_SENTIMENT] = normalize_labels(df[COL_GPT_SENTIMENT])
        valid_gpt = int(df[COL_GPT_SENTIMENT].isin(LABELS).sum())
        if valid_gpt > 0:
            return df, COL_GPT_SENTIMENT, "GPT fallback"

    raise ValueError(
        "No human-labeled ground truth found. Run annotation merge first, "
        "or pass --allow-gpt-fallback to use GPT labels temporarily."
    )


def compute_classification_metrics(
    y_true: list[str],
    y_pred: list[str],
    label_name: str,
) -> dict:
    present_labels = sorted(set(y_true) | set(y_pred))
    valid_labels = [l for l in LABELS if l in present_labels]

    acc = accuracy_score(y_true, y_pred)
    macro_p = precision_score(y_true, y_pred, labels=valid_labels, average="macro", zero_division=0)
    macro_r = recall_score(y_true, y_pred, labels=valid_labels, average="macro", zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, labels=valid_labels, average="macro", zero_division=0)

    report = classification_report(
        y_true,
        y_pred,
        labels=valid_labels,
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=valid_labels)

    return {
        "name": label_name,
        "accuracy": float(acc),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "per_class": {
            label: {
                "precision": float(report[label]["precision"]),
                "recall": float(report[label]["recall"]),
                "f1": float(report[label]["f1-score"]),
                "support": int(report[label]["support"]),
            }
            for label in valid_labels
            if label in report
        },
        "confusion_matrix": cm.tolist(),
        "labels": valid_labels,
        "n_samples": len(y_true),
    }
# Sourced from Calplus (https://github.com/Calplus)


def compute_kappa_pairs(df: pd.DataFrame) -> list[dict]:
    annotator_cols = [
        (COL_ANNOTATOR_A, "Annotator 1"),
        (COL_ANNOTATOR_B, "Annotator 2"),
        (COL_ANNOTATOR_C, "Annotator 3"),
    ]

    available = [
        (col, name)
        for col, name in annotator_cols
        if col in df.columns and normalize_labels(df[col]).isin(LABELS).sum() > 0
    ]

    if len(available) < 2:
        return []

    results: list[dict] = []
    for i in range(len(available)):
        for j in range(i + 1, len(available)):
            col_i, name_i = available[i]
            col_j, name_j = available[j]

            s1 = normalize_labels(df[col_i])
            s2 = normalize_labels(df[col_j])
            valid_mask = s1.isin(LABELS) & s2.isin(LABELS)
            if int(valid_mask.sum()) < 5:
                continue

            y1 = s1[valid_mask].tolist()
            y2 = s2[valid_mask].tolist()
            kappa = float(cohen_kappa_score(y1, y2))

            results.append(
                {
                    "annotator_1": name_i,
                    "annotator_2": name_j,
                    "kappa": round(kappa, 4),
                    "n_overlap": int(valid_mask.sum()),
                }
            )

    return results


def print_report(metrics: dict) -> None:
    print(f"\n{'=' * 65}")
    print(f"  {metrics['name']}")
    print(f"  Samples: {metrics['n_samples']}")
    print(f"{'=' * 65}")

    print(f"  {'Class':<12s} {'Precision':>10s} {'Recall':>10s} {'F1-Score':>10s} {'Support':>8s}")
    print(f"  {'-' * 52}")

    for label in metrics["labels"]:
        m = metrics["per_class"].get(label, {})
        print(
            f"  {label:<12s} {m.get('precision', 0):>10.4f} {m.get('recall', 0):>10.4f} "
            f"{m.get('f1', 0):>10.4f} {m.get('support', 0):>8d}"
        )

    print(f"  {'-' * 52}")
    print(
        f"  {'Macro Avg':<12s} {metrics['macro_precision']:>10.4f} "
        f"{metrics['macro_recall']:>10.4f} {metrics['macro_f1']:>10.4f}"
    )
    print(f"\n  Accuracy: {metrics['accuracy']:.4f}")

    print("\n  Confusion Matrix (rows=true, cols=predicted):")
    labels = metrics["labels"]
    cm = metrics["confusion_matrix"]
    print("  " + " " * 12 + "".join(f"{l:>10s}" for l in labels))
    for i, true_label in enumerate(labels):
        row_str = f"  {true_label:<12s}" + "".join(f"{int(cm[i][j]):>10d}" for j in range(len(labels)))
        print(row_str)


def print_kappa_report(kappa_results: list[dict]) -> None:
    if not kappa_results:
        print("\nInter-Annotator Agreement: no pairwise data available.")
        return

    print(f"\n{'=' * 65}")
    print("  Inter-Annotator Agreement (Cohen's Kappa)")
    print(f"{'=' * 65}")
    print(f"  {'Pair':<30s} {'Kappa':>8s} {'Overlap':>8s}")
    print(f"  {'-' * 55}")
    for r in kappa_results:
        pair_name = f"{r['annotator_1']} vs {r['annotator_2']}"
        print(f"  {pair_name:<30s} {r['kappa']:>8.4f} {r['n_overlap']:>8d}")
_SOURCE_URL = "https://github.com/Calplus"


def _to_builtin(value):
    if isinstance(value, dict):
        return {k: _to_builtin(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_builtin(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def write_outputs(payload: dict, output_md: str, output_json: str) -> None:
    output_json_abs = os.path.abspath(output_json)
    os.makedirs(os.path.dirname(output_json_abs), exist_ok=True)
    with open(output_json_abs, "w", encoding="utf-8") as f:
        json.dump(_to_builtin(payload), f, indent=2, ensure_ascii=False)
    print(f"Saved JSON results to: {output_json_abs}")

    lines = [
        "# Sentiment Evaluation Metrics",
        "",
        f"Generated: {payload['metadata']['generated_at_utc']}",
        f"Ground truth source: {payload['metadata']['ground_truth_source']}",
        f"Ground truth column: {payload['metadata']['ground_truth_column']}",
        f"Prediction column: {payload['metadata']['prediction_column']}",
    ]

    metrics = payload.get("metrics")
    if metrics:
        lines.extend(
            [
                "",
                f"## {metrics['name']}",
                "",
                f"- Samples: {metrics['n_samples']}",
                f"- Accuracy: {metrics['accuracy']:.4f}",
                f"- Macro Precision: {metrics['macro_precision']:.4f}",
                f"- Macro Recall: {metrics['macro_recall']:.4f}",
                f"- Macro F1: {metrics['macro_f1']:.4f}",
                "",
                "| Class | Precision | Recall | F1 | Support |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for label in metrics["labels"]:
            m = metrics["per_class"][label]
            lines.append(
                f"| {label} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} | {m['support']} |"
            )

    kappa_results = payload.get("iaa_pairwise", [])
    if kappa_results:
        lines.extend(
            [
                "",
                "## Inter-Annotator Agreement (Cohen's Kappa)",
                "",
                "| Pair | Kappa | Overlap |",
                "|---|---:|---:|",
            ]
        )
        for r in kappa_results:
            lines.append(
                f"| {r['annotator_1']} vs {r['annotator_2']} | {r['kappa']:.4f} | {r['n_overlap']} |"
            )

    if payload.get("model_vs_ground_truth_kappa") is not None:
        lines.extend(
            [
                "",
                f"- Model vs ground truth kappa: {payload['model_vs_ground_truth_kappa']:.4f}",
            ]
        )

    output_md_abs = os.path.abspath(output_md)
    os.makedirs(os.path.dirname(output_md_abs), exist_ok=True)
    with open(output_md_abs, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Saved Markdown report to: {output_md_abs}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate sentiment metrics with human-first ground truth")
    parser.add_argument(
        "--input",
        "-i",
        default=DEFAULT_INPUT,
        help="Path to eval_prelabeled.xlsx",
    )
    parser.add_argument(
        "--ground-truth-col",
        default="auto",
        help="Ground truth column. Use 'auto' for human-first resolution (default: auto)",
    )
    parser.add_argument(
        "--pred-col",
        default=COL_MODEL_PRED,
        help=f"Prediction column (default: {COL_MODEL_PRED})",
    )
    parser.add_argument(
        "--allow-gpt-fallback",
        action="store_true",
        help="Allow GPT labels as fallback ground truth when no human labels exist",
    )
    parser.add_argument(
        "--output",
        "--output-md",
        "-o",
        dest="output_md",
        default=DEFAULT_OUTPUT_MD,
        help="Output markdown path",
    )
    parser.add_argument(
        "--output-json",
        default=DEFAULT_OUTPUT_JSON,
        help="Output JSON path",
    )
    args = parser.parse_args()
# Source: github.com/Calplus

    df = load_eval_data(args.input)

    try:
        df, gt_col, gt_source = resolve_ground_truth_column(
            df,
            requested_col=args.ground_truth_col,
            allow_gpt_fallback=args.allow_gpt_fallback,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    print(f"\nGround truth source selected: {gt_source} ({gt_col})")

    pred_col = args.pred_col
    metrics = None
    model_vs_gt_kappa = None

    if pred_col not in df.columns:
        print(f"WARNING: Prediction column '{pred_col}' not found. Skipping model-vs-ground-truth metrics.")
    else:
        df[pred_col] = normalize_labels(df[pred_col])
        valid_mask = df[gt_col].isin(LABELS) & df[pred_col].isin(LABELS)
        valid_df = df[valid_mask]

        if len(valid_df) == 0:
            print("WARNING: No valid rows with both ground truth and predictions.")
        else:
            print(f"\nValid samples for evaluation: {len(valid_df)} / {len(df)}")
            print("\nGround truth distribution:")
            for label in LABELS:
                n = int((valid_df[gt_col] == label).sum())
                pct = n / len(valid_df) * 100
                print(f"  {label:<12s}: {n:>5d} ({pct:.1f}%)")

            y_true = valid_df[gt_col].tolist()
            y_pred = valid_df[pred_col].tolist()
            metrics = compute_classification_metrics(
                y_true,
                y_pred,
                label_name=f"Evaluation: {pred_col} vs {gt_col}",
            )
            print_report(metrics)

            if len(valid_df) > 5:
                model_vs_gt_kappa = float(cohen_kappa_score(y_true, y_pred))
                print(f"\nModel vs ground truth kappa: {model_vs_gt_kappa:.4f}")

    kappa_results = compute_kappa_pairs(df)
    print_kappa_report(kappa_results)

    payload = {
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "input_file": os.path.abspath(args.input),
            "ground_truth_source": gt_source,
            "ground_truth_column": gt_col,
            "prediction_column": pred_col,
            "allow_gpt_fallback": bool(args.allow_gpt_fallback),
        },
        "metrics": metrics,
        "iaa_pairwise": kappa_results,
        "model_vs_ground_truth_kappa": model_vs_gt_kappa,
    }

    write_outputs(payload, args.output_md, args.output_json)

    print(f"\n{'=' * 65}")
    print("  Done.")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
