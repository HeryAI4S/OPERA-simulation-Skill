# OPERA result transfer and data contracts

Use this reference whenever a result leaves one OPERA analysis and becomes input to another OPERA analysis, an OPERA–Simulink port, Python code, a CSV/table, or an external post-processing workflow. The goal is not merely to “export data”, but to preserve the physical identity of every value: geometry, coordinates, units, component convention, time/frequency, mesh location, and source case. It is based on the local OPERA 2025 SP1 Post-Processor `TABLE` documentation and coupled EM–thermal application note.

## Contents

1. [Choose the transfer mechanism](#choose-the-transfer-mechanism)
2. [Define a data contract](#define-a-data-contract)
3. [OPERA table-file transfer](#opera-table-file-transfer)
4. [Transfer between different meshes](#transfer-between-different-meshes)
5. [EM–thermal and multiphysics loops](#emthermal-and-multiphysics-loops)
6. [Simulink, Python and external files](#simulink-python-and-external-files)
7. [Validation, provenance and failure handling](#validation-provenance-and-failure-handling)

## Choose the transfer mechanism

| Need | Preferred mechanism | Do not use it for |
| --- | --- | --- |
| Add/interpolate field values into another OPERA database | Post-Processor `TABLE` then `SYSVARIABLE` | A scalar controller signal that needs each transient step |
| Transfer heat source, temperature-dependent property field or magnetization between analyses | Named `.table` files plus case-specific post COMI | An undocumented one-shot copy without unit/time/mesh metadata |
| Exchange scalar input/output every transient step with a controller | Opera Analysis block ports (`#` inputs, system/user scalar outputs) | Full field-map transfer |
| Extract a moderate field grid/history for Python/MATLAB | `TABLE`, `GRID`, or `LOGGEDDATAFILE` into a case-local data file | A mesh-attached field required by a later OPERA solver |
| Calculate/store values during a solve | `solver.comi` + Python hooks after installed API verification | Replacing a transparent post-processing transfer when hooks are unnecessary |
| Summarize a parameter sweep | External Python reads per-case files and writes a manifest/CSV | Mutating a shared source OP3/database |

Use the most native mechanism that retains the data's semantics. A screenshot, graph or manually copied number is not a transfer artifact.

## Define a data contract

Create a small machine-readable manifest next to every exported file. The receiving script must validate it before consuming the data.

| Field | Example |
| --- | --- |
| `dataset_id` | `case-017_em_joule_heat_t0p25` |
| `producer` / `receiver` | `ELEKTRATR` / `TEMPOTR` |
| `source_op3` and source case/time/frequency/phase | `em.op3`, case 12, `t=0.25 s` |
| geometry/mesh identity | source model hash, node/element count, selected labels |
| coordinate frame | global Cartesian or named local frame with origin/orientation |
| point location | nodes, element centroids, field buffer, line, surface or volume |
| quantity semantics | `JHD`, `B`, `H`, temperature, loss density, field integral, etc. |
| component convention | real/imaginary, global/local, normal/tangential, sign convention |
| units and file format | OPERA internal / FORMAT 1 / user units FORMAT 2; column unit expressions |
| coverage | full model, selected volumes, valid coordinate bounds, missing-value rule |
| provenance | script revision, OPERA version, timestamp, checksum |

For scalar data, the same contract applies in compact form. Record whether a value is instantaneous, amplitude, phase, time average, peak, accepted transient-step value, or a post-processed integral.

## OPERA table-file transfer

The OPERA-3d Post-Processor `TABLE` command reads field-point coordinates and optional values, evaluates expressions where needed, and writes to a file, an internal buffer, or a database. Its main parameters are:

| Parameter | Meaning |
| --- | --- |
| `INFILE` | Source: filename, `NODES`, `ELEMENTS`, `DBASE`, `SELECTION`, `SUBNODES`, `SUBELEMENTS`, or `TEMP` buffer |
| `OUTFILE` | Destination: filename, `TEMP`, `NULL`, `DBASE`, `SUBNODES`, or `SUBELEMENTS` |
| `F1` … `F12` | Expressions/columns to write or field names to import |
| `NAME1` … `NAME12` | Column names |
| `UNIT1T` … `UNIT12T` | Unit expressions for columns |
| `COLUMNS` | Number of written columns |
| `FORMAT` | Table representation; reference documents internal Format 1 and user-unit Format 2 |
| `BUFFERNAME` | Name when output is an internal buffer |

Before a transfer, activate and load the intended source/receiver database explicitly. A bare `LOAD` or stale active case is not enough evidence of source identity.

### Export for external tools

For a MATLAB/Python/CSV consumer, normally write coordinates plus named values and explicit units. Use FORMAT 2 if the file is intended for users/external software in current OPERA units; use a documented internal-unit representation when the file is intended to be read back as OPERA database field data. Do not assume a filename extension conveys units.

```text
/ Shape only: verify exact units/names against installed release.
TABLE INFILE=NODES OUTFILE=receiver_nodes.table F1=X F2=Y F3=Z UNIT1T=LENGU UNIT2T=LENGU UNIT3T=LENGU COLUMNS=3

/ In source database, evaluate values at receiver coordinates.
TABLE INFILE=receiver_nodes.table OUTFILE=source_values.table F1=X F2=Y F3=Z F4=<documented_field_component> COLUMNS=4
```

### Validate before importing

Use `TABLE OUTFILE=NULL` to test input-file format without output/calculation. Check record count, coordinate bounds, column names, unit factors, min/max, and several known sample points before writing into a database. If field-point evaluation encounters a point outside usable model space, OPERA can abort and set that point/subsequent values to zero according to `SET` abort behaviour; treat unexpected zeros as a failed transfer, not valid physics.

## Transfer between different meshes

The documented four-stage `TABLE` workflow transfers fields even when source and receiver finite-element meshes differ:

1. Load the receiving simulation and export its node coordinates to a table.
2. Load the source simulation and evaluate source fields at those receiver coordinates; write a second table.
3. Reload the receiver and import that second table into its database (`OUTFILE=DBASE`, `SUBNODES`, or `SUBELEMENTS` as appropriate).
4. Register imported fields with `SYSVARIABLE` before later post-processing/analysis uses them.

For fields copied between simulations, use OPERA's documented internal field names, for example real magnetic-field components `RHX`, `RHY`, `RHZ` (and imaginary `IHX`, `IHY`, `IHZ` for complex fields), rather than friendly labels such as “Hx”. For electric fields, use the documented `REX`, `REY`, `REZ` naming convention where applicable. With `SYSVARIABLE`, specify the field stem/type as documented; the reference notes that a system-variable request removes leading real/imaginary prefix and vector component suffix.

### Select import destination deliberately

| Destination | Use when | Critical limitation |
| --- | --- | --- |
| `OUTFILE=DBASE` | Data covers all nodes or all element centroids | Record count and location must match the receiver database expectation. |
| `OUTFILE=SUBNODES` | Nodal data belongs only to selected receiver volumes | A newly created vector is zero outside supplied nodes; select intended volumes first. |
| `OUTFILE=SUBELEMENTS` | Element-centroid data belongs to selected volumes | Input record order/location constraints matter; a new vector is zero in unprovided elements. |
| `OUTFILE=TEMP` | Inspect or reuse a calculated data set inside Post-Processor | It is not durable until written/exported. |

Prefer `INFILE=SUBNODES` over `INFILE=SELECTION` if the table must later be loaded back using `OUTFILE=SUBNODES`. At interface nodes, ensure field lookup is restricted to the selected volume when a quantity is multivalued; otherwise a correct coordinate can receive the wrong side's value.

### Cross-mesh transfer acceptance tests

1. Same coordinates: export/import a simple analytic or uniform field and verify exact component/sign/unit recovery.
2. Source/receiver domain overlap: prove every receiver coordinate lies in valid source field space; report excluded/zero points.
3. Conservation/physics check: compare integrated power, flux, total heat or another relevant invariant before/after interpolation.
4. Mesh sensitivity: repeat with a refined source and/or receiver mesh; separate interpolation error from solver discretization error.
5. Interface check: sample both sides of material/contact boundaries where field values can be discontinuous or multivalued.

## EM–thermal and multiphysics loops

The local coupled EM–thermal example uses weak coupling because electromagnetic time constants are usually much shorter than thermal time constants. Its reproducible data loop is:

```text
EM at current material state
  -> export spatial ohmic/Joule heat source
  -> thermal run with that source until meaningful temperature change
  -> export temperature distribution
  -> update temperature-dependent EM material properties
  -> re-run EM and refresh heat source
  -> repeat until final time / convergence criterion
```

The transfer consists of two distinct physical products: **EM-to-thermal heat source** and **thermal-to-EM temperature/property field**. Give each a separate dataset ID, time/case stamp, source material/volume labels and unit. Do not overwrite a generic `Loss.table` or `Temperature.table` in a multi-case study.

The application note describes post-processing COMI scripts for both sides and optionally Python hooks to detect when thermal temperature change requires an EM recomputation. Use a fixed post-processing schedule first; only replace it with Python monitoring after the same recomputation points and transfer values are reproduced.

For magnetization, external-field and combined E/B workflows, use the same discipline: table of receiver points → source evaluation → receiver import → `SYSVARIABLE` registration → solver/post validation.

## Simulink, Python and external files

### Opera Analysis block scalar exchange

Use Simulink only for small scalar/vector port values, not mesh fields. Input ports update OPERA `#` user variables; outputs expose OPERA user/system variables. At each accepted OPERA step, outputs are sent to Simulink, Simulink advances to that time, inputs are written back, and OPERA advances again. Record port units, signs, initial values and ownership in the interface table described in [Simulink co-simulation](simulink-cosimulation.md).

If a controller needs an integral field/harmonic, calculate and expose a named scalar only at an intentional output rate. Do not launch an expensive full-field `POLAR`/`MAP`/`FIT` calculation on every transient substep unless its cost and numerical effect have been validated.

### Python and external data science

Use Python for case generation, parsing structured output, numerical reduction, regression tests and a final summary manifest. Keep the OPERA transfer artifact as a table/database field when another OPERA solver must consume it. For each Python-produced input table, validate schema, coordinate order, finite values, units and checksum before `TABLE` import.

Use `LOGGEDDATAFILE` for compact history/buffer CSV-style exchange and `GRID` for regular grid data. Preserve a raw OPERA table alongside any converted CSV/NumPy format so a future OPERA rerun is not dependent on a third-party conversion.

## Validation, provenance and failure handling

### Minimum transfer manifest

```text
dataset_id,producer_op3,producer_case_or_time,receiver_op3,
quantity,components,unit_format,coordinate_frame,location_type,
record_count,mesh_id,source_script,checksum,status
```

### Required checks

1. Source and receiver database/case/time/frequency are explicitly logged.
2. Coordinate frame, units, real/imaginary convention and component order match on both sides.
3. Record count and selected node/element/volume coverage are expected.
4. No unexpected zero, NaN, out-of-domain or duplicated coordinate exists.
5. At least one hand-checkable point and one relevant global/integral quantity agree within tolerance.
6. Imported field is visible through `SYSVARIABLE` before it is used in another command/solver.
7. Every generated table/CSV uses a case-local immutable-ish name; source OP3/model is not overwritten.

On failure, keep the source/receiver tables, manifests, logs and OP3 case copies. Do not silently fill missing data with zero, apply an unexplained symmetry multiplier, or continue a coupled iteration using a stale heat/property field.
