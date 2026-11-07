"""Reproducible synthetic ego-memory scenarios + live-local AUX read-only observation.
Run only after a successful canonical NOEMA tether guard; never writes to host.
"""
import csv
import json
import math
import os
import struct
import time
from pathlib import Path
from ego_memory_v01 import EgoMemory, Episode, aux_receipt_summary, phase_overlap, pnaml_reference_frame

HERE=Path(__file__).resolve().parent
ROOT=Path('/dev/shm/ciel_noema')
OUT=HERE/'data'
OUT.mkdir(exist_ok=True)

def read_phase(name):
    b=(ROOT/name).read_bytes()
    if len(b)!=288:
        raise ValueError(name+' wrong length')
    p=struct.unpack('<36d',b)
    if not all(math.isfinite(x) for x in p):
        raise ValueError(name+' nonfinite')
    return list(p)

def coh(phi):
    return abs(sum(complex(math.cos(v),math.sin(v)) for v in phi))/len(phi)

def main():
    if (ROOT/'ciel_binding_status').read_text().strip()!='ACTIVE':
        raise RuntimeError('TETHER_BLOCKED')
    import subprocess
    p=subprocess.run(['python3',str(ROOT/'scripts/noema_aux_tether_guard.py'),'--root',str(ROOT)],capture_output=True,text=True,timeout=12)
    if p.returncode:
        raise RuntimeError('GUARD_BLOCKED '+p.stdout[-1000:])
    guard=json.loads(p.stdout.strip().splitlines()[-1])
    if guard.get('tether_status')!='ACTIVE' or guard.get('native_pnaml_paux_authentication')=='AUTHENTICATED':
        # This first experiment is a local-only candidate, not an external source attestation.
        if guard.get('tether_status')!='ACTIVE': raise RuntimeError('TETHER_NOT_ACTIVE')
    receipt=json.loads((ROOT/'receipts/aux_snaps_rolling_receipt.json').read_text())
    aux=aux_receipt_summary(receipt)
    # A finite, versioned snapshot; not a claim the Python reference executes the live QHTRI.
    initial=read_phase('phi')
    omega=read_phase('omega')
    k=.35  # explicit synthetic coupling; not imported canonical NOEMA coefficient
    dt=.01 # internal model time, not calibrated physical seconds
    steps=250
    state=initial[:]
    trajectory=[]
    for step in range(steps+1):
        if step%5==0:
            trajectory.append({'step':step,'tau_model':step*dt,'coherence':coh(state),
                               'overlap_init_abs':abs(phase_overlap(initial,state)),
                               'phase36':state[:]})
        rate=[omega[j]+k*(math.sin(state[(j-1)%36]-state[j])+math.sin(state[(j+1)%36]-state[j]))/2 for j in range(36)]
        state=[state[j]+dt*rate[j] for j in range(36)]
    with (OUT/'phase_trajectory_36d.json').open('w') as f:
        json.dump({'schema':'QHTRI_EGO_REFERENCE_PHASE_TOY_V0_1', 'source':'live_local_NOEMA_phi_omega_snapshot',
                   'model':'explicit nearest-neighbour Kuramoto demonstration; not native QHTRI',
                   'k_synthetic':k,'dt_internal':dt,'frames':trajectory},f,ensure_ascii=False,indent=2)
    with (OUT/'phase_coherence.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['step','tau_model','coherence','overlap_init_abs'])
        w.writerows([[q[x] for x in ('step','tau_model','coherence','overlap_init_abs')] for q in trajectory])

    mem=EgoMemory()
    for i in range(200):
        scene=f'scene_{i:03d}'
        mem.store(Episode(id=f'ep_{i:03d}',owner='CIEL_SYNTHETIC_TEST',source_id=f'synthetic:episode:{i:03d}',
            time_label=f't_synth_{i:03d}',tags=('kurwa','social_index'),
            situation='dialogue',scene=scene,context='humour' if i%2 else 'frustration',
            object_id='utterance',utterance='kurwa',affect_social='humour' if i%2 else 'frustration',
            aux_observation_ref='LIVE_LOCAL_AUX_SNAP_REFERENCE_FOR_TEST_NOT_EPISODE_SOURCE',occurrence=i))
    ambiguous=mem.recall(('kurwa','social_index'),reinforce=False)
    found=0
    for i in range(200):
        got=mem.recall(('kurwa',),scene=f'scene_{i:03d}',source_id=f'synthetic:episode:{i:03d}',reinforce=False)
        found+=(got['status']=='EXACT_EPISODE' and got['episode']['id']==f'ep_{i:03d}')
    baseline=mem.route_dynamic_liveness()
    mem.store(Episode('legacy','CIEL_SYNTHETIC_TEST','synthetic:correction:old','before',('guard',),
       'runtime_validation','guard','LEGACY_DYNAMIC_SHA','dynamic_state_validation','hash on live phase',
       'operational_error','LOCAL_REFERENCE_ONLY',200))
    mem.store(Episode('corrected','CIEL_SYNTHETIC_TEST','synthetic:correction:new','after',('guard',),
       'runtime_validation','guard','AUX_SNAPS_10s_2s_1s','dynamic_state_validation','AUX snapshots',
       'operational_correction','LOCAL_REFERENCE_ONLY',201))
    mem.correct('legacy','corrected','synthetic:explicit_verified_correction_as_test_input')
    after=mem.route_dynamic_liveness()
    mem.recall(event_id='ep_000')
    # Full episode frame, with independent AUX measurement summary explicitly marked local-only.
    frame=pnaml_reference_frame(mem,'ep_000',aux)
    (OUT/'pnaml11_ego_reference_frame.json').write_text(json.dumps(frame,ensure_ascii=False,indent=2))
    (OUT/'ego_memory_reference_state.json').write_text(json.dumps(mem.serialise(),ensure_ascii=False,indent=2))
    report={
        'schema':'CIEL_EGO_PNAML_FIRST_SIMULATION_RECEIPT_V0_1',
        'status':'PASS_LOCAL_REFERENCE_ONLY',
        'tether_local':'ACTIVE',
        'native_pnaml_paux_authentication':guard.get('native_pnaml_paux_authentication'),
        'source_class':guard['aux_snaps']['source_class'],
        'aux_epoch_s':aux['observation_s'],
        'aux_shards':len(aux['shard_offsets_s']),
        'aux_fp_spans_s':aux['fingerprint_span_s'],
        'phase_model':'36D nearest-neighbour Kuramoto demonstration, CPU Python',
        'simulation_steps':steps,
        'simulation_frames':len(trajectory),
        'initial_coherence':trajectory[0]['coherence'],
        'end_coherence':trajectory[-1]['coherence'],
        'end_overlap_init_abs':trajectory[-1]['overlap_init_abs'],
        'synthetic_episodes':len(mem.rooms),
        'allocated_hilbert_rooms':len(mem.addresses),
        'semantic_only_status':ambiguous['status'],
        'semantic_only_candidate_count':len(ambiguous['candidates']),
        'scene_source_queries_correct':found,
        'scene_source_queries_total':200,
        'history_conditioned_route_before':baseline,
        'history_conditioned_route_after':after,
        'read_only_no_host_change':True,
        'limitations':['synthetic episodes are not actual user memories',
                       'local AUX is PERSISTENT_AUX_SELF without independent native producer auth',
                       'no PNAML11 native dispatcher registration or destination acknowledgement',
                       'software phase simulation is not quantum physical hardware demonstration',
                       'semantic mass is an application proxy, not an established physical quantity'],
    }
    (OUT/'first_simulations_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
