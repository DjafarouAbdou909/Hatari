"""Robustness to obfuscated messages, preregistered in docs/research_obfuscation.md.

Usage, from the repository root, after python -m hatari.data.corpus:

    python -m hatari.research.obfuscation

or, to recompute only the hypothesis intervals from saved predictions,
python -m hatari.research.obfuscation tests. Writes data/interim/obfuscation_predictions.csv.gz, one row per English held-out
message, reports/obfuscation_results.csv and reports/obfuscation_hypotheses.csv.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import precision_score, recall_score

from hatari.analysis.signals import MEDIUM, STRONG, detect
from hatari.models.candidates import Candidate, build, decision_scores, default_threshold
from hatari.models.selection import REPORTS_DIR, fold_assignment, load_training
from hatari.models.uncertainty import DRAWS, _group_index, paired_difference
from hatari.text.defence import defend

INTERIM_DIR = Path(__file__).resolve().parents[3] / "data" / "interim"
SEED = 0
CYRILLIC = {"a": "а", "c": "с", "e": "е", "i": "і", "o": "о", "p": "р", "x": "х", "y": "у",
            "A": "А", "C": "С", "E": "Е", "I": "І", "O": "О", "P": "Р", "X": "Х", "Y": "У"}
DIGITS = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "A": "4", "E": "3", "I": "1", "O": "0", "S": "5"}
ZERO_WIDTH_SPACE = "​"
PERTURBATIONS = ["P0", "P1", "P2", "P3", "P4"]
SYSTEMS = {"M": Candidate("SVM", "mask", 1.0), "C": Candidate("SVM-char", "normalize", 0.1)}


def substitute(text: str, table: dict, rate: float, rng: np.random.Generator) -> str:
    return "".join(table[c] if c in table and rng.random() < rate else c for c in text)


def invisible(text: str, rate: float, rng: np.random.Generator) -> str:
    return "".join(c + ZERO_WIDTH_SPACE if c.isalpha() and rng.random() < rate else c for c in text)


def separate(text: str, rate: float, rng: np.random.Generator) -> str:
    def dotted(word: str) -> str:
        return ".".join(word) if len(word) >= 4 and word.isalpha() and rng.random() < rate else word
    return " ".join(dotted(word) for word in text.split(" "))


def perturb(text: str, code: str, rng: np.random.Generator) -> str:
    if code == "P0":
        return text
    if code == "P1":
        return substitute(text, CYRILLIC, 0.3, rng)
    if code == "P2":
        return invisible(text, 0.2, rng)
    if code == "P3":
        return substitute(text, DIGITS, 0.3, rng)
    if code == "P4":
        return separate(text, 0.2, rng)
    raise ValueError(code)


def perturbed_texts(frame: pd.DataFrame, seed: int = SEED) -> dict[str, pd.Series]:
    """The same perturbed version of every suspicious message for every system. Legitimate ones are unchanged."""
    result = {}
    for position, code in enumerate(PERTURBATIONS):
        rng = np.random.default_rng([seed, position])
        result[code] = pd.Series([perturb(text, code, rng) if suspicious else text
                                  for text, suspicious in zip(frame["text"], frame["suspicious"])], index=frame.index)
    return result


def rules_flag(text: str) -> bool:
    return any(signal.strength in {STRONG, MEDIUM} for signal in detect(text))


def predictions(training: pd.DataFrame) -> pd.DataFrame:
    folds = fold_assignment(training)
    english = training[training["language"] == "en"]
    variants = perturbed_texts(english)
    rows = pd.DataFrame({"suspicious": english["suspicious"].astype(bool), "group": "en:" + english["group"].astype(str)},
                        index=english.index)
    for defended in [False, True]:
        prepare = defend if defended else (lambda text: text)
        texts = training["text"].map(prepare)
        for system, candidate in SYSTEMS.items():
            columns = {code: np.empty(len(english), dtype=bool) for code in PERTURBATIONS}
            for fold in np.unique(folds):
                train = folds != fold
                model = clone(build(candidate)).fit(texts[train], training.loc[train, "suspicious"].astype(bool))
                held = english.index[folds[english.index] == fold]
                positions = english.index.get_indexer(held)
                for code in PERTURBATIONS:
                    scores = decision_scores(model, variants[code].loc[held].map(prepare))
                    columns[code][positions] = scores > default_threshold(candidate)
            for code in PERTURBATIONS:
                rows[f"{system}_{'D' if defended else 'N'}_{code}"] = columns[code]
            print(f"system {system}, defence {defended} done", flush=True)
        for code in PERTURBATIONS:
            rows[f"R_{'D' if defended else 'N'}_{code}"] = variants[code].map(prepare).map(rules_flag).to_numpy()
    return rows


def results(rows: pd.DataFrame) -> pd.DataFrame:
    truth, groups = rows["suspicious"].to_numpy(), rows["group"].to_numpy()
    table = []
    for system in ["M", "C", "R"]:
        reference = rows[f"{system}_N_P0"].to_numpy()
        for defence in ["N", "D"]:
            for code in PERTURBATIONS:
                predicted = rows[f"{system}_{defence}_{code}"].to_numpy()
                loss = paired_difference(truth, reference, predicted, groups, metric="recall")
                table.append({"system": system, "defence": defence, "perturbation": code,
                              "recall": recall_score(truth, predicted), "precision": precision_score(truth, predicted),
                              "recall_loss": loss["difference"], "loss_low": loss["low"], "loss_high": loss["high"]})
    return pd.DataFrame(table)


def _bootstrap(statistic, truth, groups, draws: int = DRAWS, seed: int = SEED) -> tuple[float, float, float]:
    _, members = _group_index(groups)
    generator = np.random.default_rng(seed)
    values = np.empty(draws)
    for draw in range(draws):
        index = np.concatenate([members[position] for position in generator.integers(0, len(members), len(members))])
        values[draw] = statistic(index)
    everything = np.arange(len(truth))
    return float(statistic(everything)), float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def hypothesis_tests(rows: pd.DataFrame) -> pd.DataFrame:
    """Paired intervals for H2, loss of M minus loss of C, and for H4, precision change of M under the defence."""
    truth, groups = rows["suspicious"].to_numpy(), rows["group"].to_numpy()
    tests = []
    for code in ["P1", "P2", "P3"]:
        columns = {name: rows[name].to_numpy() for name in ["M_N_P0", f"M_N_{code}", "C_N_P0", f"C_N_{code}"]}

        def loss_gap(index, code=code, columns=columns):
            recall = {name: recall_score(truth[index], values[index]) for name, values in columns.items()}
            return (recall["M_N_P0"] - recall[f"M_N_{code}"]) - (recall["C_N_P0"] - recall[f"C_N_{code}"])

        value, low, high = _bootstrap(loss_gap, truth, groups)
        tests.append({"hypothesis": "H2", "perturbation": code, "statistic": "loss of M minus loss of C",
                      "value": value, "low": low, "high": high})
    without, with_defence = rows["M_N_P0"].to_numpy(), rows["M_D_P0"].to_numpy()

    def precision_change(index):
        return (precision_score(truth[index], with_defence[index], zero_division=0)
                - precision_score(truth[index], without[index], zero_division=0))

    value, low, high = _bootstrap(precision_change, truth, groups)
    tests.append({"hypothesis": "H4", "perturbation": "P0", "statistic": "precision of M with D minus without D",
                  "value": value, "low": low, "high": high})
    return pd.DataFrame(tests)


def main() -> None:
    rows = predictions(load_training())
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    rows.to_csv(INTERIM_DIR / "obfuscation_predictions.csv.gz")
    table = results(rows)
    REPORTS_DIR.mkdir(exist_ok=True)
    table.round(4).to_csv(REPORTS_DIR / "obfuscation_results.csv", index=False)
    print(table.round(3).to_string(index=False))
    tests = hypothesis_tests(rows)
    tests.round(4).to_csv(REPORTS_DIR / "obfuscation_hypotheses.csv", index=False)
    print(tests.round(4).to_string(index=False))


def tests_only() -> None:
    """Recompute the hypothesis intervals from the saved predictions, without retraining."""
    rows = pd.read_csv(INTERIM_DIR / "obfuscation_predictions.csv.gz", index_col=0)
    tests = hypothesis_tests(rows)
    tests.round(4).to_csv(REPORTS_DIR / "obfuscation_hypotheses.csv", index=False)
    print(tests.round(4).to_string(index=False))


if __name__ == "__main__":
    import sys

    tests_only() if sys.argv[1:] == ["tests"] else main()
