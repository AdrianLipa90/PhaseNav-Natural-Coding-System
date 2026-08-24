from __future__ import annotations
import cmath, json, math, hashlib
from fractions import Fraction
from pathlib import Path
import numpy as np
import mpmath as mp

mp.mp.dps = 60

def C(n:int)->int:
    assert isinstance(n,int) and not isinstance(n,bool) and n>0
    return n//2 if n%2==0 else (3*n+1)//2

def orbit(start,steps):
    xs=[start]
    for _ in range(steps): xs.append(C(xs[-1]))
    return xs

def weight_direct(xs,s):
    w=1+0j
    odd=0
    for a,b in zip(xs[:-1],xs[1:]):
        r=b/a
        bit=a&1
        odd+=bit
        w*=cmath.exp(-s*math.log(r))*((-1)**bit)
    return w

def weight_fact(xs,s):
    odd=sum(x&1 for x in xs[:-1])
    r=xs[-1]/xs[0]
    return cmath.exp(-s*math.log(r))*((-1)**odd)

def factor(n):
    d={}
    x=n
    p=2
    while p*p<=x:
        while x%p==0:
            d[p]=d.get(p,0)+1; x//=p
        p=3 if p==2 else p+2
    if x>1:d[x]=d.get(x,0)+1
    return d

def valuation_flux(a,b):
    fa,fb=factor(a),factor(b)
    ps=set(fa)|set(fb)
    return {p:fb.get(p,0)-fa.get(p,0) for p in ps if fb.get(p,0)!=fa.get(p,0)}

def prime_ratio(flux):
    out=Fraction(1,1)
    for p,e in flux.items():
        out*= Fraction(p**e,1) if e>=0 else Fraction(1,p**(-e))
    return out

def fuzz(omegas, probs, t):
    A=sum(p*cmath.exp(-1j*w*t) for w,p in zip(omegas,probs))
    return 1-abs(A)**2

checks=[]
def check(name,cond,detail=None):
    if not cond: raise AssertionError(f'{name}: {detail}')
    checks.append({'name':name,'status':'PASS','detail':detail})

# 1 theta modular
def theta(t):
    return mp.jtheta(3,0,mp.e**(-mp.pi*t))
for t in [mp.mpf('0.13'),mp.mpf('0.7'),mp.mpf('2.3'),mp.mpf('9.1')]:
    err=abs(theta(t)-t**(-mp.mpf('0.5'))*theta(1/t))
    check(f'theta_modular_{t}', err < mp.mpf('1e-48'), str(err))

# theta Mellin relation; transform the (0,1) part with modular inversion so numerical evaluation only uses t>=1
s=mp.mpf('2.5')
I_hi=mp.quad(lambda u:(theta(u)-1)*u**(s/2-1), [1, mp.inf])
I_lo=mp.quad(lambda u:theta(u)*u**(-(s+1)/2) - u**(-s/2-1), [1, mp.inf])
lhs=I_lo+I_hi
rhs=2*mp.pi**(-s/2)*mp.gamma(s/2)*mp.zeta(s)
check('theta_mellin_zeta',abs(lhs-rhs)<mp.mpf('1e-40'),str(abs(lhs-rhs)))

# xi reflection
def xi(z): return mp.mpf('0.5')*z*(z-1)*mp.pi**(-z/2)*mp.gamma(z/2)*mp.zeta(z)
for z in [mp.mpc('0.2','3.1'),mp.mpc('0.5','14.134725'),mp.mpc('1.7','2.2')]:
    err=abs(xi(z)-xi(1-z))
    check(f'xi_reflection_{z}',err<mp.mpf('1e-45'),str(err))

# Collatz orbit factorization
probes=[0.5+0j,0.5+1.25j,0.31+2.7j,1.2-0.8j]
maxerr=0.0
for seed in range(1,401):
    xs=orbit(seed,40)
    for z in probes:
        e=abs(weight_direct(xs,z)-weight_fact(xs,z))
        maxerr=max(maxerr,e)
check('collatz_orbit_factorization_400x4',maxerr<1e-11,maxerr)

# defect identity and half-axis nonclosed
xs=orbit(27,17); L=math.log(xs[-1]/xs[0])
for sig in [0.2,0.5,0.8,1.3]:
    z=sig+1.7j
    ws=weight_fact(xs,z); wc=weight_fact(xs,1-z)
    d=(math.log(abs(ws))-math.log(abs(wc)))**2
    exact=(2*sig-1)**2*L**2
    check(f'defect_sigma_{sig}',abs(d-exact)<1e-12,(d,exact))
check('half_axis_nonclosed_unique_control',abs(L)>1e-12 and (2*0.5-1)**2*L**2==0.0)

# closed path degeneracy and sign holonomy
cycle=[1,2,1]
for sig in [0.1,0.5,1.4]:
    z=sig+2.0j
    ws=weight_fact(cycle,z); wc=weight_fact(cycle,1-z)
    check(f'closed_defect_degenerate_{sig}',abs(math.log(abs(ws))-math.log(abs(wc)))<1e-14)
check('one_loop_minus_one',abs(weight_fact(cycle,0.37+5j)+1)<1e-14,weight_fact(cycle,0.37+5j))
double=[1,2,1,2,1]
check('double_loop_plus_one',abs(weight_fact(double,0.37+5j)-1)<1e-14,weight_fact(double,0.37+5j))

# critical conjugate
xs=orbit(97,33)
for tau in [0.0,0.3,7.1,14.134725]:
    a=weight_fact(xs,0.5+1j*tau); b=weight_fact(xs,0.5-1j*tau)
    check(f'critical_conjugate_{tau}',abs(b-a.conjugate())<1e-12,abs(b-a.conjugate()))

# prime valuation / prime flux exactness across steps
prime_ok=True
prime_steps=0
for seed in range(1,301):
    xs=orbit(seed,25)
    for a,b in zip(xs[:-1],xs[1:]):
        prime_steps += 1
        if prime_ratio(valuation_flux(a,b)) != Fraction(b,a):
            prime_ok=False; break
    if not prime_ok: break
check('prime_flux_exact_steps',prime_ok,{'steps':prime_steps})
# endpoint sum flux
xs=orbit(871,60)
agg={}
for a,b in zip(xs[:-1],xs[1:]):
    for p,e in valuation_flux(a,b).items(): agg[p]=agg.get(p,0)+e
agg={p:e for p,e in agg.items() if e}
check('prime_flux_telescopes_endpoint',prime_ratio(agg)==Fraction(xs[-1],xs[0]),agg)

# T36 pair geometry
xs=orbit(27,17); odd=sum(x&1 for x in xs[:-1]); L=math.log(xs[-1]/xs[0]); taus=[0.11*(j+1) for j in range(18)]
angles=[]
for tau in taus:
    angles += [ (math.pi*odd-tau*L)%(2*math.pi), (math.pi*odd+tau*L)%(2*math.pi) ]
check('t36_pair_len',len(angles)==36)
check('t36_pair_finite',all(math.isfinite(x) and 0<=x<2*math.pi for x in angles))

# FFT control: uniform modes, DFT/ifft equivalence under numpy convention
N=32
rng=np.random.default_rng(1234)
coeff=rng.normal(size=N)+1j*rng.normal(size=N)
# np.fft.ifft = (1/N) sum C_k exp(+2pi i kn/N); choose direct same convention
m=np.arange(N)
k=np.arange(N)
direct=np.array([(coeff*np.exp(2j*np.pi*k*mi/N)).sum()/N for mi in m])
fast=np.fft.ifft(coeff)
check('uniform_fft_direct_equivalence',float(np.max(np.abs(direct-fast)))<1e-12,float(np.max(np.abs(direct-fast))))

# fuzziness invariants
check('fuzz_zero_time',abs(fuzz([1.0,2.5,4.0],[0.2,0.3,0.5],0.0))<1e-15)
vals=[fuzz([1.0,2.5,4.0],[0.2,0.3,0.5],t) for t in np.linspace(0,20,501)]
check('fuzz_bounds',min(vals)>-1e-12 and max(vals)<1+1e-12,(min(vals),max(vals)))
check('single_mode_fuzz_zero',max(abs(fuzz([3.7],[1.0],t)) for t in np.linspace(0,10,100))<1e-14)
# two equal modes 0,w => F=sin^2(wt/2)
w=2.7
errs=[]
for t in np.linspace(0,5,100): errs.append(abs(fuzz([0,w],[0.5,0.5],t)-math.sin(w*t/2)**2))
check('two_mode_exact_fuzz',max(errs)<1e-13,max(errs))
# small-time variance
omegas=np.array([0.7,1.4,3.9]); probs=np.array([0.2,0.5,0.3]); mu=(omegas*probs).sum(); var=((omegas-mu)**2*probs).sum(); t=1e-4
ratio=fuzz(omegas,probs,t)/(var*t*t)
check('small_time_variance_law',abs(ratio-1)<2e-7,ratio)

report={'schema':'PHASENAV_HOLONOMIC_TEMPORAL_ARITHMETIC_VALIDATION_V0_2','checks':checks,'passed':len(checks),'failed':0,'status':'PASS'}
out=Path('/mnt/data/phasenav_holonomic_temporal_arithmetic_v02/validation/VALIDATION_REPORT_V0_2.json')
out.write_text(json.dumps(report,indent=2,default=str))
print(json.dumps({'status':'PASS','checks':len(checks),'max_factorization_error':maxerr,'report':str(out)},indent=2))
