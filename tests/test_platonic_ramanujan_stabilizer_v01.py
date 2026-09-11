from __future__ import annotations
import math
import numpy as np
from phasenav_natural_code import platonic_ramanujan_stabilizer_v01 as pr

def test_carrier_shape_degree_edges_and_connectivity():
    a=pr.adjacency36(); assert a.shape==(36,36); assert np.array_equal(a,a.T); assert np.all(np.diag(a)==0); assert np.all(a.sum(1)==7); assert int(a.sum()//2)==126
    seen={0}; stack=[0]
    while stack:
        i=stack.pop()
        for j in np.flatnonzero(a[i]):
            j=int(j)
            if j not in seen: seen.add(j); stack.append(j)
    assert len(seen)==36

def test_exact_spectrum_and_ramanujan_bound():
    eig=np.linalg.eigvalsh(pr.adjacency36()); s=math.sqrt(5.0)
    expected=[7.0]+[2+s]*3+[4.0]*2+[s-1]*6+[1.0]*5+[2-s]*3+[-2.0]*10+[-1-s]*6
    assert np.allclose(np.sort(eig),np.sort(expected),rtol=0.0,atol=2e-12)
    m=pr.spectral_metrics(); assert m.degree==7 and m.is_ramanujan
    assert math.isclose(m.nontrivial_radius,2+s,rel_tol=0.0,abs_tol=2e-12)
    assert m.nontrivial_radius<2*math.sqrt(6.0)
    assert math.isclose(m.normalized_laplacian_gap,(5-s)/7,rel_tol=0.0,abs_tol=2e-12)

def test_existing_12x3_lane_order_is_preserved():
    for i in range(36): assert pr.channel_local_lane(i)==(i//3,i%3)

def test_support_mask_has_seven_neighbors_per_lane():
    mask=pr.support_mask(); assert mask.dtype==np.bool_; assert np.all(mask.sum(1)==7); assert not np.any(np.diag(mask))

def test_mask_is_non_mutating_and_sparse():
    g=np.arange(36*36,dtype=np.float64).reshape(36,36); before=g.copy(); out=pr.apply_support_mask(g)
    assert np.array_equal(g,before); assert np.count_nonzero(pr.support_mask(),axis=1).tolist()==[7]*36; assert np.all(out[~pr.support_mask()]==0)

def test_uniform_zero_global_phase_covariant_and_zero_net():
    phi=np.full(36,1.234); assert np.allclose(pr.stabilizing_coupling(phi,.7),0,atol=1e-15)
    rng=np.random.default_rng(20260911); phi=rng.uniform(-math.pi,math.pi,36)
    c0=pr.stabilizing_coupling(phi,.25); c1=pr.stabilizing_coupling(phi+.918273,.25)
    assert np.allclose(c0,c1,rtol=0.0,atol=2e-15); assert abs(float(c0.sum()))<5e-15

def test_small_perturbations_contract_under_candidate_term():
    rng=np.random.default_rng(7); d=rng.normal(size=36); d-=d.mean(); d*=1e-4/np.linalg.norm(d)
    nxt=d+.1*pr.stabilizing_coupling(d,.5); nxt-=nxt.mean(); assert np.linalg.norm(nxt)<np.linalg.norm(d)

def test_linearized_gap_bound():
    b=.75; assert math.isclose(pr.linearized_decay_bound(b),b*(5-math.sqrt(5))/7,rel_tol=0.0,abs_tol=1e-15)
