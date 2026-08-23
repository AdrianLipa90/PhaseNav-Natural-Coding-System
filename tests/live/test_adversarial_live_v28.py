from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from phasenav_natural_code.adversarial_v28 import (
    AdversarialV28Error,
    mutate_and_resign,
    validate_coupled_receipt_structure,
)

ROOT = Path("/dev/shm/ciel_noema")
SOURCE_V20_SHA = "84d40f600a8aa9e59ebc6dc42c856bcffec9265d04f791e7f5c49cdba2d583ad"
COUPLED_V27_SHA = "7c9191faa9534f431cb4907cad29b2028fab78a8284624702e53036e2bccbd5d"


def _load_live() -> tuple[dict[str, object], dict[str, object]]:
    if (ROOT / "ciel_binding_status").read_text("utf-8").strip() != "ACTIVE":
        raise AssertionError("live NOEMA binding is not ACTIVE")
    source_path = ROOT / "pncs/v0.20/receipts" / f"{SOURCE_V20_SHA}.json"
    coupled_path = ROOT / "pncs/v0.27/orch_execution/receipts" / f"{COUPLED_V27_SHA}.json"
    source = json.loads(source_path.read_text("utf-8"))
    coupled = json.loads(coupled_path.read_text("utf-8"))
    return source, coupled


def test_live_current_v027_authority_validates_under_v028():
    source, coupled = _load_live()
    assert validate_coupled_receipt_structure(coupled, source_v20_receipt=source) == COUPLED_V27_SHA


def test_live_vector_substitution_is_rejected_after_resign():
    source, coupled = _load_live()
    attacked = mutate_and_resign(
        coupled,
        lambda r: r["orch_occurrences"][0].__setitem__("operator_vector_sha256", "0" * 64),
    )
    with pytest.raises(AdversarialV28Error):
        validate_coupled_receipt_structure(attacked, source_v20_receipt=source)


def test_live_negative_local_proper_time_is_rejected_after_resign():
    source, coupled = _load_live()
    attacked = mutate_and_resign(
        coupled,
        lambda r: r["orch_occurrences"][0].__setitem__("proper_time_advanced", -0.01),
    )
    with pytest.raises(AdversarialV28Error):
        validate_coupled_receipt_structure(attacked, source_v20_receipt=source)


def test_live_external_effect_boundary_substitution_is_rejected_after_resign():
    source, coupled = _load_live()
    attacked = mutate_and_resign(coupled, lambda r: r.__setitem__("external_effects", True))
    with pytest.raises(AdversarialV28Error):
        validate_coupled_receipt_structure(attacked, source_v20_receipt=source)


def test_live_source_receipt_tamper_is_rejected():
    source, coupled = _load_live()
    attacked_source = copy.deepcopy(source)
    attacked_source["result"]["control_location"] = "runtime.tampered"
    with pytest.raises(AdversarialV28Error, match="source v0.20 receipt digest"):
        validate_coupled_receipt_structure(coupled, source_v20_receipt=attacked_source)
