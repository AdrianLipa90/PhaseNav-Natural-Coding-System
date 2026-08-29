//! Native 36D execution primitives for PhaseNav.
//!
//! PhaseNav owns the semantic contract. This crate provides a compact native
//! execution layer for exact finite 36D `f64` states and equivalence-gated CPU
//! acceleration.

use core::cmp::Ordering;

pub const DIM: usize = 36;
pub const TAU: f64 = core::f64::consts::TAU;
pub const PI: f64 = core::f64::consts::PI;

#[repr(C, align(32))]
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Phi36 {
    pub x: [f64; DIM],
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Phi36Error {
    NonFinite { index: usize },
    InvalidK { k: usize, len: usize },
}

impl Phi36 {
    #[inline]
    pub fn new(x: [f64; DIM]) -> Result<Self, Phi36Error> {
        validate_finite(&x)?;
        Ok(Self { x })
    }

    #[inline]
    pub const fn from_finite_unchecked(x: [f64; DIM]) -> Self {
        Self { x }
    }

    #[inline]
    pub fn as_array(&self) -> &[f64; DIM] {
        &self.x
    }

    #[inline]
    pub fn wrapped_delta_radians(&self, other: &Self) -> Self {
        let mut out = [0.0; DIM];
        let mut i = 0;
        while i < DIM {
            let d = (self.x[i] - other.x[i]).rem_euclid(TAU);
            out[i] = if d > PI { TAU - d } else { d };
            i += 1;
        }
        Self::from_finite_unchecked(out)
    }

    #[inline]
    pub fn signed_torus_delta_turns(&self, other: &Self) -> Self {
        let mut out = [0.0; DIM];
        let mut i = 0;
        while i < DIM {
            out[i] = ((other.x[i] - self.x[i]) + 0.5).rem_euclid(1.0) - 0.5;
            i += 1;
        }
        Self::from_finite_unchecked(out)
    }
}

#[inline]
pub fn validate_finite(x: &[f64; DIM]) -> Result<(), Phi36Error> {
    let mut i = 0;
    while i < DIM {
        if !x[i].is_finite() {
            return Err(Phi36Error::NonFinite { index: i });
        }
        i += 1;
    }
    Ok(())
}

#[inline]
fn l2_sq_scalar(x: &[f64; DIM]) -> f64 {
    let mut sum = 0.0;
    let mut i = 0;
    while i < DIM {
        sum += x[i] * x[i];
        i += 1;
    }
    sum
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn square_lanes_avx2(x: &[f64; DIM]) -> [f64; DIM] {
    use core::arch::x86_64::{_mm256_loadu_pd, _mm256_mul_pd, _mm256_storeu_pd};

    let mut squared = [0.0; DIM];
    let mut i = 0;
    while i < DIM {
        // SAFETY: `i` advances in blocks of four and DIM is exactly 36, so each
        // load/store addresses four valid contiguous `f64` values.
        let v = unsafe { _mm256_loadu_pd(x.as_ptr().add(i)) };
        let vv = _mm256_mul_pd(v, v);
        unsafe { _mm256_storeu_pd(squared.as_mut_ptr().add(i), vv) };
        i += 4;
    }
    squared
}

#[cfg(target_arch = "x86_64")]
#[inline]
fn l2_sq_avx2_strict(x: &[f64; DIM]) -> f64 {
    // Vector multiplication is lane-local. The reduction is then performed in
    // canonical scalar index order to preserve the strict reduction ordering.
    let squared = unsafe { square_lanes_avx2(x) };
    let mut sum = 0.0;
    let mut i = 0;
    while i < DIM {
        sum += squared[i];
        i += 1;
    }
    sum
}

#[inline]
pub fn l2_sq_strict(v: &Phi36) -> f64 {
    #[cfg(target_arch = "x86_64")]
    {
        if std::is_x86_feature_detected!("avx2") {
            return l2_sq_avx2_strict(&v.x);
        }
    }
    l2_sq_scalar(&v.x)
}

#[inline]
pub fn l2_strict(v: &Phi36) -> f64 {
    l2_sq_strict(v).sqrt()
}

#[inline]
pub fn distance_radians_strict(a: &Phi36, b: &Phi36) -> f64 {
    l2_strict(&a.wrapped_delta_radians(b))
}

#[inline]
pub fn angular_distance_radians_strict(a: &Phi36, b: &Phi36) -> f64 {
    distance_radians_strict(a, b) / (DIM as f64).sqrt()
}

pub fn nearest_k_radians_strict(
    target: &Phi36,
    candidates: &[Phi36],
    k: usize,
) -> Result<Vec<(usize, f64)>, Phi36Error> {
    if k == 0 || k > candidates.len() {
        return Err(Phi36Error::InvalidK {
            k,
            len: candidates.len(),
        });
    }

    let mut scored = Vec::with_capacity(candidates.len());
    for (index, candidate) in candidates.iter().enumerate() {
        scored.push((index, distance_radians_strict(target, candidate)));
    }

    scored.sort_by(|(ia, da), (ib, db)| match da.partial_cmp(db) {
        Some(Ordering::Equal) => ia.cmp(ib),
        Some(order) => order,
        None => Ordering::Equal,
    });
    scored.truncate(k);
    Ok(scored)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample(offset: f64) -> Phi36 {
        let mut x = [0.0; DIM];
        let mut i = 0;
        while i < DIM {
            x[i] = offset + (i as f64) * 0.03125;
            i += 1;
        }
        Phi36::new(x).unwrap()
    }

    #[test]
    fn phi36_is_exactly_288_bytes_and_32_aligned() {
        assert_eq!(core::mem::size_of::<Phi36>(), 288);
        assert_eq!(core::mem::align_of::<Phi36>(), 32);
    }

    #[test]
    fn rejects_non_finite_coordinates() {
        let mut x = [0.0; DIM];
        x[17] = f64::NAN;
        assert_eq!(Phi36::new(x), Err(Phi36Error::NonFinite { index: 17 }));
    }

    #[test]
    fn wrapped_delta_is_symmetric_in_magnitude() {
        let a = sample(0.1);
        let b = sample(5.9);
        assert_eq!(a.wrapped_delta_radians(&b), b.wrapped_delta_radians(&a));
    }

    #[test]
    fn torus_turn_delta_is_bounded() {
        let a = sample(0.1);
        let b = sample(0.9);
        let d = a.signed_torus_delta_turns(&b);
        for value in d.x {
            assert!((-0.5..0.5).contains(&value));
        }
    }

    #[test]
    fn strict_l2_matches_scalar_reference_bitwise() {
        let v = sample(0.25);
        assert_eq!(l2_sq_strict(&v).to_bits(), l2_sq_scalar(&v.x).to_bits());
    }

    #[test]
    fn nearest_k_has_stable_index_tie_break() {
        let target = sample(0.0);
        let c0 = sample(0.2);
        let c1 = sample(0.1);
        let c2 = sample(0.1);
        let got = nearest_k_radians_strict(&target, &[c0, c1, c2], 2).unwrap();
        assert_eq!(got[0].0, 1);
        assert_eq!(got[1].0, 2);
    }
}
