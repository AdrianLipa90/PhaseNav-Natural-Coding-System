from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

from .usb_sysfs_effect_v01 import UsbDeviceSnapshot

PROBE_CONTRACT_ID = "PHASENAV_USB_CRYSTAL_PROBE_V0_2_NATIVE"


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _digest(value: object) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ControllerClockRecord:
    record_id: str
    controller_vendor: str
    controller_family: str
    controller_part_number: str
    topology: str
    nominal_hz: int | None
    evidence_reference: str
    confidence: float
    vid: str | None = None
    pid: str | None = None
    product_contains: str | None = None

    def __post_init__(self) -> None:
        if self.topology not in {
            "EXTERNAL_CRYSTAL", "EXTERNAL_RESONATOR", "INTERNAL_RC",
            "INTERNAL_PLL", "USB_CLOCK_RECOVERY", "HYBRID", "UNKNOWN",
        }:
            raise ValueError("invalid clock topology")
        if self.nominal_hz is not None and self.nominal_hz <= 0:
            raise ValueError("nominal_hz must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence outside [0,1]")

    def matches(self, snapshot: UsbDeviceSnapshot) -> bool:
        if self.vid is not None and snapshot.vid != self.vid.lower():
            return False
        if self.pid is not None and snapshot.pid != self.pid.lower():
            return False
        if self.product_contains is not None:
            product = snapshot.attributes.get("product", "").lower()
            if self.product_contains.lower() not in product:
                return False
        return any(x is not None for x in (self.vid, self.pid, self.product_contains))


@dataclass(frozen=True)
class UsbCrystalProbeReceipt:
    snapshot_id: str
    vid: str
    pid: str
    product: str | None
    usb_reported_speed_mbps: str | None
    controller_vendor: str | None
    controller_family: str | None
    controller_part_number: str | None
    clock_topology: str
    nominal_hz: int | None
    evidence_class: str
    evidence_reference: str | None
    confidence: float

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": "PHASENAV_USB_CRYSTAL_PROBE_RECEIPT_V0_2",
            "contract_id": PROBE_CONTRACT_ID,
            "snapshot_id": self.snapshot_id,
            "vid": self.vid,
            "pid": self.pid,
            "product": self.product,
            "usb_reported_speed_mbps": self.usb_reported_speed_mbps,
            "controller_vendor": self.controller_vendor,
            "controller_family": self.controller_family,
            "controller_part_number": self.controller_part_number,
            "clock_topology": self.clock_topology,
            "nominal_hz": self.nominal_hz,
            "evidence_class": self.evidence_class,
            "evidence_reference": self.evidence_reference,
            "confidence": self.confidence,
            "usb_bus_speed_is_oscillator_frequency": False,
        }

    @property
    def receipt_id(self) -> str:
        return f"pncs:usb-crystal-probe:sha256:{_digest(self.payload)}"


def resolve_crystal_probe(
    snapshot: UsbDeviceSnapshot,
    controller_registry: Iterable[ControllerClockRecord] = (),
) -> UsbCrystalProbeReceipt:
    records = [r for r in controller_registry if r.matches(snapshot)]
    records.sort(key=lambda r: (-r.confidence, r.record_id))
    product = snapshot.attributes.get("product")
    speed = snapshot.attributes.get("speed")

    if not records:
        return UsbCrystalProbeReceipt(
            snapshot_id=snapshot.snapshot_id,
            vid=snapshot.vid,
            pid=snapshot.pid,
            product=product,
            usb_reported_speed_mbps=speed,
            controller_vendor=None,
            controller_family=None,
            controller_part_number=None,
            clock_topology="UNKNOWN",
            nominal_hz=None,
            evidence_class="UNKNOWN",
            evidence_reference=None,
            confidence=0.0,
        )

    best = records[0]
    return UsbCrystalProbeReceipt(
        snapshot_id=snapshot.snapshot_id,
        vid=snapshot.vid,
        pid=snapshot.pid,
        product=product,
        usb_reported_speed_mbps=speed,
        controller_vendor=best.controller_vendor,
        controller_family=best.controller_family,
        controller_part_number=best.controller_part_number,
        clock_topology=best.topology,
        nominal_hz=best.nominal_hz,
        evidence_class="INFERRED",
        evidence_reference=best.evidence_reference,
        confidence=best.confidence,
    )
