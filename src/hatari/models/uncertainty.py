"""Confidence intervals by bootstrap of message groups.

Messages that differ only by their digits share a group, and a group is
resampled as a whole. Resampling single messages would treat near-duplicates
as independent and give intervals that are too narrow.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score

DRAWS = 2000
SEED = 0
METRICS = {
    "precision": lambda truth, predicted: precision_score(truth, predicted, zero_division=0),
    "recall": lambda truth, predicted: recall_score(truth, predicted, zero_division=0),
    "f1": lambda truth, predicted: f1_score(truth, predicted, zero_division=0),
}


def _group_index(groups) -> tuple[np.ndarray, list[np.ndarray]]:
    labels, inverse = np.unique(np.asarray(groups).astype(str), return_inverse=True)
    members = [np.flatnonzero(inverse == position) for position in range(len(labels))]
    return labels, members


def grouped_bootstrap(truth, predicted, groups, draws: int = DRAWS, seed: int = SEED, level: float = 0.95) -> dict:
    """Percentile interval of precision, recall and F1 when whole groups are resampled."""
    truth = np.asarray(truth, dtype=bool)
    predicted = np.asarray(predicted, dtype=bool)
    _, members = _group_index(groups)
    generator = np.random.default_rng(seed)
    samples = {name: np.empty(draws) for name in METRICS}
    for draw in range(draws):
        chosen = generator.integers(0, len(members), len(members))
        index = np.concatenate([members[position] for position in chosen])
        for name, metric in METRICS.items():
            samples[name][draw] = metric(truth[index], predicted[index])
    tail = (1 - level) / 2 * 100
    return {name: (float(np.percentile(values, tail)), float(np.percentile(values, 100 - tail)))
            for name, values in samples.items()}


def paired_difference(truth, first, second, groups, metric: str = "f1", draws: int = DRAWS, seed: int = SEED,
                      level: float = 0.95) -> dict:
    """Interval of the difference of a metric between two classifiers on the same messages."""
    truth = np.asarray(truth, dtype=bool)
    first, second = np.asarray(first, dtype=bool), np.asarray(second, dtype=bool)
    _, members = _group_index(groups)
    generator = np.random.default_rng(seed)
    function = METRICS[metric]
    differences = np.empty(draws)
    for draw in range(draws):
        chosen = generator.integers(0, len(members), len(members))
        index = np.concatenate([members[position] for position in chosen])
        differences[draw] = function(truth[index], first[index]) - function(truth[index], second[index])
    tail = (1 - level) / 2 * 100
    observed = function(truth, first) - function(truth, second)
    return {"difference": float(observed), "low": float(np.percentile(differences, tail)),
            "high": float(np.percentile(differences, 100 - tail))}
