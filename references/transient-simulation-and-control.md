# Transient simulation and control COMI

Use this reference for OPERA-3d time-dependent analyses: Transient EM (`ELEKTRATR`), Motional EM (`CARMEN`), Magnetization (`DEMAG`), Quench, and Transient Thermal (`TEMPOTR`). It is based on the 2025 SP1 local manuals. Confirm exact command option names, control-file discovery, and solver availability in the installed release before execution. For loss-variable semantics, spatial/time integration, single-pulse versus periodic iron-loss selection, and heat-source transfer, also read [transient losses and electromagnetic-thermal heat sources](transient-losses.md).

## Contents

1. [Choose the right solver](#choose-the-right-solver)
2. [Build a dynamic model](#build-a-dynamic-model)
3. [Configure initial time stepping and outputs](#configure-initial-time-stepping-and-outputs)
4. [Control-file discovery and lifecycle](#control-file-discovery-and-lifecycle)
5. [Control time steps safely](#control-time-steps-safely)
6. [Control circuits and motion](#control-circuits-and-motion)
7. [Drives, logging and Python hooks](#drives-logging-and-python-hooks)
8. [Restart and multiphysics coupling](#restart-and-multiphysics-coupling)
9. [Validation sequence](#validation-sequence)

## Choose the right solver

| Objective | Start with | Critical distinction |
| --- | --- | --- |
| Eddy currents, pulse/ramp response, voltage/current circuit drive | Transient EM (`ELEKTRATR`) | Use time stepping and conductive meshed regions when induced currents matter. |
| Rigid rotation/translation coupled to EM fields and circuits | Motional EM (`CARMEN`) | Add `GROUPLABEL`s and a `GAP` region; motion is defined by a control COMI. |
| Prescribed static speed with motion-induced currents | Fixed Velocity EM | It is a static-field-with-velocity-effect model, not a time history. |
| Magnetic material evolution | Magnetization (`DEMAG`) | Use its solver-specific control file and material model. |
| Quench with circuit/thermal evolution | Quench or coupled Quench–Transient EM | Model thermal material behaviour and circuit coupling; do not approximate it by a pure magnetostatic sweep. |
| Temperature transient and electromagnetic heat exchange | Transient Thermal (`TEMPOTR`) or coupled workflow | Decide whether a fixed heat source is sufficient or whether EM properties must be recalculated. |

Do not turn a magnetostatic `TOSCAMAGN` model into a pulse model by merely changing the solver name. First identify the physical source of time dependence, conductor representation, conductivity/eddy-current regions, circuit and output quantities.

## Build a dynamic model

### Establish the physical contract

Specify before scripting:

1. Drive type: prescribed Biot–Savart current density, circuit current source, circuit voltage source, external field, boundary-potential drive, or heat table.
2. Waveform: analytic (`STEP`, `RAMP`, `RISE`, `SINE`, `COSINE`, functional) or a time table. Give time/current/voltage units and a source of truth for its samples.
3. Conductors: distinguish mesh-independent Biot–Savart sources from meshed circuit-element conductors. The latter can be voltage/current driven through circuits and can capture conductor effects represented by the model.
4. Materials: declare nonlinear B-H, electrical conductivity, temperature dependence and any hysteretic/loss model needed by the physics.
5. Observables: centre field, integrated field/harmonics, coil current/voltage, losses, temperature, force/position, and the required sampling interval.

Use a static solution at the peak or quasi-DC current as a baseline. The first dynamic result should approach the comparable static result only when the physics actually permits it; eddy currents, circuit dynamics and hysteresis can make the difference physically real.

### Requirements unique to Motional EM

For Motional EM, give **every cell and conductor** a group label. `GAP` is reserved for the deforming buffer region. Any two adjacent moving/stationary groups require a `GAP` region between them; neighbouring cells with different non-GAP labels cause an error.

- Make the first two characters of every non-GAP group label unique. OPERA derives motion-variable prefixes from these characters.
- Use group labels such as `ROTOR`, `STATOR`, `GAP`; their control variables use prefixes such as `RO_` and `ST_`.
- Model the GAP volume as a mesh region that can be reshaped/remeshed. Do not prescribe independent motion for `GAP` itself.
- Check periodicity/symmetry under the actual displacement/rotation, not just at the initial position.

## Configure initial time stepping and outputs

### Analysis settings

The local reference documents these transient-analysis settings under `ANALYSISDATA`:

```text
ANALYSISDATA OPTION=LOAD PROGRAM=ELEKTRATR
ANALYSISDATA OPTION=SET PROGRAM=ELEKTRATR LINEAR=NO NLITERTYPE=NEWTON NITERATIONS=<nonlinear-limit> ITPTSTEP=<iterations-per-step> TOLERANCE=<nonlinear-tolerance> UPDATE=SIMPLE DELTAT=<initial-step>
```

This block is a parameter map, not a copy-paste command: place it on one supported COMI line or use the installed version's continuation convention. Important settings are:

| Setting | Meaning |
| --- | --- |
| `PROGRAM` | Choose `ELEKTRATR`, `CARMEN`, `DEMAG`, `QUENCH`, or `TEMPOTR` as appropriate. |
| `LINEAR`, `NLITERTYPE`, `NITERATIONS`, `TOLERANCE` | Nonlinear magnetic iteration behaviour. |
| `ITPTSTEP` | Maximum nonlinear iterations per transient step for Motional/Transient EM and Magnetization. |
| `UPDATE=SIMPLE` | Fixed step length. In nonlinear analyses, OPERA may reduce a failing step to obtain convergence. |
| `UPDATE=ADAPTIVE` | Variable step length; `DELTAT` is initial step and `MAXADERR` is maximum percentage error target. |
| `DELTAT` | Fixed step, or initial step in adaptive mode. |
| `DRIVELABEL`, `SCALEDRIVE` | Associate scaling/drive behaviour with selected conductor, field or boundary labels. |
| `LOGLIST` | List variables to log during the transient run; verify list syntax in the installed version. |

Start with `SIMPLE` fixed stepping to establish a transparent baseline. Choose a step small enough to resolve the shortest relevant physical/circuit time scale, switching edge and requested waveform/harmonic. After baseline validation, compare against an `ADAPTIVE` run or a sufficiently refined fixed-step run.

### Define output times deliberately

Use `DBCASEDATA` to define saved transient output times. The reference documents `PROGRAM`, `OPTION` and `VALUE` semantics:

```text
DBCASEDATA PROGRAM=ELEKTRATR OPTION=CLEAR
DBCASEDATA PROGRAM=ELEKTRATR OPTION=ADD VALUE=<t_1>
DBCASEDATA PROGRAM=ELEKTRATR OPTION=ADD VALUE=<t_2>
```

- Use `CARMEN` for Motional EM, `ELEKTRATR` for Transient EM, and `TEMPOTR` for Transient Thermal.
- OPERA includes an output at time zero and orders transient output times chronologically.
- Output times are storage/post-processing points, not necessarily all solver steps. Use logging and/or hooks when a denser history is needed.
- With fixed stepping, OPERA adjusts the step to yield a nearest integer number of steps between output times. Confirm the resulting actual cadence.
- For periodic field/loss analysis, choose enough output points per cycle for the highest harmonic retained; inspect the waveform rather than accepting a nominal point count blindly.

## Control-file discovery and lifecycle

The solver automatically looks for a time-step control COMI in the **same folder as the OP3 database**. It first prefers a database-specific file, then a generic file.

| Analysis | Specific file for `model.op3` | Generic file |
| --- | --- | --- |
| Motional EM | `model_carmen.comi` | `control_carmen.comi` |
| Magnetization | `model_demag.comi` | `control_demag.comi` |
| Transient EM | `model_elektratr.comi` | `control_elektratr.comi` |
| Quench | `model_quench.comi` | `control_quench.comi` |
| Transient Thermal | `model_tempotr.comi` | `control_tempotr.comi` |

Use a generic control file only for intentionally identical cases. For parameter sweeps, render a specific control file into each case folder, together with the case-local OP3, circuit files and Python files.

The command file runs repeatedly during a time step. `TIMESTEP_STAGE` identifies the call:

| Value | Meaning | Safe role |
| --- | --- | --- |
| `INIT` | First call at time zero before stepping | Initialize persistent string state and configuration. |
| `START` | Immediately before a step beginning at `T0` | Change step method, step length/limits, force a future event time. |
| `FULL` | Full-step trial in adaptive algorithm | Observe only; avoid state changes. |
| `FIRSTHALF` | First half-step trial in adaptive algorithm | Observe only; avoid state changes. |
| `SECONDHALF` | Second half-step trial in adaptive algorithm | Observe only; avoid state changes. |
| `END` | Accepted/complete step at `T0 + Δt` | Update switches, output/final/repeat decisions and accepted-step state. |

Test stage strings with `%COMPARE`; it returns zero on equality. This guard means “execute only at END”:

```text
$IF !%COMPARE(&TIMESTEP_STAGE&,END)
  / Accepted-step actions only.
$END IF
```

## Control time steps safely

### START: method, step length and event alignment

At `START`, modify the time-step controls only through the documented override variables:

```text
$IF !%COMPARE(&TIMESTEP_STAGE&,START)
  $STRING TIMESTEP_METHOD SIMPLE
  $STRING TIMESTEP_DELTAT OVERRIDE
  $CONSTANT #TIMESTEP_DELTAT <new_step>

  / For adaptive mode limits:
  $STRING TIMESTEP_MINMAX OVERRIDE
  $CONSTANT #TIMESTEP_MIN <minimum_step>
  $CONSTANT #TIMESTEP_MAX <maximum_step>

  / Force adaptive stepping to include a known discontinuity/event time:
  $CONSTANT #TIMESTEP_NEXT <event_time>
$END IF
```

`TIMESTEP_METHOD` accepts `SIMPLE` or `ADAPTIVE`. `TIMESTEP_DELTAT=OVERRIDE` enables the numeric `#TIMESTEP_DELTAT`; the current solver step is available as system variable `TIMESTEP_DELTAT`. Setting `TIMESTEP_MINMAX=OVERRIDE` enables `#TIMESTEP_MIN/#TIMESTEP_MAX`, and those limits persist until changed again.

Use `#TIMESTEP_NEXT` to land on a known waveform kink, switch event, requested sample time or mechanical contact. Do not rely on a floating-point equality test to notice that time has crossed an event.

### END: output, final and repeat

At `END`, set any of the following string variables to `YES` or `NO`:

| Variable | Meaning |
| --- | --- |
| `TIMESTEP_OUTPUT` | Force/suppress writing the accepted solution as an output case. |
| `TIMESTEP_FINAL` | End analysis; also forces output. Set to `NO` to continue beyond initially listed times. |
| `TIMESTEP_REPEAT` | Repeat current step. Output/final flags are ignored for the repeated attempt. |

Adaptive stepping compares a full-step solution against two half steps. If the estimated error is too high, it repeats the step with a smaller size. Therefore never update physical controller state, file output, counters, switch states or accumulated statistics during `FULL`, `FIRSTHALF`, or `SECONDHALF`.

When a step is repeated, OPERA reverts system variables and numerical user variables to their values before the original step. The manual's end-stop example uses string variables as persistent flags across a retry. Use that pattern when a controller must remember that it already requested a retry:

```text
$IF !%COMPARE(&TIMESTEP_STAGE&,INIT)
  $STRING RETRY_PENDING NO
$END IF

$IF <event_detected>&&!%COMPARE(&TIMESTEP_STAGE&,END)
  $IF !%COMPARE(&RETRY_PENDING&,NO)
    $STRING RETRY_PENDING YES
    $STRING TIMESTEP_REPEAT YES
  $ELSE
    $STRING RETRY_PENDING NO
    $STRING TIMESTEP_OUTPUT YES
  $END IF
$END IF
```

Replace `<event_detected>` with a tolerance-based physical condition. Set any new step length at the next `START`, not in this END block.

## Control circuits and motion

### Circuit switching

Build named circuit elements in the Circuit Editor/COMI before relying on their variables. The transient reference exposes loop/component values such as:

| Variable pattern | Meaning |
| --- | --- |
| `loopname_I`, `loopname_DIDT` | Loop current and its time derivative |
| `component_I`, `component_DIDT`, `component_V` | Component current, current derivative and voltage |
| `component_R` | Resistance for a resistor component |

Update functional switch state **only at `END`**. The user-guide hysteretic controller compares actual current with a reference and writes switch variables after an accepted step. Adapt the names to the circuit's actual functional variables:

```text
$IF !%COMPARE(&TIMESTEP_STAGE&,END)
  $CONSTANT #i_ref #i_peak*COS(2*PI*#frequency*TTIME)
  $IF Coil_I>#i_ref+#band
    $CONSTANT #S1 0
    $CONSTANT #S3 1
  $ELIF Coil_I<#i_ref-#band
    $CONSTANT #S1 1
    $CONSTANT #S3 0
  $END IF
  $CONSTANT #S2 !#S1
  $CONSTANT #S4 !#S3
$END IF
```

Verify the component and switch variable names in the circuit model. Test no-load and resistive-limit cases before coupling to nonlinear iron or motion. A controller that changes switches outside `END` can produce inconsistent adaptive-step results.

### Motion control

For group `ROTOR`, the local guide gives this rotational-speed control pattern:

```text
$STRING RO_MOTIONCONTROL SPEED
$CONSTANT #RO_OMEGAZ PI/10
```

`PI/10` is in radians per second. Motion control types are `STATIONARY`, `POSITION`, `SPEED`, and `ACCELERATION`. Position and acceleration require corresponding group-prefixed variables; the detailed manual example uses `#MO_ACCELX/Y/Z` for an acceleration-controlled moving group and derives `#MO_ACCELZ` from force/mass.

Use mechanical variables such as position, angle, speed and acceleration only after confirming their prefix from the group label. Position-driven switch logic should calculate a wrapped position with `MOD`, use a tolerance/rounding strategy, and update circuit state at END.

## Drives, logging and Python hooks

### Drives

The transient reference supports time functions including `DC`, `STEP`, `RAMP`, `RISE`, `SINE`, `COSINE`, `FUNCTIONAL`, `PEAK`, `TABLE`, and `TOFF`. Apply them to source currents, circuit sources, external fields or eligible boundary drives using the solver-specific model properties.

For a table drive, use free-format `(time, value)` pairs in chronological order beginning at zero. The `TABLE` option is a switch-on function; `TOFF` is a switch-off function. Repeated time values can represent a discontinuity in value or first derivative. Beyond the last table time, OPERA holds the final computed value—extend the table deliberately rather than assuming it returns to zero.

### Logs and hooks

Use solver logging for scalar values needed at every accepted analysis time, and output cases for field snapshots. Keep logged expressions limited to decisive diagnostics: current/voltage, central field, loss/temperature extrema, motion state, time step and controller state.

Use `solver.comi` plus Python only when in-solver data access is necessary. Register hooks after validating the installed API. Typical division of work:

- `on_timestep_end`: steady-state detection, controller observations, analysis of accepted time-step data;
- `on_store_time_output`: store sampled component fields/histories and add derived arrays to database;
- external Python: create independent cases, invoke OPERA and collate final results.

For moving meshes, regenerate label-based node/element index sets when the relevant mesh changes. Keep Python callback state explicit and avoid full-field extraction each time step.

## Restart and multiphysics coupling

### Restart

Restart a transient solution from a chosen saved output time through the Post-Processor `COPYCASE` workflow, then add/adjust control-file logic for the new horizon/output cadence. Newly added cases are appended to the database, so case ordering may not be chronological. Do not post-process by raw case index; select by stored time.

### Coupling patterns

For weakly coupled EM–thermal analyses where EM time constants are much shorter than thermal ones:

1. solve electromagnetic model at current material properties;
2. export Joule/ohmic losses as thermal heat source;
3. run transient thermal until a meaningful temperature change/output point;
4. update temperature-dependent electrical/magnetic properties;
5. re-solve EM, export new heat source, and repeat.

Keep EM build, thermal build, EM post-transfer and thermal post-transfer scripts separate. Exchange named tables/arrays with units and a timestamp/case ID. In the supplied example, `solver.comi` plus Python can monitor temperature inside the thermal run and avoid unnecessary stops; retain a non-Python post-processor fallback for debugability.

Do not reduce a single-pulse heat source to a cycle-average loss unless the averaging interval and the thermal time-scale approximation are declared and checked. Preserve either the time-dependent heat field or an energy-conserving sequence of interval-averaged fields. The thermal receiving field must retain its node/element association; OPERA expects `RNODALHEAT` or `RELEMENTHEAT` for imported heat tables.

## Validation sequence

1. **Static reference:** solve a magnetostatic or steady reference at one known drive; check sign, current, material and centre field.
2. **Dynamic uncoupled:** run a simple fixed-step Transient EM case with a smooth drive and one conductive region; inspect current, field and energy evolution.
3. **Time-step convergence:** halve fixed step or compare with adaptive; verify key scalar outputs and switch/event times converge.
4. **Output/log contract:** confirm every expected time/output exists, logs have units/time/case ID, and controller changes occur only once per accepted step.
5. **Circuit/motion:** test switches or motion with a simplified linear model before nonlinear iron/full mesh.
6. **Coupling:** verify transferred heat/temperature/field tables with a single hand-checkable exchange before a long run.
7. **Automation:** run one isolated case folder, then a small bounded sweep; retain failed logs/databases and never overwrite sources.

Report solver/version, control file selected, initial/final time, fixed/adaptive settings, output-time schedule, all override events, convergence evidence and unresolved assumptions.
