# PNCS Nonlinear Coframe Incompatibility Firewall v0.1
Date: 2026-09-26
Status: CANDIDATE / RAW_CURL_CURVATURE_NO_GO / NON-CANON

A coframe/triad array and a material deformation gradient may share matrix
shape while carrying different semantics.

Countercontrols:
- E=R_z(theta(x,y)) can have Curl E != 0 with h=E^T E=I and zero curvature;
- the conformal nonflat triad can have Curl E=0 at a point while intrinsic
  curvature is nonzero there.

Therefore raw row-wise Curl of a coframe is not an intrinsic nonlinear
curvature observable.

The correct nonlinear geometric hierarchy is

    e -> declared connection omega -> Omega=domega+omega wedge omega -> Riemann.

Material Curl F remains a compatibility/defect diagnostic only in its typed
material role.

Independent validation: PASS.

canon_allowed=false
