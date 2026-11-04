# OPERA-3d post-processing, field quality and result transfer

Use this reference after an OPERA-3d solve to construct reproducible field maps, line/circle samples, integrated fields, multipole fits, forces, transient summaries and data exports. It distinguishes native post-processing commands from a user-supplied integrated-harmonic COMI pattern. Confirm command options and unit conventions in the installed release before executing: the local converted manuals contain occasional OCR/transcoding damage.

## Contents

1. [Start with the active result](#start-with-the-active-result)
2. [Coordinate and sampling contract](#coordinate-and-sampling-contract)
3. [Lines, arcs, circles and maps](#lines-arcs-circles-and-maps)
4. [Integrated field and harmonics](#integrated-field-and-harmonics)
5. [Forces, energy and volume quantities](#forces-energy-and-volume-quantities)
6. [Transient and harmonic result discipline](#transient-and-harmonic-result-discipline)
7. [Tables, grids and coupling transfer](#tables-grids-and-coupling-transfer)
8. [Automation and acceptance tests](#automation-and-acceptance-tests)

## Start with the active result

Post-processing uses the database currently made resident by `LOAD`; activating a file is not enough. Record the database filename, case number, time/frequency, local coordinate system, symmetry assumptions and units at the top of every post COMI.

```text
/ Pseudocode: verify exact installed syntax before use
ACTIVATE FILE=case.op3
LOAD
SET ...                 / select output time, phase and/or local frame
/ sample -> reduce -> write case-local result table
```

The available system variables depend on analysis. Magnetostatics offers `POT`, `H`, `HS`, `B`, `ERRB`; transient/motional EM additionally provides quantities such as `A_`, `DADT_`, `E`, `J`, `JM`, `ERRJ`, `LOSS`, `SIBCLOSS`, and transient `HLOSS`. Per-material transient totals can additionally include `JH_<name>`, `EJ_<name>`, and `HLOSS_<name>` when the matching model/material definition provides them. These names have different instantaneous, time-average, and cumulative semantics; use [transient losses and electromagnetic-thermal heat sources](transient-losses.md) before integrating them. For a circuit database, loop/element variables include current and its derivative; a current source does not necessarily expose its voltage. Never reuse a component expression from a static job in a transient/harmonic job without verifying that it is defined.

## Coordinate and sampling contract

### Declare the reference frame

The field vector components (`BX`, `BY`, `BZ`) are global. Sampling positions for `LINE`, `CIRCLE`, `POLAR` and related commands are affected by the local frame selected with `SET`. If local components are required, use the documented rotation matrix (`ROTL11...ROTL33`) or a verified local-frame command; do not rename global components by assumption.

For every result routine, name:

- the beam/magnet coordinate convention and longitudinal coordinate;
- the origin and direction of the reference trajectory;
- whether coordinates are global Cartesian, local Cartesian, cylindrical, or a curved-frame construction;
- aperture/reference radius and its units;
- longitudinal integration limits and their physical definition (iron length, effective field limits, or stated fixed limits);
- symmetry restoration used while activating/loading the database.

For a curved magnet, do not apply a straight-magnet `B_y dz` convention blindly. Define the reference curve and desired field projection first, then use it consistently in sampling and integration.

### Choose the observable before choosing resolution

`NP` means number of intervals/steps, so line/circle commands typically evaluate `NP+1` points. Set sampling density based on the highest spatial harmonic or end-field variation to resolve, then run a sampling-convergence check. A smooth plot is not evidence that an integral or Fourier coefficient has converged.

Keep field data in named buffers. Commands such as `LINE`, `ARC`, `CIRCLE`, `POLAR` and `FIT` can consume/produce buffers; `BUFFER` switches the active one. Give buffers a case and purpose name, for example `b_centerline`, `b_refcircle`, `b_endfield`, rather than relying on the default `Line`/`Circle`/`Fit` buffer.

## Lines, arcs, circles and maps

### One-dimensional sampling

| Command | Intended geometry | Useful reduction |
| --- | --- | --- |
| `LINE` | Segment between two points | axial field, gradient, fringe field, centreline integral |
| `ARC` / `CIRCLE` | Circular path in a local XY plane | azimuthal field/multipole samples |
| `DATALINE` | Plot/process a current buffer | graphing and buffer-derived scalar checks |
| `FIT TYPE=FOURIER` | Complete cycle of line/arc/circle values | Fourier coefficients `A_n`, `B_n` |
| `FIT TYPE=LEGENDRE` | Sphere inside model space | spherical-harmonic/Legendre representation |

`LINE` evaluates all currently available variables on the points and stores them in a buffer. Its endpoint coordinates are interpreted through the selected local frame while vector components remain global. `CIRCLE` similarly samples a local XY circle at `ZC`; it is suitable only when the complete geometric cycle is physically meaningful.

`FIT TYPE=FOURIER` assumes a complete cycle and stores coefficients in system variables `A_n`, `B_n`; the requested order cannot exceed half the number of field points. This is an OPERA-native Fourier fit to sampled values. It is not automatically the same as accelerator normal/skew multipoles: the chosen component, angle convention, reference radius and normalization must be declared.

### Two-dimensional maps

`POLAR`, Cartesian and spherical sampling commands create field points on patches. `MAP` plots scalar contours and/or vector arrows over those points and also updates:

- `INTEGRAL` for the displayed component over the patch;
- `MINIMUM`, `MAXIMUM`;
- extreme locations (`XATMINIMUM`, `YATMINIMUM`, `ZATMINIMUM`, and maxima equivalents).

Use `MAP` both as a visual diagnostic and as an integration primitive only after checking patch orientation, limits and component expression. Reversing a parameterization/normal can reverse the physical sign. Store the scalar result immediately into a user constant if later commands will overwrite `INTEGRAL`.

```text
/ Conceptual sequence; establish the coordinate/patch convention first.
POLAR ...
MAP COMPONENT=BY
$CONSTANT #int_by INTEGRAL
```

Do not use default contour limits in a regression check. Specify a fixed range for comparison pictures, while separately writing numeric extrema/integrals for verification.

## Integrated field and harmonics

### Three distinct quantities

Keep these results separate in filenames, tables and prose:

1. **Local field**: a component or magnitude at a named point/plane.
2. **Longitudinal/integrated field**: a component/projection integrated along the reference path.
3. **Multipole/harmonic coefficient**: a Fourier/complex coefficient obtained from a defined transverse or cylindrical sample, often after longitudinal integration.

The dominant order depends on the convention (for example dipole versus quadrupole) and whether an angular symmetry factor is included. The sign and normal/skew meaning cannot be recovered later if the frame and phase are absent.

### User-supplied cylinder method

The supplied file `harm3d dipole&quadrpole intfield amp.comi` performs a useful explicit workflow:

1. Constructs a cylindrical `POLAR` patch over radius `#R`, azimuthal extent and longitudinal limits `#Z1:#Z2`.
2. For each order, maps the requested field expression multiplied by `COS(n*theta)` and `SIN(n*theta)`.
3. Reads `INTEGRAL` after each `MAP`, applies a geometry/symmetry normalization, and stores normal/skew-like coefficients.
4. Forms amplitude, then normalizes to `10000` units using the selected main harmonic.
5. Writes `harmonic.txt` with `OVERWRITE`.

Treat that file as a **template to validate**, not a universal accelerator convention. It explicitly assumes the magnet centreline is global Z, asks only dipole/quadrupole type, assumes activated full symmetry, and overwrites its output filename. Its `#NZ`/azimuthal point counts, radial normalisation, field expression, angular range and `#th_harm` must be re-derived for each magnet convention.

### Do not mix two harmonic definitions

For 3D end fields, choose one definition and put it in the result filename and CSV header:

| Definition | Procedure | What it answers |
| --- | --- | --- |
| Slice-first | At each longitudinal position, fit transverse/circular harmonics; integrate each coefficient along the reference path | Longitudinal evolution and integral multipoles with explicit slice resolution |
| Integral-first | Build a longitudinally integrated cylindrical/patch field, then Fourier-project it (the supplied template's pattern) | Harmonics of the integrated field over the stated surface/limits |

They may agree only when the component convention, transverse reference path, weights, limits and numerical quadrature are equivalent. Never compare a slice-first `B_n(z)` directly with an integral-first coefficient as though both were local multipoles. Save the method, z nodes/weights, angle nodes and field projection with every coefficient.

### Harmonic validation protocol

1. Run a centre-point check at low current; confirm expected field direction/dominant order.
2. Check the same reference radius at two azimuthal and longitudinal sample densities; compare dominant and significant error harmonics.
3. Vary radius inside the good-field aperture and compare at a common reference radius. Under approximately 2D source-free assumptions, raw order-n fields scale as radius to power n-1, and relative units normalized to order m scale as radius to power n-m. A large high-order radius trend alone is not an error. Use [integrated-harmonic diagnostics](integrated-harmonic-diagnostics.md) for parity, finite-endpoint caveats and numerical-floor checks.
4. Reverse current in a linear material baseline. Signed field and signed coefficients should reverse; normalised relative errors may stay unchanged. Explain any nonlinear/hysteretic exception.
5. Compare symmetry-related points. A forbidden parity component is a high-value diagnostic for boundary, coil-sign or frame mistakes.
6. Save raw coefficients, amplitudes, reference radius, main-harmonic definition and normalization factor—not only “units”.

Avoid normalizing to a numerically tiny main harmonic. Detect `ABS(main)<tolerance`, emit a failed/undefined status, and preserve raw values instead of generating misleading large relative units.

The normalized main value of `10000` is an identity, not evidence of equal absolute fields or correct case loading. Retain numeric case/time identity and raw signed main coefficients with units. Literal `TTIME` in an export requires a format/load-identity check before comparison. Full-circle integration of an octant model requires verified vector reflection, not scalar loss multiplication; follow the [symmetry and identity diagnostics](integrated-harmonic-diagnostics.md).

## Forces, energy and volume quantities

Use the integration command that matches the object of interest:

| Quantity | Native route | Main caution |
| --- | --- | --- |
| Force/torque on an enclosed object | `INTEGRATE`, Maxwell stress or virtual work | Surface must enclose the body and the torque action point must be declared |
| Magnetic/electric energy/co-energy | `ENERGY` or documented solver result | State nonlinear/time/harmonic convention |
| Current-flow/eddy-current power | `ENERGY` selected by material/volume label, then `POWER` | `POWER` is the selected-volume integral of `J·E`; confirm symmetry and do not confuse it with cumulative energy |
| Field expression in material/labelled volume | `VOLUME` | Select volumes explicitly; use adaptive integration where appropriate |
| Flux linkage | `FLUXLINKAGE` after conductor selection | Converge spacing and axial patches |
| Field patch integral | `MAP`, `PLOT`, `SURFACE`, or `VOLUME` | Interpret `INTEGRAL` only with geometry/orientation known |

`INTEGRATE` reports force (`FX`,`FY`,`FZ`) and torque (`TORQX`,`TORQY`,`TORQZ`). Maxwell stress is evaluated on the selected enclosing surface; virtual work integrates energy changes around it. For Maxwell stress, keep the integration surface in a suitable air gap whenever possible. If it crosses ferromagnetic material, use the documented material-aware formulation/system variables rather than an air-only expression.

`VOLUME` integrates a component expression over selected material/volume labels and reports `INTEGRAL`, `VOLUME`, extrema and locations. It excludes reflected/rotated copies set at activation, so apply symmetry multiplication only after verifying the selected model fraction and the physical parity. For fields calculated by integration, adaptive volume integration may be needed for accuracy; demonstrate convergence.

## Transient and harmonic result discipline

### Transient result series

At every output time, write a compact row with at least time, drive/current, a reference field/integral, one loss/temperature/motion observable where relevant, solver case/status and mesh/model identifier. Sample at declared output times, not at arbitrary solver substeps, unless the control contract explicitly requires the latter.

For a pulsed magnet, compare:

- current waveform and circuit voltage against their source definition;
- field lag and eddy-current response against a low-frequency/static limit;
- energy/loss trends and a physically meaningful sign check;
- response after pulse turn-off, rather than only peak field.

Use an exact table of requested times around discontinuities, fast ramp edges and extrema. A transient solve that converges with sparse output is still inadequate for an unobserved peak or delay.

### Harmonic/AC result series

Harmonic field values may be instantaneous, amplitude, phase or time-average quantities depending on the command option and selected phase/time. Never mix these in a comparison table. Record frequency, phase/`ACTIME`, and whether force/energy/flux uses `ANGLE`, `AMPLITUDE`, `AVERAGE`, `PEAK` or `PHASE` evaluation.

For time-series Fourier analysis (for example iron-loss workflows), select one steady periodic cycle after transients decay. The local documentation recommends at least `2n+1` output times per period for highest harmonic order `n`; use more where waveform sharpness demands it. Label stationary and rotating regions separately when a workflow needs spatial rotation decomposition.

## Tables, grids and coupling transfer

### Export reproducible data

- `GRID` evaluates up to 12 expressions on a 1D/2D/3D grid and writes text `.table` or binary grid data; include coordinate and field units in the output definition.
- `TABLE` evaluates expressions at specified points, writes table data, and can copy values into a database.
- `LOGGEDDATAFILE` creates/imports/exports row-based buffers (CSV) and is useful for case summaries and time histories.
- `PICTURE`/plots are audit artifacts, not numerical source of truth.

Write raw data before derived normalised values. Choose unique filenames per case and result type. Do not overwrite a generic `harmonic.txt`, `.table` or CSV from a parameter sweep.

### Transfer fields between analyses carefully

The documented `TABLE` workflow transfers fields even between different meshes:

1. In the receiving simulation, export its nodal coordinates.
2. Load the source simulation and evaluate source fields at those coordinates into a second table.
3. Reload the receiving simulation and import the evaluated fields into its database.
4. Register the imported quantities with `SYSVARIABLE` before using them in later field commands.

This is a data-transfer procedure, not proof of a physically valid coupled solve. Preserve source/target model versions, coordinate/unit transformations, field names, interpolation settings and conservation/error checks. For EM–thermal or magnetization coupling, use named transfer tables and explicitly decide whether the workflow is one-way, weak iterative or fully coupled.

## Automation and acceptance tests

Give every case a machine-readable summary row plus raw tables. A useful schema is:

```text
case_id,model_hash,mesh_level,solver,case_or_time,drive,observable,
value,unit,reference_frame,normalization,status,log_path
```

Before accepting an automated post-process run:

1. Confirm correct database, active result time/frequency, model symmetry and units.
2. Confirm every sampling path/patch lies in valid model space and has the intended orientation.
3. Verify that a command did not overwrite a shared `INTEGRAL`, `MINIMUM`, `MAXIMUM` or buffer before the value was captured.
4. Compare a baseline result with a GUI/manual point probe and with an independently computed simple limit where available.
5. Demonstrate mesh and sample-density convergence for each reported integral or significant harmonic.
6. Fail visibly on missing fields, no selected volumes/surfaces, tiny normalization denominator, solver warnings or incomplete time range.
7. Archive COMI/Python inputs, source database/version, solver/post log and results together so a later rerun is traceable.
