from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
import hashlib
import numpy as np


class TemporalFibreKernelError(RuntimeError):
    pass


def _require_dense_hermitian(H: np.ndarray, *, atol: float = 1e-12) -> np.ndarray:
    a=np.asarray(H,dtype=np.complex128)
    if a.ndim!=2 or a.shape[0]!=a.shape[1] or a.shape[0]<1:
        raise TemporalFibreKernelError("dense square Hamiltonian required")
    if not np.isfinite(a.real).all() or not np.isfinite(a.imag).all():
        raise TemporalFibreKernelError("Hamiltonian contains non-finite values")
    if not np.allclose(a,a.conj().T,atol=atol,rtol=0.0):
        raise TemporalFibreKernelError("Hamiltonian must be Hermitian")
    return np.ascontiguousarray(a)


def _require_state(psi: np.ndarray, n: int) -> np.ndarray:
    a=np.asarray(psi,dtype=np.complex128).reshape(-1)
    if a.shape!=(n,):
        raise TemporalFibreKernelError(f"state dimension {a.size} != Hamiltonian dimension {n}")
    if not np.isfinite(a.real).all() or not np.isfinite(a.imag).all():
        raise TemporalFibreKernelError("state contains non-finite values")
    return a


def _require_times(values: np.ndarray, *, name: str) -> np.ndarray:
    t=np.asarray(values,dtype=np.float64).reshape(-1)
    if not np.isfinite(t).all():
        raise TemporalFibreKernelError(f"{name} contains non-finite values")
    if np.any(t<0.0):
        raise TemporalFibreKernelError(f"{name} must be non-negative")
    return t


@dataclass(frozen=True)
class PreparedDenseTemporalFibre:
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    hbar: float
    hamiltonian_sha256: str

    @classmethod
    def prepare(cls,H: np.ndarray,*,hbar: float=1.0,atol: float=1e-12) -> "PreparedDenseTemporalFibre":
        if not np.isfinite(hbar) or hbar<=0.0:
            raise TemporalFibreKernelError("hbar must be finite and positive")
        a=_require_dense_hermitian(H,atol=atol)
        vals,vecs=np.linalg.eigh(a)
        digest=hashlib.sha256(a.astype('<c16',copy=False).tobytes(order='C')).hexdigest()
        vals=np.asarray(vals,dtype=np.float64); vecs=np.asarray(vecs,dtype=np.complex128)
        vals.setflags(write=False); vecs.setflags(write=False)
        return cls(vals,vecs,float(hbar),digest)

    @property
    def dimension(self)->int:
        return int(self.eigenvalues.size)

    def evolve(self,psi: np.ndarray,delta_tau: float)->np.ndarray:
        if not np.isfinite(delta_tau) or delta_tau<0.0:
            raise TemporalFibreKernelError("delta_tau must be finite and non-negative")
        state=_require_state(psi,self.dimension)
        coeff=self.eigenvectors.conj().T@state
        phase=np.exp((-1j*float(delta_tau)/self.hbar)*self.eigenvalues)
        return self.eigenvectors@(phase*coeff)

    def trajectory(self,psi0: np.ndarray,tau: np.ndarray)->np.ndarray:
        state=_require_state(psi0,self.dimension)
        times=_require_times(tau,name="tau")
        if times.size==0:
            return np.empty((0,self.dimension),dtype=np.complex128)
        coeff=self.eigenvectors.conj().T@state
        phase=np.exp((-1j/self.hbar)*times[:,None]*self.eigenvalues[None,:])
        # Each row is V @ (phase_k * coeff), written as one BLAS-backed matrix product.
        return (phase*coeff[None,:])@self.eigenvectors.T

    def trajectory_from_increments(self,psi0: np.ndarray,delta_tau: np.ndarray,*,include_initial: bool=False)->np.ndarray:
        increments=_require_times(delta_tau,name="delta_tau")
        cumulative=np.cumsum(increments,dtype=np.float64)
        if include_initial:
            cumulative=np.concatenate((np.array([0.0],dtype=np.float64),cumulative))
        return self.trajectory(psi0,cumulative)

    def local_gate_trajectory(self,psi0: np.ndarray,global_dt: float,local_rate: np.ndarray,*,include_initial: bool=False)->np.ndarray:
        # Computational local phase-time contract: d_tau = local_rate * d_t.
        # local_rate is explicit runtime input; no density/viscosity/BEC law is inferred here.
        if not np.isfinite(global_dt) or global_dt<0.0:
            raise TemporalFibreKernelError("global_dt must be finite and non-negative")
        rate=_require_times(local_rate,name="local_rate")
        return self.trajectory_from_increments(psi0,float(global_dt)*rate,include_initial=include_initial)


def _float64_key(value: float) -> bytes:
    return np.float64(value).tobytes()


@dataclass(frozen=True)
class CompiledTemporalGateSet:
    """Finite exact set of precompiled U(delta_tau) gates for dynamic stepwise flow.

    This deliberately does not infer delta_tau from density, viscosity, or any physical
    medium model. The admitted local-time increments are explicit host inputs.
    """
    hamiltonian_sha256: str
    dimension: int
    delta_tau_values: np.ndarray
    propagators: np.ndarray
    _index: Mapping[bytes, int]

    @classmethod
    def compile(cls, kernel: PreparedDenseTemporalFibre, delta_tau_values: np.ndarray, *, max_gates: int = 64) -> "CompiledTemporalGateSet":
        if not isinstance(kernel, PreparedDenseTemporalFibre):
            raise TemporalFibreKernelError("PreparedDenseTemporalFibre required")
        if not isinstance(max_gates, int) or max_gates < 1:
            raise TemporalFibreKernelError("max_gates must be positive")
        raw=_require_times(delta_tau_values,name="delta_tau_values")
        ordered=[]; seen=set()
        for x in raw:
            key=_float64_key(float(x))
            if key not in seen:
                seen.add(key); ordered.append(float(x))
        if not ordered:
            raise TemporalFibreKernelError("at least one temporal gate is required")
        if len(ordered)>max_gates:
            raise TemporalFibreKernelError("temporal gate set exceeds explicit bound")
        delta=np.asarray(ordered,dtype=np.float64)
        phase=np.exp((-1j/kernel.hbar)*delta[:,None]*kernel.eigenvalues[None,:])
        # U_k = V diag(exp(-i E delta_tau_k / hbar)) V^dagger
        props=np.einsum("ia,ka,ja->kij",kernel.eigenvectors,phase,kernel.eigenvectors.conj(),optimize=True)
        delta.setflags(write=False); props.setflags(write=False)
        index=MappingProxyType({_float64_key(float(x)):i for i,x in enumerate(delta)})
        return cls(kernel.hamiltonian_sha256,kernel.dimension,delta,props,index)

    def step(self, psi: np.ndarray, delta_tau: float) -> np.ndarray:
        if not np.isfinite(delta_tau) or delta_tau<0.0:
            raise TemporalFibreKernelError("delta_tau must be finite and non-negative")
        try:
            idx=self._index[_float64_key(float(delta_tau))]
        except KeyError as exc:
            raise TemporalFibreKernelError("delta_tau is not an explicitly compiled temporal gate") from exc
        state=_require_state(psi,self.dimension)
        return self.propagators[idx]@state

    def compile_schedule(self, delta_tau: np.ndarray) -> "CompiledTemporalSchedule":
        schedule=_require_times(delta_tau,name="delta_tau")
        indices=[]
        for dt in schedule:
            try:
                indices.append(self._index[_float64_key(float(dt))])
            except KeyError as exc:
                raise TemporalFibreKernelError("schedule contains a delta_tau outside the compiled temporal gate set") from exc
        idx=np.asarray(indices,dtype=np.intp); idx.setflags(write=False)
        return CompiledTemporalSchedule(self.hamiltonian_sha256,self.dimension,self.propagators,idx)

    def run_known_schedule(self, psi0: np.ndarray, delta_tau: np.ndarray, *, include_initial: bool=False) -> np.ndarray:
        state=_require_state(psi0,self.dimension).copy()
        schedule=_require_times(delta_tau,name="delta_tau")
        out=[]
        if include_initial: out.append(state.copy())
        for dt in schedule:
            state=self.step(state,float(dt)); out.append(state.copy())
        if not out:
            return np.empty((0,self.dimension),dtype=np.complex128)
        return np.asarray(out)


@dataclass(frozen=True)
class CompiledTemporalSchedule:
    """Validated bounded schedule over a finite CompiledTemporalGateSet."""
    hamiltonian_sha256: str
    dimension: int
    propagators: np.ndarray
    gate_indices: np.ndarray

    def final_state(self, psi0: np.ndarray) -> np.ndarray:
        state=_require_state(psi0,self.dimension).copy()
        for idx in self.gate_indices:
            state=self.propagators[int(idx)]@state
        if not np.isfinite(state.real).all() or not np.isfinite(state.imag).all():
            raise TemporalFibreKernelError("compiled temporal schedule produced non-finite state")
        return state

    def trajectory(self, psi0: np.ndarray, *, include_initial: bool=False) -> np.ndarray:
        state=_require_state(psi0,self.dimension).copy(); out=[]
        if include_initial: out.append(state.copy())
        for idx in self.gate_indices:
            state=self.propagators[int(idx)]@state; out.append(state.copy())
        if not out:
            return np.empty((0,self.dimension),dtype=np.complex128)
        result=np.asarray(out)
        if not np.isfinite(result.real).all() or not np.isfinite(result.imag).all():
            raise TemporalFibreKernelError("compiled temporal schedule produced non-finite trajectory")
        return result
