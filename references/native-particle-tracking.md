# OPERA-3d native particle and beam tracking

Use the OPERA-3d Post-Processor to calculate how a solved electric and/or magnetic field acts on charged particles. The native `TRACK` command includes full relativistic correction. Use `VIEW` to display and reduce the saved trajectories.

## Contents

1. [Choose the correct particle model](#choose-the-correct-particle-model)
2. [GUI and command mapping](#gui-and-command-mapping)
3. [Prepare the active field](#prepare-the-active-field)
4. [Define the particle or test beam](#define-the-particle-or-test-beam)
5. [Control and save the trajectory](#control-and-save-the-trajectory)
6. [Display and analyse the beam](#display-and-analyse-the-beam)
7. [Accelerator-magnet workflow](#accelerator-magnet-workflow)
8. [Validation checklist](#validation-checklist)

## Choose the correct particle model

| Need | OPERA route | Physics included |
| --- | --- | --- |
| Reference particle or a rectangular test pattern through an already solved field | Post-Processor `TRACK OPTION=PARTICLE` or `OPTION=BEAM` | Relativistic Lorentz motion in the resident electric, magnetic, or combined field |
| A field line rather than a physical particle | `TRACK OPTION=FLUXTUBE` | Follows the applicable flux-density/current-density field |
| Analytic or time-dependent user-defined fields | `TRACK OPTION=FUNCTION` | Uses `#BX,#BY,#BZ,#EX,#EY,#EZ`, including expressions involving `TOF` |
| Space-charge-limited emission, self-consistent beam electric field, optional beam self-magnetic field, collisions or secondary particles | Charged Particle solver, historically SCALA | Iterates Poisson field, beamlets and space charge; not equivalent to post-processing a fixed field |
| Full accelerator lattice, Twiss matching, arbitrary six-dimensional bunch distributions or collective ring/linac effects | Export an OPERA field/map or transfer map to a beam-dynamics program | Outside the intended scope of the Post-Processor test-pattern beam |

`TRACK OPTION=BEAM` is a beam **test pattern**, not a self-consistent bunch solve. Each track has a current weight for density/power reductions, but that current does not update the resident magnet field. Do not describe it as a space-charge calculation.

## GUI and command mapping

The Chinese ribbon shown as **后处理 → 轨迹** maps to the following native operations:

| GUI item | Native operation | Result |
| --- | --- | --- |
| 计算 | `TRACK` | Calculate one particle, a beam test pattern, a user-field particle, or a flux line |
| 显示 | `VIEW PLOT=DISPLAY` | Overlay saved tracks on the three-dimensional model |
| 图 | `VIEW PLOT=BUFFER` | Put selected trajectory variables into a graph buffer |
| 与补片相交 | `VIEW PLOT=INTERSECTIONS` | Calculate intersections with a selected Cartesian, polar or spherical patch |
| Density-map processing | `VIEW PLOT=TEMP`, then `MAP COMPONENT=BEAMDENSITY` | Current, power or particle-number density on a patch |
| Create display tubes | `VIEW PLOT=TUBE` | Build display facets around tracks; this is a visualization reduction |

Do not confuse a display tube with `TRACK OPTION=FLUXTUBE`: the latter calculates a flux-following line; the former thickens existing tracks for display.

## Prepare the active field

1. `ACTIVATE` and `LOAD` the required result database and case/time. The track uses the currently resident field, not merely the filename highlighted in the GUI.
2. Confirm the database units after `LOAD`. OPERA restores the model's stored units; the common defaults visible in older models are centimetres and gauss. Record length, magnetic flux density, energy and time units in the case manifest.
3. Establish a beam coordinate frame using `SET`. `X0,Y0,Z0` and the initial Euler-angle direction are interpreted in the selected local coordinate system.
4. Confirm that the complete intended path lies inside the field-search volume. Tracking stops when it crosses the field-calculation surface.
5. For paths restricted to the vacuum channel, verify `SET LOOK=TRAJECTORIES`. The documented behavior searches AIR volumes and excludes AIR volumes labelled `BEAMSTOP`. In a Charged Particle solver model, `BEAMPASS` can allow tracks through selected material volumes.
6. For electric plus magnetic tracking, verify that both fields are resident and combined using the installed-version `COMBINE` workflow. Do not assume that loading two result files automatically constructs a combined field.

`LOOK` is stateful. Keep `LOOK=TRAJECTORIES` for trajectory integration, but do not carry that material filter into a native `POLAR` display/diagnostic patch. The verified Opera 2025 SP1 sequence is:

```text
SET LOOK=TRAJECTORIES ...
TRACK ...
SET LOOK=ANYWHERE ABORT=YES
POLAR ...
```

Restore `LOOK=TRAJECTORIES` before any subsequent `TRACK` command.

## Define the particle or test beam

The central `TRACK` inputs are:

| Parameter | Meaning and guardrail |
| --- | --- |
| `X0,Y0,Z0` | Initial position in the active local coordinate system |
| `THETA,PHI,PSI` | Euler angles defining the Euler-frame +Z axis; Opera 2025 SP1 runtime tests found the initial velocity to be `sign(VOLTS)` times this axis |
| `VOLTS` | Acceleration-voltage parameter; the manual defines initial energy as `VOLTS*CHARGES` eV |
| `CHARGES` | Charge state in elementary-charge units; electron is `-1`, proton is `+1` |
| `MASS` | Rest mass in electron-rest-mass units; electron is `1`, proton is approximately `1836.1527` |
| `BEAMCURRENT` | Current associated with a track; it is also a weighting quantity in later density reductions |
| `OPTION` | `PARTICLE`, `BEAM`, `FUNCTION`, or `FLUXTUBE` |
| `PATTERN` | Transverse size of the rectangular starting grid for `OPTION=BEAM` |
| `LINES` | Number of grid lines in each transverse direction for `OPTION=BEAM` |

Require `VOLTS*CHARGES > 0` for a positive kinetic energy under the documented convention. For example, a positive ion uses positive `CHARGES` and `VOLTS`; an electron normally requires the corresponding negative voltage sign. Verify the GUI's displayed initial energy before launching a large set.

Do not infer the velocity sign from the Euler axis alone. A native Opera 2025 SP1 Build 20 probe measured:

```text
initial velocity direction = sign(VOLTS) * (Euler-frame +Z axis)
```

For a desired global +Z slope vector proportional to `(x',y',1)`, let `alpha=atan(sqrt(x'^2+y'^2))` and `azimuth=atan2(y',x')`. Use `THETA=alpha, PHI=azimuth` when `VOLTS>0`. When `VOLTS<0`, reverse the Euler axis with `THETA=180 degrees-alpha, PHI=azimuth+180 degrees`; keep `PSI=0`. Thus a 100 MeV electron with `CHARGES=-1, VOLTS=-100e6` needs `THETA=180` to travel exactly along global +Z. The reusable solenoid template provides `track_direction_probe.comi` to recheck this behavior after an OPERA upgrade.

The `BEAM` pattern starts particles at the intersections of a square orthogonal grid in the plane normal to the initial direction. It supplies transverse position sampling, but it is not automatically a Gaussian/Twiss distribution and does not by itself provide correlated angular or momentum spread. Use repeated scripted `PARTICLE` tracks or an external beam distribution workflow when those phase-space dimensions matter.

## Control and save the trajectory

| Parameter | Meaning |
| --- | --- |
| `STEP` | Distance between saved/displayed points along the track; it is **not** the adaptive integrator's internal step |
| `NSTEP` | Maximum number of saved steps; maximum nominal path length is `STEP*NSTEP` |
| `TOLERANCE` | Relative adaptive-integration accuracy applied to coordinates/velocities or flux density |
| `FILE` | Binary trajectory file consumed by `VIEW` |
| `STATUS` | `NEW` creates and may prompt before overwrite; `UNKNOWN` creates or silently overwrites and is command-file-only; `OLD` appends; `CLEAR` overwrites an existing file only |
| `PRINT` | Write trajectory coordinates to the Post dialogue log |
| `DISPLAY` | Display the newly calculated track in the 3D window |

A representative COMI skeleton is:

```text
/ Verify the database, case, units and local frame first.
TRACK OPTION=BEAM X0=#x0 Y0=#y0 Z0=#z0 THETA=#theta PHI=#phi PSI=#psi VOLTS=#volts CHARGES=#charge MASS=#mass BEAMCURRENT=#current PATTERN=#pattern LINES=#lines STEP=#track_step NSTEP=#nstep TOLERANCE=#track_tol FILE='results/case-0001.track' STATUS=UNKNOWN PRINT=NO DISPLAY=YES
```

Treat quoting and path syntax in this skeleton as version-sensitive COMI formatting. Verify the installed help or export a GUI-created command before execution. Keep each case's `.track` file separate.

Choose `STEP` small enough to represent aperture boundaries and fringe-field variation, then tighten `TOLERANCE` independently. A smaller display `STEP` does not prove the adaptive integration is converged.

## Display and analyse the beam

`VIEW` can read tracks from either Post-Processor `TRACK` or the Charged Particle solver.

### Three-dimensional and trajectory graphs

- Use `VIEW PLOT=DISPLAY` to overlay tracks on the model.
- Use `VIEW PLOT=BUFFER` for graphs such as `X(Z)`, `Y(Z)`, transverse velocity, time of flight or path length.
- Useful active variables include `X,Y,Z,R`, `VELX,VELY,VELZ`, `TOF`, `TRACKLENGTH`, `CURRENT`, `NUMBER`, `BEAMLETPOWER`, `Q`, `M` and `EMITTER`.
- Use `COLOUR=FUNCTION` to colour tracks by `TOF`, velocity, current or another active expression.

### Observation-plane intersections

1. After all required tracks are calculated under `LOOK=TRAJECTORIES`, execute `SET LOOK=ANYWHERE ABORT=YES` before creating a `POLAR` display/diagnostic patch. In the verified 2025 SP1 workflow this prevents patch field evaluation from inheriting the trajectory-material filter.
2. Create a Cartesian, polar or spherical patch at the observation surface.
3. Select its buffer.
4. Use `VIEW PLOT=INTERSECTIONS`; use `STOPAFTERFIRST=YES` when each particle should contribute only its first crossing.
5. Plot the cross-section or export intersection data. Available results include position, velocity, current, time of flight and the beam centre/direction variables `X0BEAM,Y0BEAM,Z0BEAM` and `TXBEAM,TYBEAM,TZBEAM`.
6. Repeat at several longitudinal planes to reconstruct centroid, angle and envelope evolution.

`VIEW PLOT=INTERSECTIONS` calculates a linear current density `DENSITY`. For a two-dimensional density map, use `VIEW PLOT=TEMP` with:

- `FUNCTION=CURRENT` for beam-current density;
- `FUNCTION=BEAMLETPOWER` for power density;
- `FUNCTION=NUMBER` for particle-number flux density.

Then display `BEAMDENSITY` with `MAP`. The integrated crossing current is available as `TOTALCURRENT`. Treat `SAMPLE` as a smoothing setting and demonstrate smoothing/track-count convergence; an attractive smooth map can still be under-sampled.

When writing `TOTALCURRENT` or the subsequent map `INTEGRAL` to a stream, define the output formats and assignment before the first `$WRITE`. This ordering was required by the Opera 2025 SP1 parser:

```text
$OPEN 0 'results/density_totals.txt' OVERWRITE
$FORMAT 1 CHARACTER 0
$FORMAT 2 EXPONENTIAL 0
$ASSIGN 1 2
$WRITE OPENSTREAM 'field_off_total_current_A=' TOTALCURRENT
MAP COMPONENT=BEAMDENSITY ...
$WRITE OPENSTREAM 'field_off_density_integral_A=' INTEGRAL
$CLOSE OPENSTREAM
```

For a deterministic headless regression that reuses existing track files, wrap the visualization COMI in `batch_visualize_<species>_solenoid_effect.comi`, invoke it with Post `/nowindow`, and terminate the wrapper with `END`. Keep the interactive visualization entrypoint free of `END` when the user needs the final Model view to remain open.

For an interactive Post session, pass the result database before the visualization COMI. The verified Opera 2025 SP1 command-line order is:

```text
operafea-post.exe /local /window "model.op3" "visualize_<species>_solenoid_effect.comi"
```

Passing only the COMI can open Post without loading the solved database, so the commands may never reach the intended track and field objects. A launcher should therefore check that the `.op3` database and saved trajectory files already exist, then supply both arguments in that order.

Do not equate a successfully opened visible Post window with a completed workflow. Maintain a second headless verification route which waits for Post to exit and checks the exported hit count, observation-plane coordinates, summed beamlet current, `TOTALCURRENT`, `BEAMDENSITY` integral, focusing metric and rotation metric. The worked solenoid case implements this separation with `validate_case.py` for static contracts and `validate_runtime_outputs.py` for actual OPERA outputs and the signed-voltage direction probe.

## Accelerator-magnet workflow

For a dipole, quadrupole or pulsed magnet:

1. Solve and validate the magnetic field, including fringe fields and the full vacuum aperture.
2. Define the reference-particle species, charge state, rest mass, kinetic energy, start point and direction.
3. Run a short on-axis `PARTICLE` track. Check `sign(VOLTS) * Euler-frame +Z`, saved-coordinate propagation, and approximate bending/focusing analytically before launching a beam.
4. Run `BEAM` with a small transverse pattern to visualize focusing, defocusing, rotation, aberration and aperture interception.
5. Add entrance, centre and exit observation patches. Save centroid, mean direction, cross-section, total crossing current and loss/interception evidence.
6. Repeat with smaller `TOLERANCE`, smaller output `STEP`, denser `LINES`, and at least one refined magnet mesh.
7. For transient fields, use a verified field/time representation or `OPTION=FUNCTION` with `TOF`; confirm that the field seen by the moving particle has the intended timing convention.

For a quick independent dipole check, with momentum `p` in GeV/c, charge state `Z`, and transverse field integral in T·m:

```text
bending angle [rad] ≈ 0.299792458 * Z * integral(B_perp ds) / p
```

Coordinate signs depend on the beam direction and local frame. Use this only as a magnitude/sign sanity check, not as a substitute for the three-dimensional trajectory.

## Validation checklist

1. Zero field produces a straight line with constant velocity.
2. Reversing magnet current or particle charge reverses the expected bend/focusing sign.
3. A quadrupole focuses one transverse plane and defocuses the other under the declared convention.
4. The path stays in a region with valid field data and the endpoint is caused by `NSTEP`, the planned observation surface, or a documented aperture—not an unnoticed field-volume exit.
5. Track results converge independently with `TOLERANCE`, output `STEP`, beam `LINES`, observation-patch resolution and magnet mesh.
6. `VOLTS`, `CHARGES`, `MASS`, units and the displayed kinetic energy are recorded with the `.track` file.
7. A post-processor `BEAM` result is labelled fixed-field/test-particle. Claim space-charge or self-field physics only when the Charged Particle solver configuration and convergence evidence are present.
8. A voltage-sign direction probe confirms the requested propagation direction before the full ensemble runs.
9. `POLAR` display patches are created after `SET LOOK=ANYWHERE ABORT=YES`; any later track restores `LOOK=TRAJECTORIES`.
10. Every `$WRITE` stream has preceding `$FORMAT` and `$ASSIGN` definitions.

## Local documentation provenance

- `opera3D_ref/ref-3d-part4/full.md`: **The TRACK Command**, **The VIEW Command**, trajectory parameters/files, intersections, density maps and active variables.
- `opera3D_ref/ref-3d-part2/full.md`: **Charged Particle Solver**, fixed/external magnetic fields, relativistic beamlets, space-charge iteration and optional beam self-magnetic field.
- Runtime-qualified direction, patch-state and stream-format behavior came from a project-supplied `template/particle_tracking/solenoid_large_emittance_beams/track_direction_probe.comi` case and successful Opera 2025 SP1 Build 20 Post logs. Those model/result artifacts are not redistributed in this repository; reproduce the probe in the target licensed installation before relying on version-sensitive behavior.
