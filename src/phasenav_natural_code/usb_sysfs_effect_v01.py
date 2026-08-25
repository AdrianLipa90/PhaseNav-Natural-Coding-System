from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Mapping

from .effect_v26_core import EffectBoundaryV26Error, EffectOrigin, _GENERATION_RE, _typed
from .effect_v26_fs import _immutable_write_at, _open_fixed_directory_fd
from .runtime_v25_core import DEFAULT_SOCKET, DEFAULT_SURFACE_ROOT, read_live_generation

USB_SYSFS_READ_CONTRACT_ID = "PNCS_USB_SYSFS_READ_EFFECT_V0_1"
USB_SYSFS_ROOT = Path("/sys/bus/usb/devices")
USB_PHYSICAL_ROOT = Path("/sys/devices")
RECEIPT_RELATIVE_ROOT = ("pncs", "usb-sysfs-read-v0.1", "receipts")
MAX_TEXT_BYTES = 4096

USB_ATTRIBUTE_WHITELIST = (
    "idVendor", "idProduct", "manufacturer", "product", "serial",
    "bcdDevice", "bcdUSB", "speed", "busnum", "devnum", "devpath",
    "version", "maxchild",
)


class UsbSysfsReadError(EffectBoundaryV26Error):
    pass


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _digest(value: object) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _read_text_bounded(path: Path) -> str | None:
    try:
        with path.open("rb") as fh:
            raw = fh.read(MAX_TEXT_BYTES + 1)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise UsbSysfsReadError(f"cannot read sysfs attribute: {path.name}") from exc
    if len(raw) > MAX_TEXT_BYTES:
        raise UsbSysfsReadError(f"sysfs attribute exceeds bound: {path.name}")
    try:
        return raw.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise UsbSysfsReadError(f"sysfs attribute is not UTF-8 text: {path.name}") from exc


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class UsbDeviceSnapshot:
    sysfs_node: str
    resolved_device_path: str
    attributes: Mapping[str, str]

    def __post_init__(self) -> None:
        attrs = dict(self.attributes)
        unknown = set(attrs) - set(USB_ATTRIBUTE_WHITELIST)
        if unknown:
            raise UsbSysfsReadError(f"non-whitelisted USB attributes: {sorted(unknown)}")
        if "idVendor" not in attrs or "idProduct" not in attrs:
            raise UsbSysfsReadError("USB snapshot requires idVendor and idProduct")
        object.__setattr__(self, "attributes", {k: attrs[k] for k in USB_ATTRIBUTE_WHITELIST if k in attrs})

    @property
    def vid(self) -> str:
        return self.attributes["idVendor"].lower()

    @property
    def pid(self) -> str:
        return self.attributes["idProduct"].lower()

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": "PNCS_USB_DEVICE_SNAPSHOT_V0_1",
            "contract_id": USB_SYSFS_READ_CONTRACT_ID,
            "sysfs_node": self.sysfs_node,
            "resolved_device_path": self.resolved_device_path,
            "attributes": dict(self.attributes),
            "evidence_class": "REPORTED",
            "read_only": True,
        }

    @property
    def snapshot_id(self) -> str:
        return f"pncs:usb-device-snapshot:sha256:{_digest(self.payload)}"


@dataclass(frozen=True)
class UsbSysfsReadReceipt:
    origin: EffectOrigin
    generation_id_before: str
    generation_id_after: str
    snapshots: tuple[UsbDeviceSnapshot, ...]
    target_vid: str | None = None
    target_pid: str | None = None

    def __post_init__(self) -> None:
        _typed(self.generation_id_before, _GENERATION_RE, "generation_id_before")
        _typed(self.generation_id_after, _GENERATION_RE, "generation_id_after")
        if self.generation_id_before != self.generation_id_after:
            raise UsbSysfsReadError("runtime generation changed across USB read effect")
        if self.generation_id_before != self.origin.generation_id:
            raise UsbSysfsReadError("USB read effect generation differs from dispatch origin")
        if not self.snapshots:
            raise UsbSysfsReadError("USB read effect produced no device snapshots")

    @property
    def payload(self) -> dict[str, object]:
        return {
            "schema": "PNCS_USB_SYSFS_READ_RECEIPT_V0_1",
            "contract_id": USB_SYSFS_READ_CONTRACT_ID,
            "origin": self.origin.payload,
            "generation_id_before": self.generation_id_before,
            "generation_id_after": self.generation_id_after,
            "target_vid": self.target_vid,
            "target_pid": self.target_pid,
            "snapshots": [s.payload | {"snapshot_id": s.snapshot_id} for s in self.snapshots],
            "evidence_class": "REPORTED",
            "read_only": True,
            "sysfs_only": True,
            "block_device_write": False,
            "raw_usb_write": False,
            "vendor_command": False,
            "firmware_command": False,
            "subprocess_allowed": False,
            "network_allowed": False,
            "static_runtime_fallback": False,
        }

    @property
    def receipt_id(self) -> str:
        return f"pncs:usb-sysfs-read-receipt:sha256:{_digest(self.payload)}"


def enumerate_usb_sysfs(
    *,
    sysfs_root: Path | str = USB_SYSFS_ROOT,
    physical_root: Path | str = USB_PHYSICAL_ROOT,
    target_vid: str | None = None,
    target_pid: str | None = None,
    require_canonical_root: bool = True,
) -> tuple[UsbDeviceSnapshot, ...]:
    root = Path(sysfs_root)
    physical = Path(physical_root)
    if require_canonical_root and (root != USB_SYSFS_ROOT or physical != USB_PHYSICAL_ROOT):
        raise UsbSysfsReadError("operational USB read effect is fixed to canonical Linux sysfs roots")
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name)
        physical_resolved = physical.resolve(strict=True)
    except OSError as exc:
        raise UsbSysfsReadError("cannot enumerate canonical USB sysfs roots") from exc

    tv = target_vid.lower() if target_vid else None
    tp = target_pid.lower() if target_pid else None
    out: list[UsbDeviceSnapshot] = []

    for entry in entries:
        try:
            resolved = entry.resolve(strict=True)
        except OSError:
            continue
        if not _inside(resolved, physical_resolved):
            if require_canonical_root:
                raise UsbSysfsReadError("USB sysfs node resolves outside /sys/devices")
            continue

        attrs: dict[str, str] = {}
        for name in USB_ATTRIBUTE_WHITELIST:
            value = _read_text_bounded(resolved / name)
            if value is not None:
                attrs[name] = value
        if "idVendor" not in attrs or "idProduct" not in attrs:
            continue
        if tv is not None and attrs["idVendor"].lower() != tv:
            continue
        if tp is not None and attrs["idProduct"].lower() != tp:
            continue
        out.append(UsbDeviceSnapshot(entry.name, str(resolved), attrs))

    if not out:
        target = ":".join(x or "*" for x in (tv, tp))
        raise UsbSysfsReadError(f"no USB device matched target {target}")
    return tuple(out)


class UsbSysfsReadEffect:
    def __init__(
        self,
        surface_root: Path | str = DEFAULT_SURFACE_ROOT,
        *,
        socket_path: Path | str = DEFAULT_SOCKET,
        max_heartbeat_age_s: float = 2.0,
        require_socket: bool = True,
        require_canonical_root: bool = True,
        generation_reader=read_live_generation,
    ) -> None:
        self.surface_root = Path(surface_root)
        self.socket_path = Path(socket_path)
        self.max_heartbeat_age_s = max_heartbeat_age_s
        self.require_socket = require_socket
        self.require_canonical_root = require_canonical_root
        self.generation_reader = generation_reader
        if require_canonical_root and self.surface_root != DEFAULT_SURFACE_ROOT:
            raise UsbSysfsReadError("USB read receipts are fixed to /dev/shm/ciel_noema")

    def _generation_id(self) -> str:
        try:
            state = self.generation_reader(
                self.surface_root,
                socket_path=self.socket_path,
                max_heartbeat_age_s=self.max_heartbeat_age_s,
                require_socket=self.require_socket,
                require_canonical_root=self.require_canonical_root,
            )
        except Exception as exc:
            raise UsbSysfsReadError("live NOEMA generation admission failed") from exc
        return _typed(getattr(state, "generation_id", None), _GENERATION_RE, "live generation_id")

    def execute(
        self,
        dispatch_receipt: Mapping[str, object],
        *,
        target_vid: str | None = None,
        target_pid: str | None = None,
        sysfs_root: Path | str = USB_SYSFS_ROOT,
        physical_root: Path | str = USB_PHYSICAL_ROOT,
    ) -> UsbSysfsReadReceipt:
        origin = EffectOrigin.from_dispatch_receipt(dispatch_receipt)
        before = self._generation_id()
        if before != origin.generation_id:
            raise UsbSysfsReadError("USB read request is stale for current live runtime generation")
        snapshots = enumerate_usb_sysfs(
            sysfs_root=sysfs_root,
            physical_root=physical_root,
            target_vid=target_vid,
            target_pid=target_pid,
            require_canonical_root=self.require_canonical_root,
        )
        after = self._generation_id()
        receipt = UsbSysfsReadReceipt(origin, before, after, snapshots, target_vid, target_pid)
        raw = (json.dumps(receipt.payload | {"receipt_id": receipt.receipt_id}, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        directory_fd = _open_fixed_directory_fd(self.surface_root, RECEIPT_RELATIVE_ROOT)
        try:
            filename = receipt.receipt_id.rsplit(":", 1)[-1] + ".json"
            _immutable_write_at(directory_fd, filename, raw, collision="immutable USB read receipt collision")
        finally:
            os.close(directory_fd)
        return receipt
