from scripts.profiles import write_initial_profiles, load_all_profiles, validate_profile


def test_initial_profiles_valid(tmp_path, monkeypatch):
    # Riusa la directory profili reale della skill
    created = write_initial_profiles(overwrite=False)
    profs = load_all_profiles()
    expected = {"de_natura_sonorum", "kits_beach_soundwalk", "presque_rien", "great_animal_orchestra"}
    assert expected.issubset(set(profs.keys())), f"mancano profili: {expected - set(profs.keys())}"
    for pid in expected:
        errors = validate_profile(profs[pid])
        assert not errors, f"profilo {pid} ha errori: {errors}"
        assert profs[pid]["source_type"] == "literature_based"
