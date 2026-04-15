from scripts.comparison import (
    extract_vector, extract_profile_vector, compare_to_profile, rank_profiles
)
from scripts.profiles import write_initial_profiles, load_all_profiles


def _fake_summary(centroid=1800, flatness=0.2, dr=30, lufs=-24, ndsi=0.0, onsets=2.0,
                   bands_pct=None):
    bands = bands_pct or {
        "Sub-bass": 3, "Bass": 15, "Low-mid": 15, "Mid": 25,
        "High-mid": 20, "Presence": 15, "Brilliance": 7,
    }
    return {
        "spectral": {
            "timbre": {"spectral_centroid_hz": centroid, "spectral_flatness": flatness},
            "bands_schafer": {k: {"energy_pct": v, "energy_db": 0, "range_hz": [0, 0]} for k, v in bands.items()},
            "onsets": {"events_per_sec": onsets},
        },
        "technical": {
            "levels": {"dynamic_range_db": dr},
            "lufs": {"integrated_lufs": lufs},
        },
        "ecoacoustic": {"ndsi": {"ndsi": ndsi}},
    }


def test_compare_to_profile():
    write_initial_profiles(overwrite=False)
    profs = load_all_profiles()
    prof = profs["de_natura_sonorum"]
    summary = _fake_summary()
    r = compare_to_profile(summary, prof)
    assert 0 <= r["cosine_distance"] <= 2
    assert "narrative_it" in r
    assert r["profile_id"] == "de_natura_sonorum"


def test_rank_profiles():
    write_initial_profiles(overwrite=False)
    profs = load_all_profiles()
    summary = _fake_summary()
    rank = rank_profiles(summary, profs)
    assert len(rank) == len(profs)
    # Deve essere ordinato per distanza crescente
    dists = [r["cosine_distance"] for r in rank]
    assert dists == sorted(dists)
