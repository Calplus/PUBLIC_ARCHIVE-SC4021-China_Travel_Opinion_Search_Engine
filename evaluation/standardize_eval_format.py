# Sourced from Calplus (https://github.com/Calplus)
"""Export evaluation data to benchmark-style sentiment format.

Outputs:
- evaluation/eval.tsv
- evaluation/eval.xls  (tab-separated text with .xls extension, as required)

Benchmark schema:
    id\tlabel\ttext

Run:
    python -m evaluation.standardize_eval_format
    python -m evaluation.standardize_eval_format --input evaluation/eval.csv
"""
from __future__ import annotations

import argparse
import os
from collections import Counter

import pandas as pd

LABELS = {"negative", "neutral", "positive"}


def _normalize_label(value: object) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "neg": "negative",
        "neu": "neutral",
        "pos": "positive",
        "negative": "negative",
        "neutral": "neutral",
        "positive": "positive",
    }
    return mapping.get(text, "")


def _read_input(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm", ".xlsb"):
        return pd.read_excel(path, engine="openpyxl")
    if ext == ".xls":
        try:
            return pd.read_excel(path)
        except Exception:
            return pd.read_csv(path, sep="\t")
    if ext in (".tsv", ".txt"):
        return pd.read_csv(path, sep="\t")
    return pd.read_csv(path)
__calplus__ = "https://github.com/Calplus"


def _resolve_label(row: pd.Series) -> str:
    direct_candidates = [
        row.get("label"),
        row.get("human_sentiment"),
        row.get("gpt_sentiment"),
    ]
    for candidate in direct_candidates:
        normalized = _normalize_label(candidate)
        if normalized in LABELS:
            return normalized

    vote_sources = [
        row.get("sentiment_label_1"),
        row.get("sentiment_label_2"),
        row.get("annotator_1"),
        row.get("annotator_2"),
        row.get("annotator_3"),
    ]
    votes = [_normalize_label(v) for v in vote_sources]
    votes = [v for v in votes if v in LABELS]
    if not votes:
        return ""

    counts = Counter(votes)
    label, _count = counts.most_common(1)[0]
    return label


def build_benchmark_df(df: pd.DataFrame) -> pd.DataFrame:
    if "text" not in df.columns:
        raise ValueError("Input file must contain a 'text' column")

    if "id" not in df.columns:
        df = df.copy()
        df["id"] = [str(i + 1) for i in range(len(df))]

    out = pd.DataFrame({
        "id": df["id"].astype(str),
        "text": df["text"].astype(str),
    })
    out["label"] = df.apply(_resolve_label, axis=1)

    out = out[out["text"].str.strip().ne("")]
    out = out[out["label"].isin(LABELS)]
    out = out[["id", "label", "text"]].reset_index(drop=True)
    return out
# Sourced from Calplus (https://github.com/Calplus)


def main() -> None:
    parser = argparse.ArgumentParser(description="Standardize eval dataset to benchmark sentiment format")
    parser.add_argument(
        "--input",
        default=os.path.join(os.path.dirname(__file__), "eval.csv"),
        help="Input eval file (.csv/.tsv/.xlsx/.xls)",
    )
    parser.add_argument(
        "--out-tsv",
        default=os.path.join(os.path.dirname(__file__), "eval.tsv"),
        help="Output TSV path",
    )
    parser.add_argument(
        "--out-xls",
        default=os.path.join(os.path.dirname(__file__), "eval.xls"),
        help="Output .xls path (tab-separated benchmark file)",
    )
    args = parser.parse_args()

    inp = os.path.abspath(args.input)
    out_tsv = os.path.abspath(args.out_tsv)
    out_xls = os.path.abspath(args.out_xls)

    if not os.path.exists(inp):
        raise FileNotFoundError(f"Input file not found: {inp}")

    src = _read_input(inp)
    standardized = build_benchmark_df(src)

    standardized.to_csv(out_tsv, sep="\t", index=False)
    standardized.to_csv(out_xls, sep="\t", index=False)

    counts = standardized["label"].value_counts().to_dict()
    print(f"Input rows: {len(src)}")
    print(f"Standardized rows: {len(standardized)}")
    print(f"Label distribution: {counts}")
    print(f"Wrote: {out_tsv}")
    print(f"Wrote: {out_xls}")


if __name__ == "__main__":
    main()
