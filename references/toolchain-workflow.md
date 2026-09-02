# OPERA engineering toolchain workflow

Use this workflow to turn a COMI/OP3 model into a repeatable engineering study. It is designed for the bundled `scripts/comi_preflight.py` and `scripts/run_cases.py`; neither script runs OPERA by default.

## Contents

1. [Project contract](#project-contract)
2. [Project layout](#project-layout)
3. [Preflight](#preflight)
4. [Prepare and run cases](#prepare-and-run-cases)
5. [Result contract and convergence](#result-contract-and-convergence)
6. [Windows example](#windows-example)

## Project contract

Before automation, define solver/version, units, coordinate system, symmetry, source model, mesh levels, parameter values, drive, requested observables, acceptance tolerances and output folder. The baseline must be a verified manual/GUI or already trusted scripted case.

Use one source of truth for each runtime variable: dimensions/case parameters, solver control, Simulink controller, and post-processing normalisation must not overwrite each other.

## Project layout

```text
study/
  source/
    model-build.comi
    geometry.comi
    post-process.comi
    control_elektratr.comi       # only when required by the solver
  sweep.json
  cases/                         # generated; one folder per parameter tuple
    case-0001/
      source/                    # byte-for-byte copied input tree
      case-parameters.comi        # generated numeric parameters
      run.comi                    # generated entry point
      logs/
      preflight.json
      case-metadata.json
    manifest.csv
```

The generated `run.comi` reads `case-parameters.comi` then `source/<entry_comi>`. Keep the source entry file free of hard-coded case output paths and use the generated `#` variables. Do not run templates in place.

## Preflight

Run static checks before preparing cases:

```powershell
$operaSkill = Join-Path $env:USERPROFILE '.codex\skills\opera-simulation'
python (Join-Path $operaSkill 'scripts\comi_preflight.py') .\source --json .\preflight.json
```

The checker reports missing local `$COMINPUT` targets, absolute paths, unquoted paths with spaces, `OVERWRITE`, `$OS`, `$EXEC`, embedded Python, local `MODEL → MESH → FILL` hazards and variables not defined in that file. It deliberately does **not** prove physical validity or exact OPERA syntax. Resolve errors; review warnings; mark expected case-input variables with `--allow-variable gap_mm` if needed.

## Prepare and run cases

Create `sweep.json` from the template example. Preparation is safe by default:

```powershell
python (Join-Path $operaSkill 'scripts\run_cases.py') .\sweep.json
```

It copies the source tree into each new case, writes the parameter/entry COMI files, performs a local preflight, and writes `cases/manifest.csv` plus JSON. It does not start OPERA.

Only after checking one generated case, provide a version-verified external command in `sweep.json` and opt in to execution:

```powershell
python (Join-Path $operaSkill 'scripts\run_cases.py') .\sweep.json --run --max-workers 1
```

Keep one worker until license capacity, RAM, disk and solver stability are demonstrated. The runner captures launcher stdout/stderr, but it cannot infer OPERA solver success from an arbitrary executable; inspect OPERA logs and write a solver-status scalar to the per-case result table.

## Result contract and convergence

Every post-process file should write a machine-readable row/table with at least:

```text
case_id,source_op3,solver,mesh_level,time_or_frequency,parameter_values,
observable,value,unit,coordinate_frame,normalisation,status
```

The template library includes `template/toolchain/result-contract.example.csv` with the required header. `status` is a gate, not a comment: use values such as `completed`, `solver_failed`, `preflight_failed`, `nonconverged_mesh`, `nonconverged_timestep` or `postprocess_failed`. Do not merge a non-`completed` row into design comparisons, curve fitting, optimisation or a Simulink lookup table.

Compare the nominal case to its trusted baseline, then repeat decisive quantities with a changed mesh, field-sampling density and (for transient cases) time step. Preserve raw field/integral/harmonic values before normalisation. Use the separate result-transfer reference when any values move between meshes, solvers, Simulink or Python.

## Windows example

The bundled scripts work with the Python standard library. They do not discover an OPERA installation automatically and intentionally do not guess a solver command. Set `command` only after verifying the executable and CLI for the installed OPERA release/solver using its Examples/help.
