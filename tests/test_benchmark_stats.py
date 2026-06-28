from __future__ import annotations

import math

from scripts import benchmark_stats as bs


def test_mean_ci_basic():
    ci = bs.mean_ci([50, 52, 48, 51, 49])
    assert ci.n == 5
    assert abs(ci.mean - 50.0) < 1e-6
    # CI simmetrico attorno alla media e strettamente piu largo della media puntuale
    assert ci.lo < ci.mean < ci.hi
    assert abs((ci.mean - ci.lo) - (ci.hi - ci.mean)) < 1e-6


def test_mean_ci_degenerate():
    assert bs.mean_ci([]).n == 0
    one = bs.mean_ci([42.0])
    assert one.n == 1 and one.lo == one.hi == 42.0 and one.sd == 0.0


def test_paired_ttest_improvement_significant():
    old = [40, 42, 38, 45, 41, 39]
    new = [55, 57, 52, 60, 54, 56]
    pt = bs.paired_ttest(old, new)
    assert pt.n == 6
    assert pt.mean_diff > 10
    assert pt.t > 0
    assert pt.p < 0.05
    assert pt.significant is True
    assert pt.cohen_dz > 0


def test_paired_ttest_no_difference():
    pt = bs.paired_ttest([50, 50, 50], [50, 50, 50])
    assert pt.significant is False
    assert pt.p == 1.0
    assert pt.cohen_dz == 0.0


def test_paired_ttest_too_few():
    pt = bs.paired_ttest([50], [60])
    assert pt.significant is False
    assert pt.n == 1
