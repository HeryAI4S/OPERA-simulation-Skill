# Native material loss and symmetry audit

Use this workflow when a transient solver total needs a material breakdown, or when a mesh-domain result is being interpreted as a complete magnet. It was exercised on OPERA 2025 SP1 Post exports from an octant dipole study. The bundled helper audits exported numbers; it does not execute Post or certify a physical model.

## Establish the represented domain first

`MODELSYMMETRY=DATABASE`, a log saying `symmetry none`, or matching material/solver totals does not establish whole-magnet coverage. Geometry can still occupy only the positive octant with no reflected copies active.

Record these independently:

| Evidence | Question it resolves |
| --- | --- |
| Geometry extents and intended physical assembly | Is the actual mesh a full assembly, half, quadrant, octant, or another subset? |
| Magnetic boundaries and excitation parity | Does reflecting this region reproduce the intended physical field? |
| Conductive bodies, cuts, terminals, circuits and source replication | Are scalar losses equal in the proposed copies, including connectivity? |
| Activation/reflection settings used for this export | Have copies already been included by the integration command? |
| Native total and per-label volumes | Does selection cover the expected meshed region with no gaps/overlap? |

For example, a background box spanning `0..1500`, `0..1500`, `0..2500 mm` has volume `5.625e9 mm3`. An unexpanded `ALL_VOLUMES` integral with that volume supports an octant-domain interpretation when the intended assembly extends symmetrically about the origin. A volume match alone does not prove the magnetic/electrical replication is valid.

For a verified octant with identical scalar dissipation in eight copies and no activated expansion, multiply power and interval energy by eight exactly once. Preserve the native values. Times, material energy fractions and normalized harmonic units do not acquire this factor. Full-circle vector field reconstruction requires component parity; see [integrated-harmonic diagnostics](integrated-harmonic-diagnostics.md). Never multiply a local field by eight.

Use the command-specific rules in [transient losses](transient-losses.md): `ENERGY` includes activated copies, while `VOLUME` excludes them. A scalar reconstruction factor is unresolved until the command, geometry and activation evidence agree.

## Extract material power from the same field solution

For each required saved case, activate the intended database, load it, set units, and integrate `J dot E` independently over `ALL_VOLUMES` and each material label. Include nonconducting regions such as air in the volume partition even when their power is zero. Reset the selection between labels; a persistent selection can silently accumulate previous materials.

The following small command pattern was exercised in 2025 SP1 on an unexpanded mesh. Replace filenames, case and labels; confirm syntax and semantics for the installed release. It is a command recipe, not an assertion that a new database has been loaded successfully.

```text
ACTIVATE FILE='case.op3' CASE=2 MODELSYMMETRY=DATABASE
LOAD
UNITS POWER=WATT ENERGY=JOULE LENGTH=MM
ENERGY ACTION=RESET
ENERGY ACTION=ADD LABEL=SHIELD
ENERGY ACTION=INTEGRATE ADAPTIVE=NO
/ Capture numeric TTIME, label index, POWER, VOLUME, ACTIVATE_STATUS.
/ Repeat RESET -> ADD -> INTEGRATE for each label and each saved case.
```

`ADAPTIVE=NO` used eight Gauss points per element in the observed release. It supplies a reproducible baseline; it does not demonstrate spatial quadrature convergence. Record the release's actual integration setting.

Before processing every case, test one state/label with known nonzero loss. Verify time, power, volume and activation status numerically. COMI `$FORMAT`/`$ASSIGN` descriptor sequences can turn a variable such as `TTIME` into literal text. A process exit code and an output file's existence do not validate its columns. If time is literal, recover identity from the native case inventory/load transcript, correct the format, and regenerate numeric evidence. Do not relabel an unverified row by position alone.

Export at least 12 significant digits for the helper's fixed relative `1e-8` / absolute `1e-12` consistency checks (in each column's declared unit). Independently rounded low-precision totals can fail closure even when the underlying solution sums correctly; regenerate a higher-precision export before diagnosing a physical inconsistency. The exercised native stream used this format for a material with index one:

```text
$open 1 'material_native.txt' write
$format 1 exponential 0
$format 2 character
$assign 1 2 1 2 1 2 1 2 1
$write 1 TTIME ' ' 1 ' ' POWER ' ' VOLUME ' ' ACTIVATE_STATUS
$close 1
```

Open the stream once around the complete case/label loop, not once per row. Check the emitted digits and numeric tokens in the installed release; if its format syntax differs, use the documented equivalent. The report records the tolerance and precision contract.

Retain the Post transcript, database/case/time inventory, extraction COMI and source identity. Read-only stat checks establish unchanged size/mtime; a matching hash provides stronger content identity. Export hashes alone do not prove that Post used the intended database. Use `SAVE=NO` for temporary symmetry changes where supported and avoid saving back into the solved source database.

## Audit a numeric export

The helper accepts whitespace-separated records with exactly five numeric columns, no header:

```text
time_s label_index power_W volume activation_status
```

The line above describes the schema; do not include it in the numeric file. Indices are zero-based positions in `--labels`, with `ALL_VOLUMES` first. Remaining labels must form a disjoint exhaustive partition. Use unexpanded native mesh exports in W, seconds and the declared volume unit. The helper does not infer those units or inspect the database/COMI to verify them. D-exponent numbers are accepted; literal tokens, NaN, nonzero activation status, negative power, missing/duplicate labels, nonmonotonic times, volume drift, and power/volume closure failures are rejected. This fixed-geometry helper does not support moving/deforming-volume studies.

```powershell
python scripts/audit_material_loss.py ./material_native.txt `
  --labels ALL_VOLUMES STEEL ALUMINIUM STAINLESS AIR `
  --volume-unit mm3 --solver-csv ./solver-audit/loss_history.csv `
  --out ./material-audit
```

The optional solver CSV uses `time_s` and `mesh_ohmic_power_W` from `extract_solver_loss.py`; `solver_mesh_ohmic_power_W` is also supported for existing project exports. Use the same unscaled domain and interval. Every native saved time must match one solver time and power; denser intermediate solver samples are allowed. The report keeps their all-step energy separate from saved-field quadrature. A mismatch is a reason to inspect units, time, selection, source identity and integration settings, not to renormalize the data into agreement.

A trial step may print power before a rollback/retry. The strict solver-log helper rejects that history even when the run later completes. Keep the log intact; use native saved states for the stated saved-state quadrature, or build a release-verified accepted-step parser. Do not call saved-state energy an integral of every accepted solver step when intermediate accepted substeps were omitted.

The output contains native per-material power, trapezoidal interval energy, interval mean power, sampled peak power, volumes, input SHA256 values and evidence limits. It refuses an existing output directory and does not modify its input files or open OPERA. Output paths are local provenance; do not publish generated reports with private paths.

To add a conditional whole-magnet estimate, supply both options:

```powershell
python scripts/audit_material_loss.py ./material_native.txt `
  --labels ALL_VOLUMES STEEL ALUMINIUM STAINLESS AIR --volume-unit mm3 `
  --full-magnet-factor 8 `
  --symmetry-evidence 'Verified physical octant, equal scalar losses, no activated reflected copies' `
  --out ./material-audit-full
```

The factor is an explicit caller assertion. The helper records it, applies it once, and preserves the native values; it cannot independently prove symmetry or detect a previously scaled input. Omit it when coverage is unresolved. `NATIVE_EXPORT_AUDITED` means the supplied records passed consistency checks, not mesh/time-step independence or engineering acceptance.

## Separate material attribution from a conductivity intervention

Turning off a shield's conductivity changes the electromagnetic solution, including loss in other conducting materials. Consequently:

`total_loss(conductivity_on) - total_loss(conductivity_off)`

is a whole-system intervention effect, not generally the shield's loss in the original solution. For example, on-case shield/other losses of `4/6 W` and off-case losses of `0/8 W` give a total difference of `2 W`, while the on-case shield loss is `4 W`.

Integrate the shield label directly in the conducting-shield case. Report the total intervention effect and changed losses elsewhere separately, at matched times, excitation, interval and domain. If conductivity values also change, this is a material sensitivity study, not a mesh convergence study. Preserve anisotropy and units explicitly: `1 S/mm = 1000 S/m`; a zero tensor component cannot be replaced by the nonzero transverse value without changing current paths.

## State what has actually been checked

Material sum equals `ALL_VOLUMES`, and `ALL_VOLUMES` matches the solver total: **same-domain accounting closure**. This does not establish whole-magnet coverage, source energy balance, accurate material data, resolved lamination loss, or a converged loss prediction.

A ramp followed by a hold is an interval, not a complete pulse cycle. The interval mean power is not a repetition-period heat load. A nonlinear B-H table alone does not establish modeled hysteresis, and a Biot-Savart source alone does not resolve winding internal loss. Preserve linear-solver and functional-conductivity warnings and J-field error estimates independently of normal completion, final nonlinear residual and activation status.
