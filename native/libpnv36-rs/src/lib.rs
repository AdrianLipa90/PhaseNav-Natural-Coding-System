//! Native 36D execution primitives for PhaseNav.
//!
//! PhaseNav owns the semantic contract. This crate provides a compact native
//! execution layer for exact finite 36D `f64` states and equivalence-gated CPU
//! acceleration.

use core::cmp::Ordering;

pub const DIM: usize = 36;
pub const TAU: f64 = core::f64::consts::TAU;
pub const PI: f64 = core::f64::consts::PI;
pub const ABI_VERSION: u32 = 1;

#[repr(C, align(32))]
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Phi36 {
    x: [f64; DIM],
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Phi36Error {
    NonFinite { index: usize },
    InvalidK { k: usize, len: usize },
    InvalidDimension { expected: usize, got: usize },
}

impl Phi36 {
    #[inline]
    pub fn new(x: [f64; DIM]) -> Result<Self, Phi36Error> {
        validate_finite(&x)?;
        Ok(Self { x })
    }

    #[inline]
    const fn from_finite_unchecked(x: [f64; DIM]) -> Self {
        Self { x }
    }

    #[inline]
    pub fn as_array(&self) -> &[f64; DIM] {
        &self.x
    }

    /// Strictly decode a runtime vector; no padding, truncation or coercion.
    #[inline]
    pub fn try_from_slice(values: &[f64]) -> Result<Self, Phi36Error> {
        if values.len() != DIM {
            return Err(Phi36Error::InvalidDimension {
                expected: DIM,
                got: values.len(),
            });
        }
        let mut x = [0.0; DIM];
        x.copy_from_slice(values);
        Self::new(x)
    }

    /// Directed signed phase differences (from -> self), in [-pi, pi].
    ///
    /// Each argument is reduced separately to prevent subtraction overflow
    /// for finite values near +/- f64::MAX. This extension is not claimed to be
    /// bit-identical to Python atan2(sin(to-from), cos(to-from)).
    #[inline]
    pub fn signed_delta_radians_from(&self, from: &Self) -> Self {
        let mut out = [0.0; DIM];
        for (i, out_i) in out.iter_mut().enumerate() {
            let a = from.x[i].rem_euclid(TAU);
            let b = self.x[i].rem_euclid(TAU);
            let delta = b - a;
            *out_i = delta.sin().atan2(delta.cos());
        }
        Self::from_finite_unchecked(out)
    }

    #[inline]
    pub fn wrapped_delta_radians(&self, other: &Self) -> Self {
        let mut out = [0.0; DIM];
        let mut i = 0;
        while i < DIM {
            // Reduce each finite coordinate before subtraction. Directly
            // subtracting opposite-sign extreme finite f64 values can overflow
            // to infinity and turn rem_euclid into NaN.
            let a = self.x[i].rem_euclid(TAU);
            let b = other.x[i].rem_euclid(TAU);
            let d = (a - b).rem_euclid(TAU);
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
            // The same pre-reduction is required for turn coordinates: the
            // raw difference of two finite values is not guaranteed finite.
            let a = self.x[i].rem_euclid(1.0);
            let b = other.x[i].rem_euclid(1.0);
            out[i] = ((b - a) + 0.5).rem_euclid(1.0) - 0.5;
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

/// Scalar two-argument angle, matching the canonical atan2 argument order.
/// Input type is f64: booleans/strings never enter this native function.
#[inline]
pub fn atan2_finite(y: f64, x: f64) -> Result<f64, Phi36Error> {
    if !y.is_finite() {
        return Err(Phi36Error::NonFinite { index: 0 });
    }
    if !x.is_finite() {
        return Err(Phi36Error::NonFinite { index: 1 });
    }
    Ok(y.atan2(x))
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
    // Multiplication is lane-local. Reduction stays in canonical scalar index
    // order so the strict path keeps the reference reduction ordering.
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

#[no_mangle]
pub extern "C" fn pnv36_abi_version() -> u32 {
    ABI_VERSION
}

#[no_mangle]
pub extern "C" fn pnv36_phi_bytes() -> usize {
    core::mem::size_of::<Phi36>()
}

#[no_mangle]
pub extern "C" fn pnv36_has_avx2() -> u32 {
    #[cfg(target_arch = "x86_64")]
    {
        return u32::from(std::is_x86_feature_detected!("avx2"));
    }
    #[allow(unreachable_code)]
    0
}

/// C ABI entrypoint for strict 36D wrapped radial distance.
///
/// Return codes: 0=PASS, 2=null pointer, 3=non-finite input.
///
/// # Safety
/// `a` and `b` must each point to at least 36 readable `f64` values and `out`
/// must point to one writable `f64` value.
#[no_mangle]
pub unsafe extern "C" fn pnv36_distance_radians_strict(
    a: *const f64,
    b: *const f64,
    out: *mut f64,
) -> i32 {
    if a.is_null() || b.is_null() || out.is_null() {
        return 2;
    }

    let mut aa = [0.0; DIM];
    let mut bb = [0.0; DIM];
    unsafe {
        core::ptr::copy_nonoverlapping(a, aa.as_mut_ptr(), DIM);
        core::ptr::copy_nonoverlapping(b, bb.as_mut_ptr(), DIM);
    }

    let aa = match Phi36::new(aa) {
        Ok(v) => v,
        Err(_) => return 3,
    };
    let bb = match Phi36::new(bb) {
        Ok(v) => v,
        Err(_) => return 3,
    };

    unsafe {
        *out = distance_radians_strict(&aa, &bb);
    }
    0
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
    fn strict_slice_requires_36_finite_coordinates() {
        assert!(matches!(
            Phi36::try_from_slice(&[0.0; DIM - 1]),
            Err(Phi36Error::InvalidDimension { expected: DIM, got: 35 })
        ));
        assert!(matches!(
            Phi36::try_from_slice(&[0.0; DIM + 1]),
            Err(Phi36Error::InvalidDimension { expected: DIM, got: 37 })
        ));
        let mut nonfinite = [0.0; DIM];
        nonfinite[35] = f64::INFINITY;
        assert_eq!(Phi36::try_from_slice(&nonfinite), Err(Phi36Error::NonFinite { index: 35 }));
        assert!(Phi36::try_from_slice(&[0.0; DIM]).is_ok());
    }

    #[test]
    fn atan2_finite_checks_arguments_and_quadrants() {
        assert_eq!(atan2_finite(0.0, 1.0).unwrap(), 0.0);
        assert_eq!(atan2_finite(1.0, 0.0).unwrap(), PI / 2.0);
        assert_eq!(atan2_finite(0.0, -1.0).unwrap().abs(), PI);
        assert_eq!(atan2_finite(-1.0, 0.0).unwrap(), -PI / 2.0);
        assert_eq!(atan2_finite(f64::NAN, 1.0), Err(Phi36Error::NonFinite { index: 0 }));
        assert_eq!(atan2_finite(1.0, f64::INFINITY), Err(Phi36Error::NonFinite { index: 1 }));
    }

    #[test]
    fn directed_signed_delta_retains_orientation_and_wraps() {
        let from = Phi36::new([0.1; DIM]).unwrap();
        let to = Phi36::new([TAU - 0.1; DIM]).unwrap();
        let forward = to.signed_delta_radians_from(&from);
        let backward = from.signed_delta_radians_from(&to);
        for i in 0..DIM {
            assert!((forward.x[i] + 0.2).abs() < 2.0e-14);
            assert!((backward.x[i] - 0.2).abs() < 2.0e-14);
            assert!((forward.x[i] + backward.x[i]).abs() < 1.0e-14);
        }
    }

    #[test]
    fn directed_signed_delta_handles_extreme_finite_angles() {
        let from = Phi36::new([-f64::MAX; DIM]).unwrap();
        let to = Phi36::new([f64::MAX; DIM]).unwrap();
        let delta = to.signed_delta_radians_from(&from);
        assert!(delta.as_array().iter().all(|v| v.is_finite() && v.abs() <= PI));
    }

    #[test]
    fn phi36_is_exactly_288_bytes_and_32_aligned() {
        assert_eq!(core::mem::size_of::<Phi36>(), 288);
        assert_eq!(core::mem::align_of::<Phi36>(), 32);
        assert_eq!(pnv36_phi_bytes(), 288);
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
        let ab = a.wrapped_delta_radians(&b);
        let ba = b.wrapped_delta_radians(&a);
        for i in 0..DIM {
            assert!((ab.x[i] - ba.x[i]).abs() <= f64::EPSILON * 4.0);
        }
    }

    #[test]
    fn wrapped_delta_keeps_extreme_finite_inputs_finite() {
        let a = Phi36::new([f64::MAX; DIM]).unwrap();
        let b = Phi36::new([-f64::MAX; DIM]).unwrap();
        let d = a.wrapped_delta_radians(&b);
        for value in d.x {
            assert!(value.is_finite());
            assert!((0.0..=PI).contains(&value));
        }
        assert!(distance_radians_strict(&a, &b).is_finite());
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
    fn torus_turn_delta_keeps_extreme_finite_inputs_finite() {
        let a = Phi36::new([f64::MAX; DIM]).unwrap();
        let b = Phi36::new([-f64::MAX; DIM]).unwrap();
        let d = a.signed_torus_delta_turns(&b);
        for value in d.x {
            assert!(value.is_finite());
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

    #[test]
    fn ffi_distance_matches_native_path() {
        let a = sample(0.2);
        let b = sample(1.1);
        let mut out = -1.0;
        let status = unsafe {
            pnv36_distance_radians_strict(a.x.as_ptr(), b.x.as_ptr(), &mut out)
        };
        assert_eq!(status, 0);
        assert_eq!(out.to_bits(), distance_radians_strict(&a, &b).to_bits());
    }
}
