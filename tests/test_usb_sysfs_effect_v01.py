from pathlib import Path
import pytest

from phasenav_natural_code.usb_sysfs_effect_v01 import (
    UsbDeviceSnapshot,
    UsbSysfsReadError,
    enumerate_usb_sysfs,
)


def _device(root: Path, name: str, *, vid="0781", pid="5567", product="Cruzer Blade") -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "idVendor").write_text(vid + "\n")
    (d / "idProduct").write_text(pid + "\n")
    (d / "manufacturer").write_text("SanDisk\n")
    (d / "product").write_text(product + "\n")
    (d / "speed").write_text("480\n")
    return d


def test_snapshot_is_content_deterministic():
    a = UsbDeviceSnapshot("1-1", "/tmp/dev/1-1", {"idVendor":"0781","idProduct":"5567","product":"Cruzer Blade"})
    b = UsbDeviceSnapshot("1-1", "/tmp/dev/1-1", {"product":"Cruzer Blade","idProduct":"5567","idVendor":"0781"})
    assert a.snapshot_id == b.snapshot_id
    assert a.payload["evidence_class"] == "REPORTED"


def test_non_whitelisted_attribute_fails_closed():
    with pytest.raises(UsbSysfsReadError):
        UsbDeviceSnapshot("1-1", "/tmp/dev/1-1", {"idVendor":"0781","idProduct":"5567","secret":"x"})


def test_enumeration_filters_exact_vid_pid(tmp_path: Path):
    physical = tmp_path / "physical"
    sysfs = tmp_path / "usb"
    physical.mkdir()
    sysfs.mkdir()
    sandisk = _device(physical, "devA")
    other = _device(physical, "devB", vid="1234", pid="9999", product="Other")
    (sysfs / "1-1").symlink_to(sandisk, target_is_directory=True)
    (sysfs / "1-2").symlink_to(other, target_is_directory=True)

    got = enumerate_usb_sysfs(
        sysfs_root=sysfs,
        physical_root=physical,
        target_vid="0781",
        target_pid="5567",
        require_canonical_root=False,
    )
    assert len(got) == 1
    assert got[0].vid == "0781"
    assert got[0].pid == "5567"
    assert got[0].attributes["product"] == "Cruzer Blade"


def test_missing_target_fails_closed(tmp_path: Path):
    physical = tmp_path / "physical"
    sysfs = tmp_path / "usb"
    physical.mkdir()
    sysfs.mkdir()
    d = _device(physical, "devA")
    (sysfs / "1-1").symlink_to(d, target_is_directory=True)
    with pytest.raises(UsbSysfsReadError):
        enumerate_usb_sysfs(
            sysfs_root=sysfs,
            physical_root=physical,
            target_vid="ffff",
            target_pid="ffff",
            require_canonical_root=False,
        )


def test_symlink_escape_does_not_enter_snapshot(tmp_path: Path):
    physical = tmp_path / "physical"
    sysfs = tmp_path / "usb"
    outside = tmp_path / "outside"
    physical.mkdir()
    sysfs.mkdir()
    outside.mkdir()
    d = _device(outside, "evil")
    (sysfs / "1-9").symlink_to(d, target_is_directory=True)
    with pytest.raises(UsbSysfsReadError):
        enumerate_usb_sysfs(
            sysfs_root=sysfs,
            physical_root=physical,
            require_canonical_root=False,
        )


def test_operational_root_is_fixed(tmp_path: Path):
    with pytest.raises(UsbSysfsReadError):
        enumerate_usb_sysfs(
            sysfs_root=tmp_path,
            physical_root=tmp_path,
            require_canonical_root=True,
        )
