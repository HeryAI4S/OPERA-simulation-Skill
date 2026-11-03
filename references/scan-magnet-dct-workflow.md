# Scan-magnet integral field and DCT adjustment

Use this workflow for two-axis scan-magnet field quality, DCT angular-distribution
adjustments, pole-turn placement and related COMI handoffs. The included helper
adds Post preparation and numerical auditing to an existing project; it neither
creates a new engineering project nor runs OPERA.

中文：本功能来自双向扫描磁铁的工程工作流。保留用户已选定的拓扑和串联方式；
固定网格与采样比较设计变化，分别报告几何检查、真实求解、数值达标和收敛验收。

## Preserve the actual design contract

Record the supplied aperture, mechanical envelope, excitation scenarios, main
field directions, good-field domain, integral target and tolerance definition.
Distinguish X/Y-labelled winding families from independently driven X/Y circuits;
a common series drive does not establish independent scan control. Do not change
layer currents to improve a series-connected design.

A possible project contract is a six-layer `XYYXXY` conformal BR20 source with two
radially stacked, series-connected physical hollow conductors represented by one
equivalent source. In that representation, the equivalent source carries `2I`.
Keep its radial/tangential dimensions and orientation literal. Evaluate cooling,
copper current density and resistance on the physical conductors. The equivalent
source current density is not the physical hollow-conductor copper density.
These are example project constraints, not defaults for every DCT magnet.

Before relying on half-z symmetry, confirm the reflection signs of the field
components and the integrated quantity. Integrating from negative to positive z
with the reflected solution already active must not receive another factor of
two. Energy, co-energy and selected-volume integrals can have different native
replication conventions. A BR20 Jacobian/conformal certificate does not establish
all interturn/end-turn clearances or physical insulation thickness.

## Optimize geometry with comparable field samples

Freeze the evaluation mesh settings, integration ranges, field sampling and
excitation when comparing nearby design candidates. Changing geometry can change
mesh topology even with identical size settings; keep mesh counts and monitor the
effect. Refine a retained candidate when final evidence requires it. Do not replace
requested design optimization with repeated refinement of unchanged geometry.

Inspect signed spatial integral residuals before choosing higher-order terms.
Keep the dipole main order fixed. For a project using
`cos(phi) + a1*sin(2*phi) + a2*sin(3*phi)`, changing the main order from 1 to 2
changes the main field family. Check phase conventions for every winding family;
the trigonometric order of a stream-function term is not automatically the same
as the measured field multipole order. Do not remove a quadrupole or fitted slope
from the acceptance metric unless the physical specification explicitly allows it.
Compensation discussed for an arced DCT magnet is not automatically appropriate
for a straight magnet.

Use a baseline and small positive/negative perturbations on the same evaluation
setup to estimate a response direction. A change in current or aperture between
two nonlinear solves confounds a finite-difference geometry sensitivity. Any
transferred or extrapolated response is a prediction until the new candidate is
solved; a material improvement must exceed evaluation variability.

If a global coefficient improves one axis but provides little margin on the
limiting axis, consider local pole-turn placement. For contour levels
`p_i=(i-0.5)/N`, adjusting the largest absolute level changes the pole-nearest
closed contours. Apply the matching positive/negative changes needed by the
actual winding symmetry. Preserve loop closure, current sense, turn counts,
local frames and conductor cross sections. Measure actual centreline movement,
minimum gaps and the full mechanical envelope after regeneration; do not infer
manufacturability from a small coefficient alone. Compare per-loop file hashes
to establish which loops changed. A midplane gap is not a full 3D gap check.

## Define and prepare the integral-field calculation

For the common project coordinate convention, X scanning uses `BY` and Y
scanning uses `BX`. Confirm this convention or supply explicit components.
For each fixed transverse point, integrate the **signed component** along z:

`I_d(x,y;L) = integral[-L,+L] B_component(x,y,z) dz`

`U_d(R) = 100 * max_{x*x+y*y<=R*R} abs(I_d(x,y)-I_d(0,0)) / abs(I_d(0,0))`

The centre normalization differs from peak-to-peak span, disk-mean normalization,
RMS error and normalization by the specified target. The helper reports centre
target error separately. A signed centre integral may be negative; use its
absolute value in the denominator. Use units T*m; in a mm/T Post session the
native line integral is divided by 1000. Capture `INTEGRAL` immediately after
each component's `PLOT` before the next command changes that system value.

Mechanical length is not the integration length: fringe fields also contribute.
Select L from the actual field and previous range checks, not a universal length
or a large arbitrary constant. The helper requires both L and a shorter check
range. It compares the two centre integrals and endpoint/centre field ratios.
That is a **centre-ray diagnostic**, not a bound on all omitted fringe-field
integrals. Check further ranges and off-axis worst rays when needed to establish
uniformity stability; report changes in uniformity in percentage points.

For an existing solved database, prepare a separate Post directory:

```powershell
python scripts/field_quality.py prepare --database ./existing-case/magnet.op3 --out ./post-screen --half-range-mm 950 --check-range-mm 850 --inner-radius-mm 25 --outer-radius-mm 35 --target-tm 0.20 --rings 14 --angles 64 --axial-step-mm 5
python scripts/comi_preflight.py ./post-screen
```

The numerical values above are an example inherited from one scan-magnet study,
not universal acceptance settings. By default the screening grid has 14 rings,
64 angles, and a nominal 5 mm axial sample setting. A denser grid is explicit,
for example `--rings 56 --angles 256 --axial-step-mm 1.25`. The inner radius must
coincide with a sampling ring. Match the installed release's `LINE NP` semantics;
the axial setting describes the requested sampling, not an integration-error bound.

The helper creates `post_integrated_field.comi` and `field_quality.json`, refuses
an existing output directory and never launches OPERA. It derives quoted paths
from the supplied arguments. A database may be named before it exists, but that
is recorded without a source hash and does not establish a solved case. Once a
source hash has been recorded, a changed/missing database is rejected during
evaluation. Use a new Post directory after any intended database/COMI change.

The generated COMI activates the named database and simulation, integrates each
component, checks the centre-range diagnostics, samples the disk, and writes:

| Output | Contents |
|---|---|
| `field_raw.dat`, type 70 | 12 columns: type, axis, sample, ring, x, y, radius, angle degrees, half-range, signed integral, nominal axial step, simulation |
| `field_summary.dat`, type 90 | type, axis, centre integral, target error %, inner U %, outer U %, worst x, worst y, half-range, nominal axial step, rings, angles |
| `field_summary.dat`, type 91 | type, axis, shorter-range integral, centre integral, increment %, endpoint %, centre field, negative endpoint field, positive endpoint field, shorter half-range, half-range, nominal axial step |

Axis 1/2 correspond to the explicitly configured X/Y components. Range-check
failure aborts before the completed type 90 records. Run Post only against the
intended solved database using the installed release's supported launch sequence.
This generated reduction has synthetic/offline validation; successful preparation
or static preflight is not native OPERA execution validation.

After Post finishes, recompute from the raw data independently:

```powershell
python scripts/field_quality.py evaluate ./post-screen/field_quality.json --out ./post-screen/audit.json
```

The audit checks both complete grids, duplicates, nonfinite values, coordinates,
simulation/range/sample metadata, reference denominators, endpoint ratios,
reported extrema and COMI summary consistency. It refuses existing audit output.
`numeric_field_pass` and `center_range_check_pass` describe the supplied numeric
records. They do not certify solver completion, field provenance, sampling
convergence, finite-element mesh convergence or engineering acceptance.

## Evidence required for an engineering claim

Keep the following states separate:

| Evidence | What it supports |
|---|---|
| Prepared COMI and hashed inputs | Reproducible input preparation |
| Conductor/bore/envelope checks | Only the checked geometry properties |
| Completed Modeller/solver/Post logs, result database and raw tables | A real solved case, subject to the actual run checks |
| Complete sampled disk below the chosen tolerance | This case and this sampling grid pass the numeric criterion |
| Nested sampling comparison | Sampling sensitivity at the fixed solved field |
| Same-geometry/current/material mesh comparison | Finite-element mesh sensitivity |
| Full specification and required verification gates | Engineering acceptance |

For the two-radius method, both radii refer to full axial integrals on fixed
transverse straight rays. An entrance/exit aperture specification alone does not
define a circular disk, local sectional field metric, tapered sampling envelope
or bent beam trajectory. Record the selected domain explicitly. Do not present
these integrals as a completed particle-tracking assessment.

When no rerun is authorized, use existing raw data, prepare changes or perform
geometry-only work as requested. Mark linear sensitivity screens and new
geometry candidates as unevaluated. A new `.cond` must not inherit a previous
case's field values, saturation margin or accepted status.
