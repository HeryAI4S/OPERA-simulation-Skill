# Beam phase space and solenoid tracking in the OPERA-3d Post-Processor

Use this reference to turn an OPERA field solution into a reproducible fixed-field beam experiment with non-zero transverse emittance. Read `native-particle-tracking.md` first for the complete `TRACK` and `VIEW` command contract.

## Contents

1. [Do not confuse beam size with emittance](#do-not-confuse-beam-size-with-emittance)
2. [Construct an explicit phase-space ensemble](#construct-an-explicit-phase-space-ensemble)
3. [Convert direction and particle properties](#convert-direction-and-particle-properties)
4. [Interpret a solenoid](#interpret-a-solenoid)
5. [Run a controlled comparison](#run-a-controlled-comparison)
6. [Build a direct native Post visualization](#build-a-direct-native-post-visualization)
7. [Worked template contract](#worked-template-contract)
8. [Acceptance tests](#acceptance-tests)

## Do not confuse beam size with emittance

For one transverse plane, calculate the geometric rms emittance from the sampled particles:

```text
epsilon_x = sqrt(<(x-<x>)^2><(x'-<x'>)^2> - <(x-<x>)(x'-<x'>)>^2)
```

Use one consistent unit, normally mm·mrad. The normalised rms emittance is:

```text
epsilon_n = beta*gamma*epsilon_geometric
```

Always state whether a quoted emittance is geometric or normalised and whether it is rms, edge, 90%, 95%, or another convention. A wide `TRACK OPTION=BEAM` grid with one common direction has beam size but essentially zero transverse phase-space area. It is not a large-emittance beam.

Particle species does not determine emittance by itself. A low-velocity heavy-ion beam often has a large geometric emittance for a modest normalised emittance because `beta*gamma` is small, but the numerical emittance still must be supplied or measured.

## Construct an explicit phase-space ensemble

For a genuine non-zero-emittance distribution, generate many `TRACK OPTION=PARTICLE` commands with individual `X0,Y0` and direction angles derived from `x',y'`.

A reusable deterministic workflow is:

1. Define `epsilon_x,epsilon_y`, rms sizes, Twiss alpha/correlation, particle count and truncation rule.
2. Generate a deterministic quasi-random or documented seeded distribution in `(x,x',y,y')`.
3. Centre the finite sample and, when a regression-quality input is needed, whiten/rescale it so its measured covariance exactly matches the requested rms sizes and emittances.
4. Save the actual particles to CSV; never rely only on generator settings.
5. Use the identical particle CSV for field-on, field-off and mesh/solver comparisons.
6. Assign `BEAMCURRENT/number_of_particles` to each ray when current-density reductions are required. This is a weight in fixed-field Post-Processor tracking; it does not create space charge.

Use command-file-only `STATUS=UNKNOWN` for the first particle written to a case-local track file: it creates a missing file or overwrites an existing file without a GUI prompt. Use `STATUS=OLD` for the rest. `STATUS=CLEAR` only overwrites an existing file and fails for a brand-new result path in Opera 2025. Do not append different parameter cases to one unnamed `.track` file.

## Convert direction and particle properties

### Slopes to OPERA Euler angles

With the reference direction along global +Z and slopes `x'=dx/dz`, `y'=dy/dz`, first calculate the desired direction angles:

```text
alpha   = degrees(atan(sqrt(x'^2+y'^2)))
azimuth = degrees(atan2(y',x'))
```

The manual describes the Euler-frame +Z axis, but an Opera 2025 SP1 Build 20 native `TRACK` probe established the additional runtime sign rule:

```text
initial velocity direction = sign(VOLTS) * (Euler-frame +Z axis)
```

Therefore the slope-to-Euler conversion must branch on `VOLTS`:

```text
if VOLTS > 0:
    THETA = alpha
    PHI   = azimuth
else if VOLTS < 0:
    THETA = 180 degrees - alpha
    PHI   = azimuth + 180 degrees
PSI = 0
```

Normalize `PHI` to any equivalent angle range accepted by the installed release. For a negative-voltage electron travelling exactly along global +Z, this reduces to `THETA=180`; `THETA=0` sends that electron toward global -Z. The sign branch is controlled by `VOLTS`, not directly by `CHARGES`. Positive kinetic energy still separately requires `VOLTS*CHARGES>0`.

The worked template keeps `track_direction_probe.comi` as a short native regression. In the verified run, a negative-voltage electron at `THETA=0` moved toward -Z, the same electron at `THETA=180` moved toward +Z, and a positive-voltage positive-charge control at `THETA=0` moved toward +Z. If the beam reference path is not global +Z, first define the reference local coordinate system and compose the desired particle slope with that frame, then apply the voltage-sign reversal.

### Energy, charge and mass

The `TRACK` manual defines:

```text
kinetic energy [eV] = VOLTS * CHARGES
```

Require a positive product and record both inputs. `CHARGES` is in elementary-charge units and `MASS` is in electron-rest-mass units.

- Electron: `CHARGES=-1`, `MASS=1`; a 100 MeV electron uses `VOLTS=-100e6`.
- Proton: `CHARGES=+1`, `MASS≈1836.1527`.
- Fully stripped `238U92+`: `CHARGES=+92`; a useful nuclear-mass approximation is `MASS≈238*1822.888486=433847.46`. For total kinetic energy `K`, use `VOLTS=K[eV]/92`.

For a heavy ion quoted at `K_u` MeV/u, total kinetic energy is `A*K_u` MeV. Do not enter `K_u` alone into the total-particle energy convention.

Calculate and preserve:

```text
gamma = 1 + K_total/(M*c^2)
beta_gamma = sqrt(gamma^2-1)
p = beta_gamma*M*c
B_rho [T m] = p[GeV/c]/(0.299792458*abs(charge_state))
```

These quantities are an independent check on OPERA's relativistic trajectory result.

## Interpret a solenoid

For an approximately axial field, define the signed Larmor wavenumber:

```text
k = q*Bz/(2*p) = sign(q)*Bz/(2*B_rho)
```

Call `phi_L=integral(k dz)` the **signed Larmor phase**, not an unqualified observed rotation angle. With the standard laboratory-coordinate hard-edge matrix written below, an initially parallel off-axis ray has transverse position angle `-phi_L` at the magnet exit (while the Larmor frame itself uses `phi_L`). State the matrix and coordinate convention whenever reporting a sign. The focusing strength depends on `k^2`, while either observed rotation convention reverses with charge or field sign. Therefore electrons and positive ions rotate in opposite directions under the same field convention.

For a hard-edge solenoid of length `L`, the Larmor-frame 2x2 transport is:

```text
[ cos(kL)       sin(kL)/k ]
[ -k*sin(kL)    cos(kL)   ]
```

Use this only as a scale/sign check. The OPERA trajectory should include the calculated fringe field, transverse components and full relativistic correction.

An exactly on-axis particle moving exactly parallel to the axis has zero transverse Lorentz force in an ideal axisymmetric solenoid, so it cannot demonstrate rotation. A static magnetic field changes direction, not kinetic energy. Use a documented off-axis reference ray to expose the rotation sign.

An initially round, uncoupled distribution can hide rotation in an `x-y` scatter plot. When the teaching goal is to make the solenoid action visible, do all of the following:

1. plot `sigma_x(z)` and `sigma_y(z)` separately for field on and field off;
2. put field-on and field-off exit spots in separate panels with identical axis limits;
3. draw covariance ellipses and report at least one cross-plane correlation from `(x,x')` versus `(y,y')`;
4. plot the x-y path of an off-axis parallel reference ray and label the signed Larmor phase separately from the observed ray angle;
5. overlay the physical/reference aperture, label an exit-plane fraction as exit-only occupancy, and separately calculate each ray's maximum radius through the magnet; neither is a true loss model unless a wall/`BEAMSTOP` terminates tracks and the termination reason is audited.

For a reusable Modeller COMI, do not depend on a localized built-in coordinate-system label or an inherited current-density unit. Reset the working frame with `WCS OPTION=UNSET`, create a case-owned zero-angle `LCS`, and pass that name to `SOLENOID`. When the intended physical source is a known total current or homogenized ampere-turn value, use the documented `CURD=total_current/AREA` form; OPERA supplies the conductor cross-section `AREA`. Independently verify the resulting signed on-axis field before tracking.

## Run a controlled comparison

Use this sequence:

1. Validate the solenoid model and axial field profile.
2. Run a short field-free direction probe for each voltage-sign branch. Confirm that the saved Z coordinate advances toward the requested observation planes before generating hundreds of rays.
3. Track one on-axis reference particle; confirm energy, sign, termination and approximate rotation/focusing.
4. Track the explicit finite-emittance ensemble in the resident field with `OPTION=PARTICLE`.
5. Track the exact same ensemble with `OPTION=FUNCTION` and `#BX,#BY,#BZ,#EX,#EY,#EZ` set to zero, or use a separately verified zero-current database.
6. Save separate field-on/off `.track` files.
7. Display 3D trajectories with `VIEW PLOT=DISPLAY`.
8. Create entrance/centre/exit `CARTESIAN` or `POLAR` patches and use `VIEW PLOT=INTERSECTIONS` with `STOPAFTERFIRST=YES`.
9. For density, use `VIEW PLOT=TEMP FUNCTION=CURRENT|NUMBER|BEAMLETPOWER`, then `MAP COMPONENT=BEAMDENSITY`.
10. Make a diagnostic patch larger than the physical/reference aperture. Otherwise missing halo points are ambiguous: they may have missed the patch rather than been lost in the model.
11. Give the intersection `VIEW` a `BUFFERNAME` and export it with `LOGGEDDATAFILE OPTION=OVERWRITE` to a case-local CSV. Keep the binary `.track`, Post log and CSV together.
12. Compare centroid, mean direction, covariance/emittance, rms sizes, loss fraction and total crossing current. A smooth density map is not enough.

Post-Processor tracking is fixed-field/test-particle physics. Switch to Charged Particle/SCALA when beam space charge, self-magnetic field, emission, collisions or secondary particles must change the fields or trajectories self-consistently.

## Build a direct native Post visualization

When the user wants to **see the magnet acting on the beam inside OPERA**, do not stop at an external Python scatter plot. Generate a Post command chain that leaves both a useful Model-tab view and named Graphs-tab data:

```text
ACTIVATE FILE=%QUOTE<&COMIPATH&\..\model.op3>
LOAD
UNITS LENGTH=MM FLUX=TESLA
SET FIELDS=NODAL COIL=INTEGRATION LOOK=TRAJECTORIES XLOCAL=0 YLOCAL=0 ZLOCAL=0 TLOCAL=0 PLOCAL=0 SLOCAL=0
BUFFER OPTION=OVERWRITE
SELECT ACTION=RESET
SELECT ACTION=DEFAULT
SELECT ACTION=SELECT OPTION=SURFACES COIL=NO SYMMETRY=NONE
THREED OPTION=SETVIEW SIZE=... ROTX=... ROTY=... ROTZ=... PERSPECTIVE=NO
```

Keep `LOOK=TRAJECTORIES` while calculating every `TRACK` file. It restricts the field search to trajectory air and honors `BEAMSTOP`. In the verified Opera 2025 SP1 Post workflow, switch state before creating the `POLAR` display/diagnostic patches:

```text
SET LOOK=ANYWHERE ABORT=YES
POLAR ...
```

Without this switch, Post tried to evaluate the patch under the trajectory-material filter and aborted the visualization chain. `LOOK` is session state: restore `LOOK=TRAJECTORIES` before any later `TRACK` command.

Then create these layers, in this order:

1. `VIEW PLOT=BUFFER XAXIS=Z YAXIS=R|X|Y` for field-on and field-off ensemble comparisons.
2. A deliberately off-axis single-particle reference ray, with `VIEW PLOT=BUFFER XAXIS=X YAXIS=Y COLOUR=FUNCTION FUNCTION=TOF`, because an ideal on-axis parallel ray does not show solenoidal rotation.
3. Separate named `CARTESIAN` or `POLAR` patches at the coil entrance, centre, coil exit and downstream observation plane. Immediately select each patch with `BUFFER OPTION=SWITCH` before `VIEW PLOT=INTERSECTIONS`. A circular `POLAR` disk is preferable when the valid field-search region is cylindrical: its radius can cover the beam without invalid square corners outside the mesh/search volume.
4. Colour corresponding on/off intersections by an invariant initial label such as `ATAN2D(YSTART;XSTART)`. This makes rotation of the same initial azimuth pattern visible and avoids confusing trajectory-number colours with physical rotation.
5. Export every intersection graph buffer with `LOGGEDDATAFILE OPTION=OVERWRITE` to a case-local CSV.
6. On separate on/off exit patches, run `VIEW PLOT=TEMP FUNCTION=CURRENT SAMPLE=0`, capture `TOTALCURRENT` immediately, and then run `MAP COMPONENT=BEAMDENSITY`. Also write `INTEGRAL` after the map.
7. Finish with a 3D overlay: field-off ensemble in text colour, field-on ensemble with `COLOUR=FUNCTION FUNCTION=TOF`, straight reference-off ray, and the field-on reference ray as a visible `PLOT=TUBE`; call `THREED OPTION=REFRESH` last.

For stream output, the verified 2025 SP1 COMI parser requires formats and a stream assignment before the first `$WRITE`. Keep this ordering:

```text
$OPEN 0 'results/density_totals.txt' OVERWRITE
$FORMAT 1 CHARACTER 0
$FORMAT 2 EXPONENTIAL 0
$ASSIGN 1 2
$WRITE OPENSTREAM 'field_off_total_current_A=' TOTALCURRENT
...
$CLOSE OPENSTREAM
```

Do not place `$WRITE OPENSTREAM` immediately after `$OPEN` without `$FORMAT`/`$ASSIGN`; that version aborts with an output-format error.

Use `TRACKDENSITY` only to declutter `PLOT=DISPLAY` or 2D trajectory graphs. It is display subsampling, not a beam-physics sampling control; intersections, density, totals and exported CSV must use all tracked rays. Record the chosen display fraction so the picture is not mistaken for particle loss.

`CARTESIAN|POLAR ... BUFFERNAME=...` and `BUFFER OPTION=SWITCH NAME=...` manage field/patch buffers. `VIEW ... PLOT=BUFFER|INTERSECTIONS BUFFERNAME=...` creates graph-data buffers. Do not interchange those two namespaces. Give every graph buffer and exported file a unique, stable case/species/field/plane name.

Set `BUFFER OPTION=OVERWRITE` before creating patches so repeated runs do not silently generate unique patch names and then switch to stale data. Do not silently add `AXESVIEW OPTION=CLEARALL` to a reusable script: it deletes all graph data in the user's current Post session. Recommend a dedicated Post session for deterministic reruns, or clear graphs only with explicit user consent.

For a one-command workflow, make a driver COMI that first checks the solved database with `$EXIST`/`FILEEXISTS`, calls `ACTIVATE`, refuses to proceed unless `ACTIVATE_STATUS=0`, then loads it once and uses `$COMINPUT ... CONTINUOUS LINE` to invoke, in order, ensemble-off, ensemble-on, reference-off, reference-on and visualization children. Use `COMIPATH` for every model, track and result path; do not rely on OPERA's launch directory. A child `$COMINPUT` may use a relative name because OPERA resolves it relative to the containing COMI, but keep all children beside the driver. A temporary flag may suppress repeated `ACTIVATE` inside children, but the driver must delete stale state at startup and remove the flag at normal completion.

The visualization is evidence only after the solved `.op3` and generated `.track` files exist and the COMI has actually run in the target OPERA version. Static preflight cannot establish field sign, successful patch crossings, `TOTALCURRENT`, focusing, rotation, loss, or numerical convergence.

## Worked template contract

The qualification project used a separate, complete template with the following project-relative layout:

```text
template/particle_tracking/solenoid_large_emittance_beams
```

That model/result package is not redistributed in this skill repository. Use the following inventory as a contract when a user supplies an equivalent template; do not claim the public repository alone contains or reproduces it.

It includes:

- a 2 T-class air-core `SOLENOID` TOSCA model;
- deterministic 4D large-emittance ensembles;
- 100 MeV electron and `238U92+` at 1 MeV/u;
- field-on and exact-zero-field COMI files generated from the same particles;
- one-command `run_electron_post_demo.comi` and `run_u238_92plus_post_demo.comi` Post entrypoints;
- matching `batch_*_post_demo.comi` wrappers that execute the same chain and terminate hidden `/nowindow` sessions with `END`;
- `batch_visualize_<species>_solenoid_effect.comi` wrappers that reuse existing `.track` files, rerun only the native visualization/export chain, and terminate hidden `/nowindow` sessions with `END`;
- `track_direction_probe.comi`, a native voltage-sign/Euler-axis regression for the installed OPERA release;
- direct native 3D on/off trajectory overlays plus a thick off-axis reference ray;
- named `R(Z)`, `X(Z)`, `Y(Z)`, reference `X-Y` and four-plane on/off intersection graph buffers;
- field-on/off exit `BEAMDENSITY`, `TOTALCURRENT` and density-integral capture;
- in-mesh circular `POLAR`/`VIEW PLOT=INTERSECTIONS` analysis;
- an oversized diagnostic patch plus `LOGGEDDATAFILE` CSV transfer, so halo points are not silently clipped at the reference aperture;
- an external plot/summary helper for the actual OPERA exit CSV files;
- a labelled hard-edge analytic preview that must not be reported as an OPERA result.

When a user supplies the qualified template, reuse its `generate_track_comi.py` for a non-zero-emittance distribution. Change `case_config.json`, regenerate, and verify `generated/generation_report.json` before running OPERA.

### Historical Opera 2025 SP1 qualification evidence

The following are actual solver/Post results from `solenoid_2T.op3` created with Opera-3d/Modeller 25.1.20 and processed by Opera 2025 SP1 Build 20; they are not values from the analytic preview:

- the headless electron visualization exported eight intersection CSV files: field off/on at `z=-150,0,150,550 mm`, each with all 241 first-crossing hits;
- at `z=550 mm`, the centred rms radius was `33.9434 mm` field-off and `12.1158 mm` field-on;
- the exit covariance major-axis angle, using `0.5*atan2(2*sigma_xy,sigma_xx-sigma_yy)` and understood modulo 180 degrees, was `-1.992 degrees` field-off and `28.393 degrees` field-on;
- electron `TOTALCURRENT` was `0.0999999999999762 A` for both cases; the corresponding `BEAMDENSITY` integrals were `0.0999999999999764 A` field-off and `0.0999999999999759 A` field-on.
- the full `238U92+` batch also completed with eight 241-hit sections; at `z=550 mm` its centred rms radius changed from `51.5979 mm` field-off to `24.4220 mm` field-on, while the covariance-axis angle changed from `-2.342 degrees` to `38.209 degrees`;
- U92+ `TOTALCURRENT` was `9.99999999999762E-5 A` for both cases and the two `BEAMDENSITY` integrals agreed at approximately `1.0E-4 A`;
- `validate_runtime_outputs.py` independently consumes the real intersection CSVs, density summaries and the direction-probe Post log, writes `results/native_runtime_summary.json`, and rejects direction, hit-count, current-closure, focusing or rotation failures. Keep this runtime check separate from static COMI validation.

These results establish successful fixed-field solver/Post tracking, intersections, density reduction and focusing for this electron case. They do not establish self-consistent space charge.

The associated model, databases, logs, trajectory files, and exported CSVs are not bundled here. Treat these numbers as provenance for the guidance, not as a reproducible result of cloning this repository; rerun and retain equivalent evidence in the target licensed installation.

## Acceptance tests

1. The finite sample reproduces the requested rms emittance and covariance within a declared tolerance.
2. `VOLTS*CHARGES` equals the requested positive kinetic energy for every species.
3. A short native direction probe confirms `sign(VOLTS) * Euler-frame +Z` and the intended monotonic propagation direction.
4. `MASS`, charge state, isotope and total versus per-nucleon energy are explicit.
5. Zero-field trajectories are straight and agree with `x(z)=x0+x'*(z-z0)`, `y(z)=y0+y'*(z-z0)`.
6. Reversing charge or solenoid current reverses rotation while leaving first-order focusing magnitude approximately unchanged.
7. Track endpoints are explained by planned `NSTEP`, patch crossing or aperture/field-volume exit.
8. Diagnostic-patch coverage is wider than the aperture under test; hit count, `TOTALCURRENT` or equivalent ray weights make missing tracks auditable.
9. Intersection buffers are exported to a documented machine-readable result contract, not left only in a dialogue log.
10. `POLAR` display patches are created under `LOOK=ANYWHERE ABORT=YES`, while later trajectory calculation restores `LOOK=TRAJECTORIES`.
11. Every `$WRITE` stream has preceding `$FORMAT` and `$ASSIGN` definitions.
12. Results converge with magnet mesh, conductor tolerance, `TRACK TOLERANCE`, output `STEP`, particle count, truncation and patch resolution.
13. Field-on/off comparisons use byte-identical initial particle tables.
14. Fixed-field results are not labelled as space-charge simulations.
