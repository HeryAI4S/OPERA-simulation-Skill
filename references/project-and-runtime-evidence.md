# New projects and runtime evidence

## New engineering project

Create an empty, explicitly unsolved workspace:

```powershell
python scripts/init_project.py ./new-magnet --name new-magnet --solver ELEKTRATR
```

This creates `source/`, `scripts/`, `cases/`, `results/`, `project.json` and a short project README. An existing target is refused. It does not generate a physical design, copy source models, claim a successful solve, or assume units/materials. Complete unknown contract fields from the engineering requirements and installed release before creating COMI. For an existing project, preserve its layout instead of relocating its models. Use the [toolchain workflow](toolchain-workflow.md) for case preparation and execution.

## CPU utilization and threads

Use read-only observation first; do not terminate or restart running work merely to diagnose it. Identify the exact solver PID, database path and start time. On Windows, sample the change in process CPU seconds over wall time:

`equivalent busy cores = delta CPU seconds / delta wall seconds`

`whole-machine utilization = 100 * equivalent busy cores / logical processors`

Do not use lifetime CPU seconds or the process's total thread count as current CPU utilization. Inspect active thread CPU deltas, affinity, priority, memory pressure and I/O. One busy core on a many-core machine can produce a small aggregate percentage. Hybrid CPU cores also have different performance; the percentage is not a speedup prediction.

For Opera 2025 SP1, the locally verified Manager path is **Options → Batch Options → General Options**:

| UI option | Meaning |
|---|---|
| Maximum threads per job | Requested upper bound on threads for one solver job |
| Maximum concurrent jobs | Number of independent jobs allowed to run together |
| Preferences → Opera-3d/Post → Default threads | Post-Processor default; does not establish solver thread count |
| Use Acceleration Controller / port | Service enablement/communication; does not prove a thread allocation |

Set concurrency separately, usually one for a single large job. A displayed `Not set` or stored numeric sentinel is not evidence of an actual allocation. Inspect the dialog/confirmed settings and then the new job's `Number of threads = ...` line. A changed queue setting applies when a job starts, not retroactively. License availability may reduce the requested allocation; verify rather than assume. For CPU priority, inspect the actual process and the Manager's solver/batch options tab; use Normal when appropriate, not High as an automatic performance fix. Tab captions can vary by release.

With threads confirmed, inspect the current phase: coil-field preprocessing, matrix assembly, factorization/iteration, field averaging or file output. Even a multithreaded run need not saturate all cores throughout. Distinguish a phase with no new log lines from a stalled process by CPU deltas and subsequent progress. Inspect all live jobs; avoid launching duplicate jobs as a diagnostic.

## Audit actual solver settings

Use the matching `.res` run header and runtime lines as evidence for version, analysis type, time range, step size, output schedule, threads, cuts, solver/preconditioner and completion. A source `.opc` can contain multiple historical ANALYSISDATA records: use it for cross-checking, not as proof of the active run. Never inherit the previous case's linear solver, mesh or convergence status when the new log has not printed them yet.

Record the configured analysis tolerance separately from runtime residual thresholds; identical-looking numbers may represent different criteria. Distinguish a configured nonlinear workflow from actual nonlinear material behavior. Record linear-solver warnings separately from the final nonlinear residual and normal completion. In edge-element analyses, heed the runtime statement if quadratic mesh elements are treated as linear except in Post display.

## Transient loss from solver logs

For a completed fixed-step transient run that prints `Performing full step from ... to ...` followed by `Ohm Loss in meshed volume = ... [W]`, use:

```powershell
python scripts/extract_solver_loss.py ./case.res --initial-power 0 --out ./loss-report
```

Use zero only after verifying the initial state; `--initial-power` is an explicit caller-supplied assumption. This parser supports a single complete run and continuous accepted full steps, including D-exponent numbers. It deliberately rejects ambiguous retries, duplicate/missing steps, missing losses, concatenated runs and incomplete final output. For other log formats, failed/retried steps or multiple simulations, use native Post extraction or extend and test the parser for that release; do not delete records to force acceptance.

Outputs are a CSV power/cumulative-energy history and JSON with source-log SHA256, interval, sampled peak, mean power, threads, warnings and evidence limits. Existing output directories are refused. The input log and database are not modified; source paths in outputs are local provenance, not files to publish. This is log post-processing, not native `.op3` reload validation.

Integrate every available accepted-step power record with trapezoidal quadrature. Field-save intervals can be coarser than solver-step log records. Report `P(t)` in W, interval energy in J and interval mean power separately. Preserve ramp/hold/down-ramp boundaries from the actual drive data; a ramp plus hold is not a full cycle and its interval average is not a repetition-period heat load. Label maxima as sampled peaks. Decimation of one history checks sampling sensitivity, not solver time-step convergence or an error bound.

`Ohm Loss in meshed volume` is a native mesh-volume total. Do not multiply it again by an assumed symmetry factor or call it whole-magnet loss without checking the release/model convention. Inspect actual materials, conductivity units/functions and source representation: a model filename is not evidence of an iron material or hysteresis model. Biot-Savart-only winding sources do not resolve winding internal loss. Separate AL/steel/other bodies only through verified native per-label volume integration or supported per-material results, not by apportioning the total. Read [transient losses](transient-losses.md) for ENERGY/POWER, JH/EJ, hysteresis and symmetry semantics.

Preserve functional-conductivity warnings, linear nonconvergence and field-error estimates. A small final nonlinear residual is not mesh/time-step independence; a J-field error estimate is not directly a loss-error percentage. Compare cases only after matching geometry, material volumes/properties, waveform, units, symmetry, conductor representation and integration interval. A changed total on a finer mesh alone does not establish convergence or a design improvement.

For native per-material extraction and domain reconstruction, use the [material loss and symmetry audit](native-loss-and-symmetry-audit.md). It includes the numeric Post export contract and `audit_material_loss.py`; same-domain closure does not prove whole-magnet coverage. The [project-derived lessons](project-derived-lessons.md) summarize the tested workflow and corrected interpretations without distributing project artifacts.
