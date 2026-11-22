import numpy as np

from hatari.models.uncertainty import grouped_bootstrap, paired_difference


def test_interval_contains_the_observed_value_and_is_reproducible():
    rng = np.random.default_rng(1)
    truth = rng.random(400) < 0.3
    predicted = np.where(rng.random(400) < 0.9, truth, ~truth)
    groups = np.arange(400) // 2

    first = grouped_bootstrap(truth, predicted, groups, draws=300)
    second = grouped_bootstrap(truth, predicted, groups, draws=300)

    assert first == second
    low, high = first["f1"]
    observed = 2 * (truth & predicted).sum() / (truth.sum() + predicted.sum())
    assert low <= observed <= high


def test_perfect_predictions_give_a_degenerate_interval():
    truth = np.array([True, False] * 20)
    result = grouped_bootstrap(truth, truth, np.arange(40), draws=100)
    assert result["f1"] == (1.0, 1.0)


def test_whole_groups_widen_the_interval():
    rng = np.random.default_rng(2)
    base_truth = rng.random(60) < 0.4
    base_predicted = np.where(rng.random(60) < 0.8, base_truth, ~base_truth)
    truth, predicted = np.repeat(base_truth, 10), np.repeat(base_predicted, 10)

    single = grouped_bootstrap(truth, predicted, np.arange(600), draws=400)
    grouped = grouped_bootstrap(truth, predicted, np.repeat(np.arange(60), 10), draws=400)

    assert grouped["f1"][1] - grouped["f1"][0] > single["f1"][1] - single["f1"][0]


def test_paired_difference_of_identical_classifiers_is_zero():
    truth = np.array([True, False, True, True, False] * 10)
    predicted = np.array([True, False, False, True, False] * 10)
    result = paired_difference(truth, predicted, predicted, np.arange(50), draws=200)
    assert result == {"difference": 0.0, "low": 0.0, "high": 0.0}
