"""Statistica del benchmark (v0.13).

Aggrega N run per versione e confronta versioni con rigore - media, intervallo
di confidenza al 95% (t-Student) e paired t-test fra versioni accoppiato per
traccia, con dimensione dell'effetto (Cohen's d_z per dati appaiati).

Lo scopo e dichiarare che un miglioramento di score fra due versioni della skill
non e rumore - l'agente e stocastico, quindi un solo run non basta. `scipy.stats`
e gia una dipendenza, niente librerie nuove.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from statistics import mean, stdev


@dataclass
class MeanCI:
    n: int
    mean: float
    sd: float
    lo: float
    hi: float
    conf: float


def mean_ci(values, conf: float = 0.95) -> MeanCI:
    """Media e intervallo di confidenza t-Student al livello `conf`."""
    vals = [float(v) for v in values]
    n = len(vals)
    if n == 0:
        return MeanCI(0, 0.0, 0.0, 0.0, 0.0, conf)
    m = mean(vals)
    if n == 1:
        return MeanCI(1, round(m, 4), 0.0, round(m, 4), round(m, 4), conf)
    sd = stdev(vals)
    from scipy import stats
    se = sd / math.sqrt(n)
    half = se * float(stats.t.ppf((1 + conf) / 2.0, n - 1))
    return MeanCI(n, round(m, 4), round(sd, 4), round(m - half, 4), round(m + half, 4), conf)


@dataclass
class PairedTest:
    n: int
    mean_diff: float       # media (new - old)
    t: float
    p: float
    dof: int
    cohen_dz: float
    significant: bool


def paired_ttest(old, new, alpha: float = 0.05) -> PairedTest:
    """Paired t-test fra due versioni, accoppiato per traccia (new vs old).

    `old` e `new` sono liste di score per-traccia nello STESSO ordine. Restituisce
    t, p, gradi di liberta, Cohen's d_z e se il miglioramento e significativo.
    """
    a = [float(x) for x in old]
    b = [float(x) for x in new]
    if len(a) != len(b) or len(a) < 2:
        return PairedTest(len(a), 0.0, 0.0, 1.0, max(0, len(a) - 1), 0.0, False)
    diffs = [bi - ai for ai, bi in zip(a, b)]
    md = mean(diffs)
    sdd = stdev(diffs) if len(diffs) > 1 else 0.0
    if sdd == 0.0:
        # nessuna varianza nelle differenze: t non definito, nessuna significativita
        return PairedTest(len(a), round(md, 4), 0.0, 1.0, len(a) - 1, 0.0, False)
    from scipy import stats
    res = stats.ttest_rel(b, a)
    t = float(res.statistic)
    p = float(res.pvalue)
    if math.isnan(t) or math.isnan(p):
        return PairedTest(len(a), round(md, 4), 0.0, 1.0, len(a) - 1, 0.0, False)
    dz = md / sdd
    return PairedTest(len(a), round(md, 4), round(t, 4), round(p, 5),
                      len(a) - 1, round(dz, 4), bool(p < alpha))


def to_dict(obj) -> dict:
    return asdict(obj)
