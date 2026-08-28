from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Hydrate and verify GREMLIN native-PNV authoring after NOEMA WORKING_STATE."
    )
    parser.add_argument("--root", default="/dev/shm/ciel_noema")
    parser.add_argument("--socket", default="/run/user/1000/noema/ciel_headless.sock")
    parser.add_argument("--task", default="PNCS_GREMLIN_POST_WORKING_STATE")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    from phasenav_natural_code.gremlin_live_hydration_v03 import (
        hydrate_gremlin_pnv_live,
        open_verified_gremlin_pnv_authoring_live,
    )

    pnv_path = repo_root / "native" / "GREMLIN_TRIPLE_PULSE_BOOT_V0_5.pnv"
    pnv_text = pnv_path.read_text(encoding="utf-8")

    hydration = hydrate_gremlin_pnv_live(
        pnv_text,
        request="GREMLIN_PNV_AUTHORING_BOOT",
        surface_root=Path(args.root),
        socket_path=Path(args.socket),
    )
    session = open_verified_gremlin_pnv_authoring_live(
        pnv_text,
        surface_root=Path(args.root),
        socket_path=Path(args.socket),
    )

    witness = dict(hydration.witness)
    result = {
        "schema": "PNCS_GREMLIN_POST_WORKING_STATE_HOOK_V0_3",
        "status": "PASS",
        "surface_root": str(session.surface_root),
        "task": args.task,
        "generation_binding": session.generation_binding,
        "tether_receipt_sha256": session.tether_receipt_sha256,
        "native_pnv_source_sha256": witness["native_pnv_source_sha256"],
        "witness_sha256": witness["witness_sha256"],
        "witness_path": str(hydration.witness_path),
        "authoring_root": str(session.authoring_root),
        "promotion_state": "CANDIDATE_ONLY",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "static_runtime_fallback": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
