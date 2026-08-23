import numpy as np
import pytest
from phasenav_natural_code.temporal_fibre_v1 import PreparedDenseTemporalFibre, CompiledTemporalGateSet, TemporalFibreKernelError

RNG=np.random.default_rng(260823)
A=RNG.normal(size=(36,36))+1j*RNG.normal(size=(36,36))
H=(A+A.conj().T)/72.0
psi=RNG.normal(size=36)+1j*RNG.normal(size=36); psi=psi/np.linalg.norm(psi)

def legacy(state,dt):
    vals,vecs=np.linalg.eigh(H); c=vecs.conj().T@state
    return vecs@(np.exp(-1j*vals*dt)*c)

def test_prepare_dimension_and_digest():
    k=PreparedDenseTemporalFibre.prepare(H); assert k.dimension==36 and len(k.hamiltonian_sha256)==64

def test_nonhermitian_fails_closed():
    x=H.copy(); x[0,1]+=0.1j
    with pytest.raises(TemporalFibreKernelError): PreparedDenseTemporalFibre.prepare(x)

def test_bad_state_dimension_fails_closed():
    k=PreparedDenseTemporalFibre.prepare(H)
    with pytest.raises(TemporalFibreKernelError): k.evolve(np.zeros(35),0.1)

def test_negative_tau_fails_closed():
    k=PreparedDenseTemporalFibre.prepare(H)
    with pytest.raises(TemporalFibreKernelError): k.evolve(psi,-0.1)

def test_nan_rate_fails_closed():
    k=PreparedDenseTemporalFibre.prepare(H)
    with pytest.raises(TemporalFibreKernelError): k.local_gate_trajectory(psi,0.01,[1.0,np.nan])

def test_single_step_equivalence():
    k=PreparedDenseTemporalFibre.prepare(H)
    assert np.max(np.abs(k.evolve(psi,0.137)-legacy(psi,0.137)))<2e-13

def test_increment_trajectory_equivalence():
    k=PreparedDenseTemporalFibre.prepare(H); d=np.resize(np.array([.001,.002,.004,.003]),80)
    s=psi.copy(); ref=[]
    for dt in d: s=legacy(s,float(dt)); ref.append(s.copy())
    got=k.trajectory_from_increments(psi,d)
    assert np.max(np.abs(got-np.asarray(ref)))<2e-12

def test_local_rate_contract():
    k=PreparedDenseTemporalFibre.prepare(H); rates=np.array([.5,1.,1.5,2.])
    a=k.local_gate_trajectory(psi,.01,rates)
    b=k.trajectory(psi,np.cumsum(.01*rates))
    assert np.array_equal(a,b)

def test_zero_local_rate_holds_state():
    k=PreparedDenseTemporalFibre.prepare(H); got=k.local_gate_trajectory(psi,.1,np.zeros(5))
    assert np.max(np.abs(got-psi[None,:]))<2e-13

def test_global_phase_covariance():
    k=PreparedDenseTemporalFibre.prepare(H); alpha=.713
    a=k.evolve(np.exp(1j*alpha)*psi,.08); b=np.exp(1j*alpha)*k.evolve(psi,.08)
    assert np.max(np.abs(a-b))<2e-13

def test_norm_preservation():
    k=PreparedDenseTemporalFibre.prepare(H); got=k.trajectory(psi,np.linspace(0,3,101))
    assert np.max(np.abs(np.linalg.norm(got,axis=1)-1.0))<2e-13

def test_hamiltonian_identity_changes_with_matrix():
    k1=PreparedDenseTemporalFibre.prepare(H); x=H.copy(); x[0,0]+=1e-6; k2=PreparedDenseTemporalFibre.prepare(x)
    assert k1.hamiltonian_sha256!=k2.hamiltonian_sha256

def test_compiled_gate_equivalence():
    k=PreparedDenseTemporalFibre.prepare(H); gates=CompiledTemporalGateSet.compile(k,[.01,.02,.04])
    assert np.max(np.abs(gates.step(psi,.02)-k.evolve(psi,.02)))<2e-13

def test_compiled_gate_unknown_delta_fails_closed():
    k=PreparedDenseTemporalFibre.prepare(H); gates=CompiledTemporalGateSet.compile(k,[.01,.02])
    with pytest.raises(TemporalFibreKernelError): gates.step(psi,.03)

def test_compiled_gate_count_is_bounded():
    k=PreparedDenseTemporalFibre.prepare(H)
    with pytest.raises(TemporalFibreKernelError): CompiledTemporalGateSet.compile(k,np.linspace(0,1,65),max_gates=64)

def test_compiled_schedule_equivalence():
    k=PreparedDenseTemporalFibre.prepare(H); d=np.resize(np.array([.01,.02,.04]),60); gates=CompiledTemporalGateSet.compile(k,d)
    got=gates.run_known_schedule(psi,d); ref=k.trajectory_from_increments(psi,d)
    assert np.max(np.abs(got-ref))<2e-12

def test_compiled_route_schedule_equivalence():
    k=PreparedDenseTemporalFibre.prepare(H); d=np.resize(np.array([.01,.02,.04]),100); gates=CompiledTemporalGateSet.compile(k,d)
    schedule=gates.compile_schedule(d)
    ref=k.trajectory_from_increments(psi,d)
    assert np.max(np.abs(schedule.trajectory(psi)-ref))<2e-12
    assert np.max(np.abs(schedule.final_state(psi)-ref[-1]))<2e-12

def test_compiled_route_rejects_unknown_gate():
    k=PreparedDenseTemporalFibre.prepare(H); gates=CompiledTemporalGateSet.compile(k,[.01,.02])
    with pytest.raises(TemporalFibreKernelError): gates.compile_schedule([.01,.03])
