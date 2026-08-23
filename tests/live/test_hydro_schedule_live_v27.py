from phasenav_natural_code import hydro_schedule_v27 as s


def test_live_registry_contains_v020_execution_operators():
    ops, _ = s.load_live_operator_vectors()
    assert {
        "DIFFERENCE",
        "CONDITION",
        "COMPOSITION",
        "NEGATION",
        "ORDER",
        "TRANSFORM",
    } <= set(ops)
