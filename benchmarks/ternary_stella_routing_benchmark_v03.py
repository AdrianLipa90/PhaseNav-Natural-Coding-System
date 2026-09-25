from __future__ import annotations
import json, random, statistics, math, time
from pathlib import Path

from phasenav_natural_code.ternary_stella_v03 import (
    route_choice_full,
    route_choice_sign,
    route_choice_stella3,
    Stella3,
    pack_codes_5bit,
    unpack_codes_5bit,
    theoretical_storage_bits,
)

SEED=20260925
TRIALS=30000
ROUTE_COUNTS=(2,4,8,16,32,64)
rng=random.Random(SEED)
rows=[]

for k in ROUTE_COUNTS:
    sign_mismatch=0
    stella_mismatch=0
    sign_regret=[]
    stella_regret=[]
    stella_abs_qerr=[]
    t0=time.perf_counter()
    for _ in range(TRIALS):
        weights={f"r{i:03d}": rng.uniform(-1.0,1.0) for i in range(k)}
        truth=route_choice_full(weights)
        sign=route_choice_sign(weights)
        stella, quantized=route_choice_stella3(weights)
        sign_mismatch += sign != truth
        stella_mismatch += stella != truth
        sign_regret.append(weights[truth]-weights[sign])
        stella_regret.append(weights[truth]-weights[stella])
        stella_abs_qerr.extend(q.absolute_error for q in quantized.values())
    elapsed=time.perf_counter()-t0
    sr=sorted(stella_regret)
    sgr=sorted(sign_regret)
    rows.append({
        "routes":k,
        "trials":TRIALS,
        "sign_exact_parity":1-sign_mismatch/TRIALS,
        "stella3_exact_parity":1-stella_mismatch/TRIALS,
        "sign_mean_regret":statistics.mean(sign_regret),
        "stella3_mean_regret":statistics.mean(stella_regret),
        "sign_p95_regret":sgr[int(0.95*(len(sgr)-1))],
        "stella3_p95_regret":sr[int(0.95*(len(sr)-1))],
        "stella3_max_regret":max(stella_regret),
        "stella3_mean_abs_quantization_error":statistics.mean(stella_abs_qerr),
        "elapsed_s":elapsed,
    })

states=[Stella3.from_code(rng.randrange(27)) for _ in range(100000)]
t0=time.perf_counter()
packed=pack_codes_5bit(states)
unpacked=unpack_codes_5bit(packed,len(states))
pack_s=time.perf_counter()-t0
assert tuple(states)==unpacked
storage=theoretical_storage_bits(100000)

receipt={
    "schema":"PNCS_TERNARY_STELLA_ROUTING_BENCHMARK_V0_3",
    "date":"2026-09-25",
    "status":"MEASURED_CANDIDATE",
    "seed":SEED,
    "trials_per_route_count":TRIALS,
    "route_counts":list(ROUTE_COUNTS),
    "rows":rows,
    "serialization":{
        "states":100000,
        "roundtrip_exact":True,
        "packed_bytes":len(packed),
        "expected_packed_bytes":math.ceil(100000*5/8),
        "elapsed_s":pack_s,
    },
    "logical_storage_bits":storage,
    "weight_only_compression_ratio_float64_to_5bit":64/5,
    "weight_only_compression_ratio_float64_to_entropy_floor":64/math.log2(27),
    "shell_counts":{"center":1,"axis":6,"edge":12,"corner":8},
    "interpretation":{
        "one_standard_trit_states":3,
        "three_trit_stella_states":27,
        "corner_sign_states":8,
        "sign_only_baseline_expected_to_be_lossy":True,
        "stella3_is_classical":True,
        "physical_quantum_claim":False,
        "quantum_advantage_claim":False,
        "exact_decision_equivalence_claim":False,
    },
}
out=Path("PNCS_TERNARY_STELLA_ROUTING_BENCHMARK_V0_3.json")
out.write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps(receipt,indent=2))
