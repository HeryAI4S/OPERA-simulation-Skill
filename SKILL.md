---
name: opera-simulation
description: Use when planning, building, scripting, automating, or validating CST Studio Suite OPERA 2D or 3D electromagnetic simulations, including model setup, `.comi` command files, OPERA Python/`operafea` hooks, batch studies, field and harmonic extraction, transient Joule/eddy/hysteresis/iron-loss evaluation, native particle or beam tracking, and coupled electromagnetic-thermal-motion workflows.
---

# OPERA simulation

Use this skill to make an OPERA workflow reproducible and version-aware. Prefer a small, traceable set of input scripts over opaque GUI-only steps.

## Start with a simulation contract

Before writing files, establish the following from the user's model or project:

1. Select **OPERA-2d** or **OPERA-3d**, the installed version, analysis type, units, coordinate convention, symmetry, physics, and requested observables.
2. Identify the starting artifact: an existing `.op2`/`.op3`, a GUI model to export, or a model built from scratch.
3. Write the parameter names, nominal values, sweep ranges, result locations, and acceptance checks. Preserve the original model; put generated cases in a dedicated working directory.
4. Inspect the installation's matching Examples folder and local help before emitting solver-specific commands. Do not infer exact command keywords from another solver, another major version, or OCR-corrupted Markdown.

Ask only for information that materially changes physics or destructive actions. State explicit assumptions for incomplete geometry, material data, boundary conditions, excitation, and convergence requirements.

## Choose the control layer

| Need | Preferred layer |
| --- | --- |
| Build/edit geometry, set variables, standard pre/post processing | COMI |
| Per-time-step decisions, NumPy calculations, derived data stored during a solve | Python plus `operafea` hooks |
| Repeat whole cases, isolate failures, collect results | External Python launcher orchestrating versioned case folders |
| Fast exploratory editing or export of a 2D GUI model | OPERA-2d Python console/export |
| Closed-loop transient co-simulation with a MATLAB controller/circuit/plant | MATLAB/Simulink Opera Analysis block on Windows |
| Motion or transient circuit control | Solver-specific `control_<solver>.comi` / `control_carmen.comi` |
| Coupled analyses | Separate build, solve-control, and post-transfer scripts; exchange only named result files/arrays |

Read the relevant reference before generating code:

- Read [new projects and runtime evidence](references/project-and-runtime-evidence.md) for new engineering projects, CPU/thread diagnosis, solver-setting audits, or loss extraction from completed solver logs. Use `scripts/init_project.py` to scaffold a new project without launching OPERA and `scripts/extract_solver_loss.py` for supported single-run transient logs.
- Read [COMI and automation](references/comi-and-automation.md) for file naming, templates, batch design, and validation.
- Read [COMI command atlas](references/comi-command-atlas.md) when selecting/reviewing OPERA-2d or OPERA-3d commands, their program context, command state, and required ordering.
- Read [OPERA-3d modeller, labels and mesh](references/modeller-geometry-and-mesh.md) before constructing/editing OP3 geometry, assigning materials/boundaries, or creating a mesh/database.
- Read [post-processing, field quality and result transfer](references/postprocessing-and-field-quality.md) for field maps, integrated fields, multipoles, forces, transient summaries, and table-based coupling/export.
- Read [native particle and beam tracking](references/native-particle-tracking.md) whenever using the OPERA-3d Post-Processor **Trajectory/轨迹** menu, `TRACK`, `VIEW`, beam/particle paths, trajectory-patch intersections, beam-density maps, or when choosing between post-processor test-particle tracking and the self-consistent Charged Particle/SCALA solver.
- Read [beam phase space and solenoid tracking](references/beam-phase-space-and-solenoid.md) when the request includes non-zero geometric/normalised emittance, many explicit `TRACK OPTION=PARTICLE` rays, electron or heavy-ion charge/mass/energy conversion, solenoid focusing/Larmor rotation, field-on/off comparison, or an exit-plane beam distribution. Reuse a project-supplied, runtime-validated template when available; this repository does not bundle OPERA models or result databases.
- Read [result transfer and data contracts](references/result-transfer-and-data-contracts.md) whenever fields, losses, temperatures, material properties, transient scalars, or result tables move between OPERA analyses, meshes, Simulink, Python, or external tools.
- Read [transient losses and electromagnetic-thermal heat sources](references/transient-losses.md) whenever the request mentions pulsed or transient loss, Joule/ohmic loss, eddy-current loss, `JHD`, `LOSS`, `POWER`, `JH_<name>`, `EJ_<name>`, `HLOSS`, iron/core loss, hysteresis, `SIBCLOSS`, loss-energy integration, or an EM-to-thermal heat source. Use its single-pulse versus periodic-loss decision gate before choosing a solver or post-processing method.
- Read [engineering toolchain workflow](references/toolchain-workflow.md) when creating a reusable study, COMI preflight, parameter sweep, per-case manifest, result schema, or convergence-gated automation. Use the bundled `scripts/comi_preflight.py` before preparation and `scripts/run_cases.py` to create isolated cases; execution requires explicit opt-in.
- Read [transient simulation and control COMI](references/transient-simulation-and-control.md) for Transient EM, Motional EM, Quench, or Transient Thermal setup; time-step control; circuit switching; and restart/coupling logic.
- Read [OPERA–MATLAB/Simulink co-simulation](references/simulink-cosimulation.md) whenever an Opera Analysis block, MATLAB controller, external circuit/plant, fixed/adaptive co-simulation step, or Simulink signal interface is involved.
- Read [accelerator-magnet modeller patterns](references/accelerator-magnet-modeller-patterns.md) when building a dipole, quadrupole, curved magnet, extruded OPERA-2d section, or BRICK20/saddle coil.
- Read [Python and hooks](references/python-and-hooks.md) for `operafea`, transient callbacks, array indexing, and post-processing patterns.
- Read [documentation map](references/documentation-map.md) to select the authoritative local manual section and locate examples.

## Organize every scripted project

Use this layout unless the existing project has an established equivalent:

```text
project/
  source/                 # hand-maintained model and parameter sources
  scripts/
    model-build.comi
    solver.comi            # initialization/hooks when appropriate
    control_<solver>.comi  # transient control only when appropriate
    post-process.comi
    hooks.py
  cases/
    case-<id>/             # isolated generated run; never overwrite source
  results/
    summary.csv
  run_cases.py             # external orchestrator, if a sweep is needed
  README.md                # commands, version, units, assumptions, checks
```

Keep geometry/physics parameters in one clearly labelled source of truth. Use stable, solver-safe labels for material regions, coils, circuits, and result probes; Python extraction depends on those labels.

## Implement in small, verifiable stages

1. **Baseline** — run one nominal, GUI-verified case. Check units, material assignment, excitation direction, boundaries, mesh, solver completion, and one physically expected field/result value.
2. **Script** — reproduce that case from scripts. Keep model construction, solve control, and post-processing separate. Add comments for units, sign convention, inputs, outputs, and assumptions.
3. **Observe** — write scalar checks and machine-readable output for each case: solve status, key maximum/minimum, integrated quantity, and input parameter values.
4. **Automate** — create a fresh case folder per parameter set. Generate inputs deterministically, run with bounded concurrency, record executable/version/command/return status, and retain logs.
5. **Scale** — only after the baseline and one changed case pass. Stop or mark failed cases rather than silently using partial output.

For a field-quality or magnet task, independently sanity-check symmetry/parity, current sign, expected dominant harmonic, and normalization radius before trusting multipole results.

## COMI and Python rules

- Use COMI for the command language; use `$PYTHON FILE=...` or `$PYTHON COMMAND=...` only after confirming the exact syntax in the installed version. Keep `.py` and the COMI file in the working folder when the workflow relies on relative loading.
- Use a `solver.comi` initialization file to import/register Python callbacks for a 3D solve. Select the callback event deliberately: end of every time step versus stored output times is a correctness/performance choice.
- For Simulink co-simulation, use `#` user variables only for Simulink-to-OPERA inputs and expose a small, documented set of OPERA scalar outputs. Treat the accepted OPERA step boundary as the exchange boundary; do not create an undocumented simultaneous feedback loop.
- Keep callback code short, deterministic, and exception-safe. Make persistent counters/state explicit and emit enough context to identify the failed case/time.
- Remember that OPERA database node/element indices are documented as one-based while NumPy arrays are zero-based; subtract one only when accessing the corresponding Python array.
- Treat `$` command forms, command separators, variable spellings, and API names extracted from the converted manuals as leads to verify, not copy-paste truth. The source conversion contains visible transcription artifacts.

## Validate before handoff

Perform checks proportional to the change:

- Parse/review generated COMI and Python for undefined variables, quoted paths, and output collisions.
- Run a no-sweep baseline and inspect the OPERA solver/result log for errors and warnings.
- Confirm each generated case has its own database, log, and result destination.
- Compare one automated result with a trusted manual/reference result. For sweeps, check continuity and expected monotonic/periodic trends where physics permits.
- For loss studies, verify conductor representation, field association (node versus element), material/volume selection, model symmetry, instantaneous versus time-average/cumulative semantics, and both spatial- and time-integration convergence. Never infer pulse energy from peak loss multiplied by pulse width unless constant power over that interval has been demonstrated.
- Do not delete databases, overwrite a user's source model, or launch a large sweep without explicitly scoped paths and resource limits.

Report the exact files created/changed, run command(s), unchecked assumptions, and validation evidence. If OPERA is unavailable, produce scripts and a concrete execution/verification checklist; never claim the simulation ran.
