from __future__ import annotations

import os
from pathlib import Path
import stat
from typing import Sequence

from .effect_v26_core import (
    EFFECT_CONTRACT_ID,
    EFFECT_RECORD_SCHEMA,
    NOEMA_RUNTIME_RECORD_ADAPTER,
    EffectAuthorizationGrant,
    EffectBoundaryV26Error,
    EffectRequest,
    _json_bytes,
)


def _open_fixed_directory_fd(root: Path, relative: Sequence[str]) -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        current_fd = os.open(root, flags)
    except OSError as exc:
        raise EffectBoundaryV26Error("cannot open live effect root without following symlinks") from exc
    try:
        for component in relative:
            if component in {"", ".", ".."} or "/" in component or "\\" in component:
                raise EffectBoundaryV26Error("invalid fixed adapter path component")
            try:
                os.mkdir(component, mode=0o700, dir_fd=current_fd)
            except FileExistsError:
                pass
            try:
                next_fd = os.open(component, flags, dir_fd=current_fd)
            except OSError as exc:
                raise EffectBoundaryV26Error("bounded effect path contains a symlink or non-directory") from exc
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except Exception:
        try:
            os.close(current_fd)
        except OSError:
            pass
        raise


def _read_regular_file_at(dir_fd: int, filename: str) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(filename, flags, dir_fd=dir_fd)
    except OSError as exc:
        raise EffectBoundaryV26Error("cannot open existing immutable effect artifact without following symlinks") from exc
    try:
        mode = os.fstat(fd).st_mode
        if not stat.S_ISREG(mode):
            raise EffectBoundaryV26Error("immutable effect artifact is not a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def _immutable_write_at(dir_fd: int, filename: str, raw: bytes, *, collision: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(filename, flags, 0o600, dir_fd=dir_fd)
    except FileExistsError:
        if _read_regular_file_at(dir_fd, filename) != raw:
            raise EffectBoundaryV26Error(collision)
        return
    except OSError as exc:
        raise EffectBoundaryV26Error("bounded effect artifact create failed") from exc
    try:
        with os.fdopen(fd, "wb", closefd=True) as fh:
            fh.write(raw)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:
        try:
            os.unlink(filename, dir_fd=dir_fd)
        except OSError:
            pass
        raise


class NoemaRuntimeRecordAdapter:
    descriptor = NOEMA_RUNTIME_RECORD_ADAPTER

    def apply(self, request: EffectRequest, grant: EffectAuthorizationGrant, root: Path) -> tuple[str, bytes]:
        if request.adapter_id != self.descriptor.adapter_id or grant.adapter_id != self.descriptor.adapter_id:
            raise EffectBoundaryV26Error("adapter identity mismatch")
        if request.effect_kind != self.descriptor.effect_kind or request.target != self.descriptor.target:
            raise EffectBoundaryV26Error("adapter request scope mismatch")
        if request.payload_size_bytes > min(self.descriptor.max_payload_bytes, grant.max_payload_bytes):
            raise EffectBoundaryV26Error("adapter payload bound exceeded")
        relative = self.descriptor.runtime_relative_root.split("/")
        digest = request.request_id.rsplit(":", 1)[-1]
        filename = f"{digest}.json"
        record = {
            "schema": EFFECT_RECORD_SCHEMA,
            "effect_contract_id": EFFECT_CONTRACT_ID,
            "request_id": request.request_id,
            "authorization_id": grant.authorization_id,
            "adapter_id": self.descriptor.adapter_id,
            "origin": request.origin.payload,
            "effect_kind": request.effect_kind,
            "target": request.target,
            "payload": dict(request.payload_data),
            "payload_sha256": request.payload_sha256,
            "append_only": True,
            "program_supplied_path": False,
        }
        raw = _json_bytes(record)
        dir_fd = _open_fixed_directory_fd(root, relative)
        try:
            _immutable_write_at(dir_fd, filename, raw, collision="immutable effect record collision")
        finally:
            os.close(dir_fd)
        return "/".join(relative + [filename]), raw
