from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Sequence

import numpy as np

SCHEMA="PNCS_PLATONIC_RAMANUJAN_STABILIZER_V0_1"
N_CHANNELS=12
LANES_PER_CHANNEL=3
N=N_CHANNELS*LANES_PER_CHANNEL
CHANNEL_DEGREE=5
LOCAL_DEGREE=2
DEGREE=7

ICOSAHEDRAL_EDGES=((0,1),(0,5),(0,7),(0,8),(0,11),(1,2),(1,5),(1,6),(1,8),(2,3),(2,6),(2,8),(2,9),(3,4),(3,6),(3,9),(3,10),(4,5),(4,6),(4,10),(4,11),(5,6),(5,11),(7,8),(7,9),(7,10),(7,11),(8,9),(9,10),(10,11))

class PlatonicRamanujanStabilizerV01Error(ValueError):
    pass

def _finite_real(name,value):
    if isinstance(value,bool) or not isinstance(value,Real): raise PlatonicRamanujanStabilizerV01Error(f"{name} must be a finite real")
    out=float(value)
    if not math.isfinite(out): raise PlatonicRamanujanStabilizerV01Error(f"{name} must be a finite real")
    return out

def _phase_vector(phi):
    try: out=np.asarray(phi,dtype=np.float64)
    except (TypeError,ValueError,OverflowError) as exc: raise PlatonicRamanujanStabilizerV01Error("phi must be a finite real 36-vector") from exc
    if out.shape!=(N,) or not np.isfinite(out).all(): raise PlatonicRamanujanStabilizerV01Error("phi must be a finite real 36-vector")
    return out.copy()

def icosahedral_adjacency():
    a=np.zeros((N_CHANNELS,N_CHANNELS),dtype=np.float64)
    for i,j in ICOSAHEDRAL_EDGES: a[i,j]=a[j,i]=1.0
    if not np.array_equal(a,a.T) or not np.all(a.sum(1)==CHANNEL_DEGREE): raise AssertionError("invalid icosahedral adjacency")
    return a

def local_k3_adjacency():
    return np.ones((LANES_PER_CHANNEL,LANES_PER_CHANNEL),dtype=np.float64)-np.eye(LANES_PER_CHANNEL)

def adjacency36():
    a=np.kron(icosahedral_adjacency(),np.eye(LANES_PER_CHANNEL))+np.kron(np.eye(N_CHANNELS),local_k3_adjacency())
    if a.shape!=(N,N) or not np.array_equal(a,a.T) or not np.all(a.sum(1)==DEGREE) or np.any(np.diag(a)!=0): raise AssertionError("invalid 36-node carrier")
    return a

def support_mask(): return adjacency36().astype(bool)

def apply_support_mask(g):
    try: x=np.asarray(g,dtype=np.float64)
    except (TypeError,ValueError,OverflowError) as exc: raise PlatonicRamanujanStabilizerV01Error("g must be a finite 36x36 real matrix") from exc
    if x.shape!=(N,N) or not np.isfinite(x).all(): raise PlatonicRamanujanStabilizerV01Error("g must be a finite 36x36 real matrix")
    return np.where(support_mask(),x,0.0)

@dataclass(frozen=True)
class SpectralMetrics:
    degree:int
    nontrivial_radius:float
    ramanujan_bound:float
    normalized_laplacian_gap:float
    is_ramanujan:bool

def spectral_metrics():
    eig=np.sort(np.linalg.eigvalsh(adjacency36()))[::-1]
    if not math.isclose(float(eig[0]),7.0,rel_tol=0.0,abs_tol=1e-12): raise AssertionError("principal eigenvalue mismatch")
    rho=float(np.max(np.abs(eig[1:]))); bound=2*math.sqrt(6.0); gap=1-float(eig[1])/7.0
    return SpectralMetrics(7,rho,bound,gap,bool(rho<=bound+1e-12))

def exact_normalized_gap(): return (5.0-math.sqrt(5.0))/7.0

def linearized_decay_bound(beta):
    b=_finite_real("beta",beta)
    if b<0: raise PlatonicRamanujanStabilizerV01Error("beta must be non-negative")
    return b*exact_normalized_gap()

def stabilizing_coupling(phi:Sequence[float],beta:float)->np.ndarray:
    """Candidate additive regularizer; does not replace parent v0.32 coupling."""
    p=_phase_vector(phi); b=_finite_real("beta",beta)
    if b<0: raise PlatonicRamanujanStabilizerV01Error("beta must be non-negative")
    if b==0: return np.zeros(N,dtype=np.float64)
    a=adjacency36(); diff=p[:,None]-p[None,:]
    return -(b/7.0)*np.sum(a*np.sin(diff),axis=1)

def channel_local_lane(index:int)->tuple[int,int]:
    if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<N: raise PlatonicRamanujanStabilizerV01Error("index must be an integer in [0,35]")
    return divmod(index,LANES_PER_CHANNEL)
