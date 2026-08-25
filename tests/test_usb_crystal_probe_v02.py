from phasenav_natural_code.usb_crystal_probe_v02 import (
    ControllerClockRecord,
    resolve_crystal_probe,
)
from phasenav_natural_code.usb_sysfs_effect_v01 import UsbDeviceSnapshot


def _sandisk():
    return UsbDeviceSnapshot(
        "1-1",
        "/sys/devices/pci0000:00/usb1/1-1",
        {
            "idVendor": "0781",
            "idProduct": "5567",
            "manufacturer": "SanDisk",
            "product": "Cruzer Blade",
            "speed": "480",
        },
    )


def test_unknown_without_controller_evidence():
    r = resolve_crystal_probe(_sandisk())
    assert r.clock_topology == "UNKNOWN"
    assert r.nominal_hz is None
    assert r.evidence_class == "UNKNOWN"
    assert r.payload["usb_bus_speed_is_oscillator_frequency"] is False


def test_documented_controller_match_is_inferred():
    record = ControllerClockRecord(
        record_id="example-controller-doc",
        controller_vendor="ExampleVendor",
        controller_family="ExampleFamily",
        controller_part_number="EX123",
        topology="EXTERNAL_CRYSTAL",
        nominal_hz=12_000_000,
        evidence_reference="example datasheet section 4",
        confidence=0.82,
        vid="0781",
        pid="5567",
        product_contains="Cruzer Blade",
    )
    r = resolve_crystal_probe(_sandisk(), [record])
    assert r.clock_topology == "EXTERNAL_CRYSTAL"
    assert r.nominal_hz == 12_000_000
    assert r.evidence_class == "INFERRED"
    assert r.confidence == 0.82


def test_highest_confidence_match_wins_deterministically():
    low = ControllerClockRecord(
        record_id="b-low",
        controller_vendor="V",
        controller_family="F1",
        controller_part_number="P1",
        topology="INTERNAL_PLL",
        nominal_hz=24_000_000,
        evidence_reference="doc-low",
        confidence=0.4,
        vid="0781",
        pid="5567",
    )
    high = ControllerClockRecord(
        record_id="a-high",
        controller_vendor="V",
        controller_family="F2",
        controller_part_number="P2",
        topology="EXTERNAL_CRYSTAL",
        nominal_hz=12_000_000,
        evidence_reference="doc-high",
        confidence=0.9,
        vid="0781",
        pid="5567",
    )
    r = resolve_crystal_probe(_sandisk(), [low, high])
    assert r.controller_part_number == "P2"
    assert r.nominal_hz == 12_000_000


def test_nonmatching_registry_does_not_infer():
    record = ControllerClockRecord(
        record_id="other",
        controller_vendor="V",
        controller_family="F",
        controller_part_number="P",
        topology="EXTERNAL_CRYSTAL",
        nominal_hz=12_000_000,
        evidence_reference="doc",
        confidence=0.9,
        vid="ffff",
        pid="eeee",
    )
    r = resolve_crystal_probe(_sandisk(), [record])
    assert r.evidence_class == "UNKNOWN"
    assert r.nominal_hz is None
