# OPERA–MATLAB/Simulink co-simulation

Use this reference when a transient OPERA model must exchange signals step-by-step with a MATLAB/Simulink controller, circuit, mechanical model, observer, or supervisory logic. It is based on the local OPERA 2025 SP1 User Guide section “Opera in Simulink System Analysis”. Verify availability in the installed OPERA and MATLAB release before building a project.

## Contents

1. [Scope and prerequisites](#scope-and-prerequisites)
2. [The actual exchange schedule](#the-actual-exchange-schedule)
3. [Build the interface contract](#build-the-interface-contract)
4. [Prepare the OPERA model](#prepare-the-opera-model)
5. [Configure the Opera Analysis block](#configure-the-opera-analysis-block)
6. [Fixed and adaptive time stepping](#fixed-and-adaptive-time-stepping)
7. [Ownership of COMI, control COMI and Simulink](#ownership-of-comi-control-comi-and-simulink)
8. [Build and validate incrementally](#build-and-validate-incrementally)
9. [Failure modes and diagnosis](#failure-modes-and-diagnosis)

## Scope and prerequisites

The Opera Analysis block is a masked Level-2 S-Function backed by an OPERA Windows DLL and an Opera Application object. It is **not available on Linux**. The local guide says the MATLAB path must include both:

```text
%VFDIR%\bin
%VFDIR%\simulink
```

where `%VFDIR%` is the OPERA installation folder. Confirm the installed release supplies the block/library before designing a workflow. Do not imitate the block with GUI automation.

The block supports all OPERA **transient** solvers. Use it when the external system needs feedback during the solve: switched power electronics, a control law, mechanical plant/load, external circuit logic, supervisory protection, or a real-time-like input schedule. Do not use it as the default tool for independent magnetostatic cases or ordinary geometry parameter sweeps; an external case runner is simpler, more parallel and easier to reproduce there.

Each Opera Analysis block creates its own Opera Application object. Multiple blocks are possible, but each can create an independent solver/application and therefore has memory, license, working-file and startup consequences. Prove one block first.

## The actual exchange schedule

OPERA and Simulink have independent solvers; this is a co-simulation exchange, not one shared nonlinear solve. The local manual specifies the following order:

```text
t = 0
  Apply block initialization commands to OPERA.
  OPERA advances one OPERA time step.

At the end of every accepted OPERA step ending at t_k
  1. Send selected OPERA outputs to the Simulink block outputs.
  2. Run Simulink until the same time t_k.
  3. Copy block inputs into named OPERA user variables.
  4. Advance OPERA through its next time step.
```

This order creates a deliberate exchange boundary. A Simulink controller responding to outputs at `t_k` supplies values used for the following OPERA advance; do not describe that as a simultaneous algebraic feedback loop. Make the sample-and-hold/delay convention visible in the Simulink diagram and test it with a simple known waveform.

For each signal, record producer, consumer, unit, sign, valid range, initial value, update cadence and whether it is sampled/held. Never leave a port's meaning implicit from its position in the block diagram.

## Build the interface contract

### OPERA inputs

Block inputs map to OPERA **numeric user variables beginning with `#`**. Typical documented forms are:

| OPERA variable | Example role |
| --- | --- |
| `#V` | Functional voltage/current/drive command |
| `#xx_ALPHAZ` | Motion-group acceleration input |
| `#xx_OMEGAZ` | Motion-group angular-speed input |
| `#I_REF`, `#ENABLE`, `#T_LIMIT` | User-defined controller reference, enable, protection threshold |

Choose solver-safe stable names and declare them in the OPERA model even if their initial value is zero. Do not make a controller input depend on a different COMI assignment that overwrites it later in a timestep.

### OPERA outputs

Block outputs may be OPERA system variables or user variables. Useful documented categories include motion values such as `xx_TORQUEZ`/`xx_ALPHAZ`, circuit values such as `W1_I`, and explicit user-calculated quantities such as a centre-field error or temperature margin.

Expose small scalar observables, not full field arrays. For a large field, loss map or harmonic calculation, save an OPERA output case and run named post-processing at controlled output times; do not try to transfer an unbounded field through Simulink ports.

### Interface table template

Maintain this table beside the `.slx`, OP3 and COMI sources:

| Port | Direction | OPERA name | Unit | Initial value | Owner | Applied/observed at |
| --- | --- | --- | --- | --- | --- | --- |
| `u_voltage` | Simulink → OPERA | `#V` | V | 0 | Simulink controller | next OPERA step |
| `i_coil` | OPERA → Simulink | `W1_I` | A | checked at t=0 | OPERA circuit | end of accepted OPERA step |
| `torque` | OPERA → Simulink | `RO_TORQUEZ` | N·m | checked at t=0 | OPERA motion solver | end of accepted OPERA step |

Replace illustrative variable names with those actually present in the model. The group/circuit prefixes are model-dependent.

## Prepare the OPERA model

1. Build and solve a transient OPERA baseline **without** Simulink using a known drive. Verify units, current direction, materials, mesh, circuit/motion groups, output time schedule and one expected scalar response.
2. Replace only the externalized drive/motion value with a declared `#` input variable. Keep an in-model constant fallback so the baseline can be repeated without MATLAB.
3. Define the few outputs needed by the controller. Check their exact system-variable names in the loaded database; names such as `W1_I` depend on the circuit element/loop label.
4. Configure transient output times for field snapshots and solver logs for high-value scalar diagnostics. The block retains OPERA log/output features; use them rather than relying solely on Simulink scopes.
5. Keep the source OP3 read-only in practice. Set a distinct **working file** for every trial/run; OPERA writes the working copy used in co-simulation.

For `CARMEN`, all cells/conductors need valid motion group labels and group-separating `GAP` regions before the block is introduced. For `ELEKTRATR`, validate circuit source, conductor conductivity and eddy-current response before closing the external control loop.

## Configure the Opera Analysis block

The documented Function Block Parameters include:

| Parameter | Required decision |
| --- | --- |
| Type of time stepping | `Fixed` or `Adaptive` |
| Sample time | Fixed OPERA step or maximum adaptive OPERA step |
| Working directory | Controlled folder containing/receiving the run artifacts |
| Opera file | Source model filename, including extension |
| Working file | Disposable working copy used for the run |
| Number/names of inputs | Ordered list of `#` user variables |
| Number/names of outputs | Ordered list of OPERA system/user variables |
| Initializing commands | Standard COMI commands run only at time zero |
| Output time intervals | Up to three `start, stop, step` intervals |
| Solver | Documented value is `op3solve` |

The block can accept any number of ports; after the first five inputs/outputs, the local guide says additional variable names are entered as a space-separated list. Preserve the port order in the interface table and add Simulink signal names/units. Do not silently reorder a list when adding a port.

Use the initialization field only for short, deterministic one-time COMI actions such as setting initial user variables or selecting pre-existing model settings. Multiple commands on one line are separated with `|`. Do not put a large build script, a destructive file operation, a mesh rebuild or a time-loop controller into initialization commands.

The output schedule supports at most three intervals, each `start stop step`. Use intervals to densify saved OPERA cases near a switch/ramp/peak and reduce storage elsewhere. This is distinct from Simulink solver logging and from internal OPERA steps.

## Fixed and adaptive time stepping

### Fixed step: start here

Start with a fixed OPERA step `Δt_O` and a Simulink discrete/sample configuration that makes the exchange unambiguous. Equal steps are the easiest baseline. The guide also permits Simulink to use a smaller step; a Rate Transition block can make this explicit.

Select `Δt_O` from the fastest physical transient, circuit switching edge, mechanical timescale and required output waveform—not from a convenient controller default. Run a step-halving test and compare current, field, torque/position and controller switch times.

### Adaptive step: only after the fixed baseline

For adaptive OPERA stepping, use a **variable-step Simulink solver**. The block sample time is the maximum OPERA step. The manual recommends limiting this maximum to a reasonable value because a Simulink input change is incorporated only on the next OPERA step.

Set an explicit maximum OPERA step at every controller/switching timescale. If control action or input waveform changes at a known event, configure the OPERA control layer to land exactly on that event (`TIMESTEP_NEXT` where applicable) rather than detecting a crossed event by floating-point equality.

Do not enable adaptive stepping until the following agree between fixed-reference and adaptive runs: event time, final state, peak current/field, key integral/loss and controller switching sequence. Record accepted OPERA steps separately from Simulink minor/internal steps.

## Ownership of COMI, control COMI and Simulink

Use one writer per state variable:

| Layer | Owns | Must not independently overwrite |
| --- | --- | --- |
| Model-build COMI | Geometry, labels, materials, static setup | Runtime input values |
| Simulink block inputs | External drive/reference/command `#` variables | The same variable from a timestep COMI |
| `control_<solver>.comi` | OPERA-internal accepted-step logic, solver step limits/events, internal protection states | Simulink-owned command variables unless explicitly designed as an override |
| Solver | Physical states and system variables | Controller commands |
| Simulink | Controller/plant state and external logic | OPERA system variables |

Keep `control_<solver>.comi` when it is needed for internal time-step alignment, accepted-step circuit switching, motion control or stop/output decisions. At adaptive trial stages (`FULL`, `FIRSTHALF`, `SECONDHALF`), do not mutate controller state or write irreversible logs. If both OPERA and Simulink need protection logic, define precedence and a single `#ENABLE`/fault-latch interface rather than allowing competing switches.

## Build and validate incrementally

### Minimum viable co-simulation

1. Run OPERA alone with a constant drive and save scalar reference traces.
2. Add one Simulink constant → one OPERA input (for example `#V`) and one OPERA output (for example coil current). Verify the output trace matches standalone OPERA.
3. Replace the constant with a slow ramp. Verify time-zero value, first exchanged value, sign, units and exactly when OPERA sees the changed input.
4. Add a discrete controller with explicit rate transition/sample time. Test saturation, enable/disable and a known threshold event.
5. Add nonlinearity, motion, switching or adaptive stepping one at a time.
6. Add field snapshots/thermal transfer only after scalar closed-loop behaviour is stable.

### Acceptance checks

- MATLAB can find the installed Opera Analysis library and starts no hidden second source model.
- Source OP3 remains unchanged; working copy, logs and outputs land in a run-specific folder.
- Port count, order, variable names, units and signs exactly match the interface table.
- At `t=0`, all inputs/outputs have defined finite values; no stale workspace variable supplies an accidental initial state.
- A zero/constant input produces the standalone OPERA baseline within numerical tolerance.
- One ramp or step proves the documented exchange order and controller delay convention.
- Halving fixed OPERA step, then comparing an adaptive run, converges decisive outputs and event times.
- Logs identify OPERA time, Simulink scenario, working-file path, OPERA version, solver, step settings and failure status.

## Failure modes and diagnosis

| Symptom | Likely cause | First diagnostic action |
| --- | --- | --- |
| Block/library cannot be found | MATLAB path lacks `%VFDIR%\bin` or `%VFDIR%\simulink`; unsupported platform/release | Check Windows-only requirement and MATLAB path, then locate the shipped library |
| Input has no effect | Name lacks `#`, a drive does not reference it, or a COMI file overwrites it | Log the user variable at each OPERA output; assign one owner |
| Output stays zero/stale | Wrong circuit/group/system-variable name or no accepted output step | Verify variable in OPERA Post-Processor; reduce to one scalar output |
| Unexpected one-step delay/oscillation | Exchange order misunderstood or controller rate not explicit | Test with a constant/ramp and add Rate Transition/ZOH intentionally |
| Adaptive run misses a switch | Maximum OPERA step too large, event not aligned | Bound max step and request exact event time in OPERA control |
| Source model gets changed | Working file is source filename/path | Use a generated working filename under a unique run directory |
| Slow or out-of-memory run | Excess field output, multiple blocks, oversized model/step count | Reduce outputs to scalars, run one block, profile OPERA outputs separately |
| Non-reproducible restart | Hidden MATLAB state, generic control file, shared output folder | Save scenario parameters, block settings, case-specific control COMI and logs together |

## Handoff checklist

Deliver the `.slx`, source OP3, generated working-file convention, model-build COMI, solver/control COMI, interface table, initialization commands, fixed/adaptive settings, output-interval schedule, one standalone OPERA baseline and one co-simulation validation trace. State explicitly that the block availability and exact installed parameter dialog were verified—or list them as unchecked if OPERA/MATLAB was unavailable.
