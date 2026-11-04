# Integrated harmonics: symmetry, identity and numerical diagnostics

Use this reference with [post-processing and field quality](postprocessing-and-field-quality.md) when an octant model feeds a full-circle integral, two transient cases appear to have identical main harmonics, or high orders depend strongly on aperture radius. The checks below were exercised in a straight, global-Z, By-dominant dipole study; other magnet types need their own parity and normalization.

## Verify case identity before comparing coefficients

Record database identity, requested and actually loaded case, numeric time, frame, field component, units, radius, longitudinal limits, angular range, integration intervals and symmetry settings for every result. Keep each case in a separate output directory because many harmonic COMI routines overwrite `harmonic.txt`.

An identity export containing literal `TTIME` is not numeric time evidence. Check the native database case inventory and load transcript, fix the `$FORMAT`/`$ASSIGN` sequence, then regenerate the export. Recovering time from a case number requires the actual saved-state schedule: do not assume that case number equals time-step number. Successful activation does not by itself prove that the requested time was sampled.

Store the raw signed main coefficients and absolute main amplitude with units before normalizing. The main row is always `10000` when it is normalized as `10000 * main/main`; it cannot demonstrate equal absolute fields in two cases. Compare a fixed absolute probe or longitudinal integral as an additional load check. A stale resident case can produce perfectly plausible normalized tables.

When fields are in T and longitudinal integration uses mm, the raw integral is in T mm; divide by `1000` for T m. Record the actual field/length units instead of applying this conversion from a filename or an assumed default. Preserve signed cosine/sine terms; amplitudes alone conceal sign reversal and phase changes. Do not rename them normal/skew until the angle and field convention have been mapped explicitly.

## Restore vector fields using verified parity

For a conventional symmetric By-dominant dipole with centreline Z, the exercised reflection pattern was:

| Coordinate reflection | Bx | By | Bz |
| --- | --- | --- | --- |
| x to -x (YZ plane) | odd | even | even |
| y to -y (ZX plane) | odd | even | odd |
| z to -z (XY plane) | even | even | odd |

These are field-component parities for that excitation and boundary class, not a universal rule for all dipoles, quadrupoles, solenoids or curved magnets. Determine the plane's magnetic boundary and source/current reflection, then obtain the component signs; position reflection alone is insufficient because B is an axial vector and excitation symmetry matters. Validate mirror-related components at nonzero interior points against an available full/independent model or symmetry reconstruction. Check the vanishing odd component at each plane and continuity across reconstruction seams. The boundary-plane checks alone cannot prove the entire reflected solution correct.

The corresponding 2025 SP1 Post setting exercised for that dipole was:

```text
SYMMETRY MODELSYMMETRY=USER RXY=YES RYZ=YES RZX=INVERSE SYMMETRY=1 XORIGIN=0 YORIGIN=0 ZORIGIN=0 THETA=0 PHI=0 PSI=0 SAVE=NO
```

Verify these keyword meanings against the installed release and model; select this temporary symmetry after loading the intended case and before full-circle sampling. Do not copy it into the quadrupole branch of a generic template. `SAVE=NO` avoids persisting the temporary symmetry setting in this workflow; also verify the source file stayed unchanged.

With `x=r cos(theta)`, `y=r sin(theta)` and global components, explicitly form:

`Br = Bx cos(theta) + By sin(theta)`.

For this dipole, uniform `By=B0` gives `Br=B0 sin(theta)`, hence radial-field order one. Use this analytic identity to test the projection, phase and main-order convention. For a normal quadrupole `Bx=G*y`, `By=G*x`, it gives `Br=G*r*sin(2*theta)`, hence order two. Reconstruct the component vector, then project; reflecting Br as an unsigned scalar or multiplying its full-circle integral by eight does not reproduce the vector field.

For a complete `0..2*pi` cylindrical surface, Fourier projection divides the mapped surface integral by `pi*r` for nonzero orders under the stated convention; order zero needs its own factor of two. A reduced angular range needs its own normalization. Confirm the patch measure, radius, azimuth units, angle convention and interval-versus-point count. A discrete Fourier routine should handle the repeated `0/360` endpoint consistently rather than counting it twice as an independent sample.

## Diagnose high orders one numerical control at a time

Use independent checks with the field solution held fixed, then refine the field solution separately:

| Change | What it tests | What it does not establish |
| --- | --- | --- |
| Increase azimuthal integration intervals | Angular aliasing/quadrature sensitivity | Finite-element field accuracy |
| Increase longitudinal intervals | Sampling of fringe-field variation | Adequate integration endpoints or solved mesh |
| Extend longitudinal limits | Truncated end-field contribution | Mesh/time-step convergence |
| Change reference radius within the aperture | Expected radial multipole scaling and numerical floor | Automatic proof that high orders are physical or numerical |
| Refine solved mesh and time stepping | Field-solution convergence | Correct harmonic definition or symmetry |

For a source-free, approximately 2D transverse field, raw order-n coefficients scale as `r^(n-1)`. Relative order-n units normalized to an order-m main field scale as `r^(n-m)`; relative dipole harmonics therefore scale as `r^(n-1)`. Compare at a common reference radius using `u_n(r_ref) = u_n(r) * (r_ref/r)^(n-m)` before calling a radius trend an error. This is a diagnostic approximation for a finite-length 3D integration: end fields and finite endpoints can violate the strict 2D assumptions.

High orders can shrink by orders of magnitude when radius decreases even for a valid harmonic field. Values that approach a numerical floor should not be interpreted by relative percentage changes or fitted precise power laws. Stable harmonics under angular/longitudinal refinement demonstrate post-processing sampling stability, not finite-element mesh independence. Similar high orders in conductivity-on/off cases do not alone identify their cause: geometry, source discretization, interpolation, truncation and transient physics still need separation.

When the main amplitude is below a declared physical/numerical threshold, report normalization as undefined, retain raw coefficients and mark the comparison unusable. Returning an all-zero normalized table after setting the normalization factor to zero conceals this failure.

## Acceptance examples

- An octant export and solver total agree exactly: classify this as same-domain closure until physical reconstruction is demonstrated.
- Two cases have main rows of `10000` but absolute main integrals of `3.00` and `3.01 T m`: report the absolute difference; the normalized identity is not equality evidence.
- A dipole plus sextupole analytic field has an order-three relative term proportional to radius squared. Common-radius conversion should recover the same coefficient within quadrature error.
- Refining only the angle/longitudinal sampling stabilizes orders 13/15/17: report sampling stability and keep mesh/time-step acceptance open.
- Conductivity removal changes both shield and yoke losses: report the change in the solved system separately from direct material attribution, using [native loss auditing](native-loss-and-symmetry-audit.md).
