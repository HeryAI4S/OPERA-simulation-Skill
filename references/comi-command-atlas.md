# OPERA COMI command atlas

Use this atlas to locate the right COMI command family before writing or reviewing a script. It inventories the command headings present in the local OPERA 2025 SP1 2D COMI and 3D reference manuals, then records the important state, ordering and parameter rules. Read [COMI and automation](comi-and-automation.md) for language syntax and [documentation map](documentation-map.md) for the authoritative local source. Exact parameter spellings and version availability must still be verified in the installed OPERA help/Examples: converted Markdown has OCR/transcoding defects.

## Contents

1. [How to use the atlas](#how-to-use-the-atlas)
2. [COMI language commands](#comi-language-commands)
3. [OPERA-2d command inventory](#opera-2d-command-inventory)
4. [OPERA-3d Modeller commands](#opera-3d-modeller-commands)
5. [OPERA-3d analysis, circuits and database commands](#opera-3d-analysis-circuits-and-database-commands)
6. [OPERA-3d Post-Processor commands](#opera-3d-post-processor-commands)
7. [State and ordering rules](#state-and-ordering-rules)
8. [Syntax templates and review checklist](#syntax-templates-and-review-checklist)

## How to use the atlas

1. Select the program context first: OPERA-2d, OPERA-3d Modeller, OPERA-3d solver/control COMI, or OPERA-3d Post-Processor. Identical names such as `ARC`, `CLEAR`, `SELECT`, `VOLUME`, `UNITS` or `THREED` can exist in different contexts and mean different things.
2. Identify the active state a command consumes: current WCS/LCS, picked list, component/model view, active database/case, field buffer, selected surface/volume, or open file stream.
3. Verify the command's exact parameter table in the installed release before emitting executable COMI. Treat the parameter names below as navigation aids, not a substitute for that table.
4. Keep model construction, solver input/control and post-processing in separate files. A command file that works in an interactive GUI only because of hidden state is not an automation template.

## COMI language commands

These `$` commands are language/runtime commands shared broadly by OPERA programs; they are not Modeller/Post-Processor commands. Use full names in maintained files.

### Variables, expressions and text

| Form / command | Role | Key rule |
| --- | --- | --- |
| `$CONSTANT #name value` | Evaluate once and retain numeric value | Use for fixed inputs, loop values and captured results such as `INTEGRAL`. |
| `$PARAMETER #name expression` | Retain an expression which re-evaluates | Use when a value must track changing variables/system variables. |
| `$MODELDIMENSION` | Protected parametric geometry value | Use for dimensions intended for model/optimization setup. |
| `$EQUATION` | Implicit/equation-defined variable | Use only with a documented solver/model use. |
| `$SYSVAR` | Define a system-variable name | Do not shadow native system variables. |
| `$STRING name value` | Define/update text variable | Retrieve as `&name&`; strings can persist differently from numeric values in transient retry. |
| `$FUNCTION` / user functions | Define reusable numerical relation | Verify supported form in installed version; no spaces inside expressions. |
| `$PYTHON FILE=...` / `$PYTHON COMMAND=...` | Run embedded Python | Confirm installed API/syntax; keep side effects and callback registration explicit. |

Expressions use `#` user variables, arithmetic and logical operators, functions and parentheses. Use semicolon-separated multiple function arguments, radians for ordinary trigonometric functions and `...D` forms for degrees. Use tolerance tests, not direct equality of calculated floating values.

### Flow control and command input

| Command | Role | Important behaviour |
| --- | --- | --- |
| `$IF`, `$ELIF`, `$ELSE`, `$END IF` | Conditional branch | Use `EQ/NE/LT/...` or a parenthesized logical expression. |
| `$DO ... $END DO` | Numeric loop | Make start/end/increment and output filename dependence explicit. |
| `$FOR ... $END FOR` | Iterate listed expressions/items | Use when a finite declared list is clearer than a numeric loop. |
| `$WHILE ... $END WHILE` | Conditional loop | Include a visible termination/progress condition. |
| `$CYCLE` | Skip to next loop iteration | Use only inside the intended loop. |
| `$EXIT` | Leave loop | Do not confuse with ending an OPERA solver. |
| `$COMINPUT file` | Read a child command file | Relative path is resolved from the parent COMI folder; commands after `|` run before child input begins. |
| `$PAUSE` | Pause interactive command processing | Do not leave it in unattended batch workflows. |
| `$ABORTCOMI` | Stop current command input | Use for explicit validation failure; include a diagnostic first. |
| `$ERRORHANDLER`, `$BREAKERROR` | Control/read error behaviour | Restore handler state after controlled read/check sequences. |

### Dialog, I/O and OS interface

| Command | Role | Important behaviour |
| --- | --- | --- |
| `$DIALOG`, `$ASK`, `$PROMPT`, `$DISPLAYLINE`, `$GROUPBOX` | Build interactive data dialogs | Never make an unattended sweep depend on unanswered dialog input. |
| `$OPEN`, `$CLOSE` | Open/close numbered stream | Use a unique stream, case-local path and explicit `READ/WRITE/OVERWRITE/APPEND` intent. |
| `$READ`, `$WRITE` | Read/write a stream | Pair with `$FORMAT`/`$ASSIGN` where table layout must be stable. |
| `$FORMAT`, `$ASSIGN` | Define output formats/field assignment | Treat as persistent stream state; reset/document it locally. |
| `$BACKSPACE` | Reposition stream | Use only with a documented read sequence. |
| `$EXEC` | Start external program | Check `EXECEXITCODE`; use `WAIT` for a required dependent result. |
| `$OS` | Execute shell command | Restrict to controlled case folders; quote paths and avoid destructive wildcard operations. |
| `$CD` | Change OPERA working folder | This persists; prefer case-local absolute/validated paths. |

## OPERA-2d command inventory

The local 2D COMI reference contains the following command headings. Use it for exact 2D syntax; many operations are not interchangeable with similarly named 3D commands.

### 2D display, drawing and data presentation

| Commands | Primary purpose |
| --- | --- |
| `AXESVIEW`, `COLOUR`, `DRAW`, `ERASE`, `EXTRA`, `PICTURE`, `VIEW`, `VECTOR` | Configure/display geometry, axes, pictures and field vectors. |
| `CONTOUR`, `DATALINE`, `DATAVECTOR`, `DATAVECTORSET`, `LINE`, `POINT`, `CIRCLE`, `CLINE`, `GRID` | Evaluate/present field data on paths, points or grids. |
| `GRAPH`-style workflow via `AXESVIEW`/`DATALINE`/`PROCESSLINE` | Build graphs and derive graph-line data. |
| `LOGGEDDATAFILE`, `READ`, `WRITE` | Persist/read data buffers or text data. |

### 2D geometry, regions and mesh

| Commands | Primary purpose |
| --- | --- |
| `COPY`, `MOVE`, `MODIFY`, `POLYGON`, `RECONSTRUCT` | Create or alter 2D geometry/regions. |
| `GAP`, `GROUP`, `SYMMETRY` | Define air gap/grouping and model symmetry. |
| `MESH`, `SET`, `UNITS` | Set mesh/model options and unit system. |
| `DXFINPUT`, `DXFOUTPUT`, `CONVERT`, `EDIT` | Import/export/convert/edit geometry data. |

### 2D analysis, circuits, motion and post-processing

| Commands | Primary purpose |
| --- | --- |
| `BHDATA`, `EMITTER`, `EXTERNALCIRCUIT`, `LMMOTION`, `RMTORQUE` | Assign material/emission/circuit/linear-motion/rotor-motion data. |
| `CEDITOR`, `SOLVE`, `CLEAR`, `END` | Circuit editing, solve control and session termination/reset. |
| `HARMONICS`, `INTAREA`, `INTCIRCLE`, `INTLINE` | Harmonic and field integral calculations. |
| `TRACK` | Particle/trajectory tracking. |

### 2D command notes

- `INTAREA`, `INTCIRCLE`, `INTLINE` are 2D-specific integration routes; do not substitute the 3D `MAP`/`SURFACE`/`VOLUME` workflow without re-deriving the geometry and units.
- `HARMONICS` is a 2D analysis command; it does not imply the same normalization/projection as the supplied 3D cylindrical harmonic COMI.
- `SOLVE` selects/starts a 2D analysis; confirm analysis type, material/nonlinearity and circuit state before calling it.
- `READ`/`WRITE` appear as both language-level stream commands and in program-specific contexts. Always identify the current program and stream/table contract.

## OPERA-3d Modeller commands

### Session, files, history and UI

| Commands | Purpose / state warning |
| --- | --- |
| `CLEAR`, `END`, `LOAD`, `SAVE`, `IMPORT`, `EXPORT`, `INSERTOP2FILE`, `COMMENT` | Reset/open/save/import/export and store database comment/title text. `INSERTOP2FILE` is the OP2-to-OP3 boundary; verify sweep distance, axes and label propagation. |
| `HISTORY`, `REPLAY`, `UNDO`, `REDO`, `PREVIEW` | History/replay/preview. Do not keep GUI-generated `UNDO STATE=...` in a maintained script. |
| `GUIOPTIONS`, `MOUSE`, `WINDOW`, `PICTURE`, `PRINT`, `TITLE`, `COLOUR`, `THREED` | UI/display only unless a picture is an explicit deliverable. |
| `UNITS`, `VARIABLE`, `PRECISIONDATA`, `COMPATIBILITY` | Units, variable/tolerance/compatibility setup. Set geometry tolerance before construction. |

### Selection, inspection and labels

| Commands | Purpose / state warning |
| --- | --- |
| `FILTER`, `PICK`, `SELECT`, `LIST`, `HIDE` | Graphical filter, picked list, display selection and inspection. `FILTER` does not replace explicit `PICK` in automation. |
| `LABEL`, `RENAME`, `DELETE`, `EXTRACTCELLS` | Attach/revise/delete/extract named entities. Prefer labels/unique names over entity numbers. |
| `MEASURE`, `CHECK` | Measure geometry / locate topology errors. Run `CHECK` after complex Boolean/import/sweep operations. |
| `EDGEDATA`, `VERTEXDATA`, `CELLDATA`, `FACEDATA` | Attach entity properties, mesh controls and labels. Selection type must match the command. |

### Coordinate systems and transforms

| Commands | Purpose / state warning |
| --- | --- |
| `LCS`, `WCS` | Create named local frame / select global or local working frame. Coordinates supplied to creation/transformation depend on WCS. |
| `TRANSFORM` | Apply/copy displacement, rotation, reflection, scale or Euler transformation. `OPTION=APPLY/COPY/WCS`; use `COPYIDENTIFIER` for reproducible copied body names. |
| `MORPH`, `STRETCH`, `TWIST`, `BEND`, `OFFSET` | Change body shape. Check topology and meshability afterwards. |
| `VECTOR`, `WIREEDGE`, `SKETCH`, `SHELL`, `LOFT`, `SWEEP`, `COVER` | Construct paths/surfaces/solids from selected geometry. Picked face/edge orientation matters. |

### Geometry primitives and Boolean operations

| Commands | Typical use |
| --- | --- |
| `BLOCK`, `CYLINDER`, `PRISM`, `SPHERE`, `TORUS` | Fundamental solid primitives. |
| `ARC`, `BLEND` | Curves/edge blending. |
| `COMBINE` | Boolean `UNION`, `INTERSECT`, `SUBTRACT`, `TRIM`, `CUTAWAY`. First picked body determines retained name and directed operand. |
| `MODEL` | Create/delete the single model body used for mesh/analysis. Components become unavailable for direct geometry changes while model body exists. |

### Filamentary and geometric conductors

| Commands | Typical use |
| --- | --- |
| `STRAIGHT`, `ARC`, `SOLENOID`, `RACETRACK`, `BEDSTEAD` | Analytic/filamentary conductor shapes. |
| `BRICK8`, `BRICK20` | Higher-detail brick conductor segments; useful for manually parametrized saddle coils. |
| `FITTEDCPE`, `TANGENTIALCPE`, `HELICALEND` | Specialized coil-end forms. |
| `GEOCONDUCTOR`, `CONDUCTOR`, `CIRCUIT`, `CEDITOR` | Geometric/filamentary conductor and circuit definition/editing. |
| `WINDING` | Winding-tool control and its generated OperaObject data. |

Common conductor fields include current/current density (`CURRENT`/`CURD`), local coordinate reference, circuit inclusion/element, `DRIVELABEL`, rotational/reflection symmetry, and `GROUPLABEL` for motional analysis. Their exact applicability varies by conductor class; never transfer a parameter list from `BRICK20` to `SOLENOID` by assumption.

### Materials, boundaries, model and mesh

| Commands | Purpose / state warning |
| --- | --- |
| `MATERIALS`, `BHDATA` | Define material label properties and B-H data. Check label spelling after imports/Booleans. |
| `CELLDATA` | Assign material, potential, volume/group labels, local mesh size and element preference to picked cells. |
| `FACEDATA`, `BOUNDARY` | Attach boundary label to faces, then define the label's EM/thermal/stress condition. Do not assign a physical boundary from visual orientation alone. |
| `BACKGROUND`, `PERIODICITY` | Far-field/background and periodicity/symmetry setup. |
| `MESH`, `FILL` | Surface then volume mesh. Mandatory ordering: `MODEL OPTION=CREATE` → `MESH` → `FILL`. |
| `SOLVERS` | Database/solver element and related analysis options. |
| `VOLUME` | Modeller volume/region-related command; do not confuse with Post-Processor field-volume integration. |

## OPERA-3d analysis, circuits and database commands

### Analysis setup

| Command | Role | Key parameters/concepts to verify |
| --- | --- | --- |
| `ANALYSISDATA` | Select/configure solver analysis | `PROGRAM`, linear/nonlinear iteration controls, transient `UPDATE`, `DELTAT`, `MAXADERR`, drive scaling. |
| `DBCASEDATA` | Configure database output cases | Solver `PROGRAM`, clear/add options, chronological transient output times. |
| `DRIVE` | Define named functional/time/frequency drive | Drive label, waveform/table, units, phase and target property. |
| `CIRCUIT`, `CEDITOR` | Define/edit electrical circuit | Stable loop/component names become solver/post variable prefixes. |
| `MULTIPHYSICS` | Set coupled analysis relationship | Keep transferred quantities, units and source/target cases explicit. |
| `HEATTRANSFER` | Configure heat-transfer relation | Use only in the matching thermal/multiphysics workflow. |
| `EMITTER`, `EXTERNALCIRCUIT` | Specialized emission/external-circuit setup | Confirm solver support and external file interface. |

The common static magnet solver label is `TOSCAMAGN`; transient/motional examples use `ELEKTRATR` and `CARMEN`. Changing `PROGRAM` alone does not make a static model physically valid for dynamics: add conductive regions, appropriate materials, circuit/drive/output and time-control logic.

### Solver-control COMI variables (not top-level Modeller commands)

Time-step control COMI is invoked by a transient solver from the OP3 case folder. It relies on `TIMESTEP_STAGE` plus documented override strings/numeric variables:

| Stage / variable | Safe use |
| --- | --- |
| `INIT` | Initialize configuration/persistent string state. |
| `START` | Set `TIMESTEP_METHOD`, `TIMESTEP_DELTAT`, min/max limits and `TIMESTEP_NEXT` event alignment. |
| `FULL`, `FIRSTHALF`, `SECONDHALF` | Observe adaptive trial only; no irreversible controller/log state updates. |
| `END` | Update accepted-step switches and `TIMESTEP_OUTPUT`/`TIMESTEP_FINAL`/`TIMESTEP_REPEAT`. |

Use `control_elektratr.comi`, `control_carmen.comi`, solver-specific filename variants, or case-specific control files only after confirming discovery precedence in the installed release.

## OPERA-3d Post-Processor commands

### Database/case and coordinate context

| Commands | Purpose / state warning |
| --- | --- |
| `ACTIVATE`, `LOAD`, `SIMULATION`, `COPYCASE`, `SHOW` | Activate/load database, select a case/output or create a restart-related copy. Confirm active time/frequency/case before every measurement. |
| `SET`, `UNITS`, `SYMMETRY`, `SYSVARIABLE` | Set local field frame/time/phase/options, units, field symmetry and available variables. Vector components are global unless transformed explicitly. |
| `CLEAR`, `END`, `TITLE`, `GUIOPTIONS`, `MOUSE`, `WINDOW`, `COLOUR`, `PICTURE`, `PRINT` | Reset/display/session controls. |

### Field sampling, buffers and fitting

| Commands | Purpose / state warning |
| --- | --- |
| `POINT`, `LINE`, `ARC`, `CIRCLE` | Evaluate fields at one point/path/arc/circle into a buffer. `NP` normally means intervals, therefore `NP+1` sampled points. |
| `CARTESIAN`, `POLAR`, `SPHERICAL` | Generate 2D/3D field-point patches in the selected local frame. |
| `BUFFER` | Create/select/rename/delete field buffers. Switch explicitly before `FIT`, `MAP`, `DATALINE` or `TABLE` use. |
| `FIT` | Fourier fit of complete line/arc/circle cycle or Legendre fit on a sphere; reports `A_n`,`B_n` or spherical coefficients. |
| `PROCESSLINE`, `DATALINE`, `DATAVECTOR`, `DATAVECTORSET`, `GRAPH`, `PLOT` | Build/process graph lines and field data presentation. |
| `GRID`, `LOGGEDDATAFILE`, `TABLE` | Persist grid/buffer/point-evaluated data for external analysis or coupling. |

### Maps, surfaces, volumes and field integrals

| Commands | Purpose / state warning |
| --- | --- |
| `MAP` | Plot scalar/vector data on a generated patch; updates `INTEGRAL`, extrema and locations. Capture `INTEGRAL` immediately. |
| `SURFACE` | Select/integrate/display over surfaces; orientation/normal is physically significant. |
| `VOLUME` | Select labelled volumes and integrate an expression; updates `INTEGRAL`/`VOLUME` and extrema. Reflected/rotated images may not be included automatically. |
| `INTEGRATE` | Force/torque on bodies enclosed by selected surfaces; Maxwell-stress or virtual-work method. |
| `ENERGY` | Energy/co-energy/power-related integrals. |
| `FLUXLINKAGE` | Flux linked by selected conductor classes; converge spacing/axial sampling. |
| `BODY` | Body force-related calculation/display context. |
| `ISOSURFACE`, `THREED`, `CONTOUR`, `VECTOR` | 3D field/surface visualization. |

### Circuits, trajectories and field composition

| Commands | Purpose / state warning |
| --- | --- |
| `CONDUCTOR`, `CEDITOR` | Select/display/edit post-processing conductor/circuit context. |
| `COMBINE` | Combine electric/magnetic fields for particle trajectory calculations; do not confuse with Modeller Boolean `COMBINE`. |
| `TRACK`, `VIEW` | Charged-particle tracking and trajectory display/analysis. |
| `BHDATA`, `ARITHMETIC`, `ANIMATION`, `AXESVIEW`, `IDEAS` | Material/data arithmetic/animation/visualization utilities. |

### Post-processing invariants

- `MAP`, `PLOT`, `SURFACE` and `VOLUME` can overwrite `INTEGRAL`, extrema or active display/buffer state. Capture important values in named `$CONSTANT`s immediately.
- `FIT TYPE=FOURIER` assumes samples span a full cycle; it is not automatically an accelerator multipole convention.
- `TABLE` can transfer fields between different meshes, but after import a field must be made available with `SYSVARIABLE` before later use.
- In transient/harmonic results, record selected time/frequency/phase and whether a reported quantity is instantaneous, amplitude, average, peak or phase.

## State and ordering rules

### Core dependency chains

```text
Component geometry
  -> PICK / CELLDATA / FACEDATA / BOUNDARY
  -> MODEL OPTION=CREATE
  -> MESH
  -> FILL
  -> database + ANALYSISDATA / DBCASEDATA / DRIVE
  -> solver / control_<solver>.comi
  -> ACTIVATE + LOAD (Post-Processor)
  -> SET + sampling/buffer
  -> reduction/export
```

```text
Post field patch
  -> POLAR/CARTESIAN/SPHERICAL
  -> MAP COMPONENT=...
  -> INTEGRAL
  -> $CONSTANT #captured INTEGRAL
  -> next MAP or export
```

### Commands that share names but must not be mixed

| Name | Modeller meaning | Post-Processor meaning |
| --- | --- | --- |
| `ARC` | Create/modify geometric curve/conductor | Evaluate fields along an arc |
| `CLEAR` | Clear model/session data | Reset post data/buffers/variables according to options |
| `COMBINE` | Boolean operation on picked bodies | Combine E/B fields for particle tracking |
| `CONDUCTOR` | Define/select conductor model data | Select/display post conductor context |
| `SELECT` | Modeller display/entity selection | Post display-surface/volume selection |
| `VOLUME` | Modeller volume/region data context | Field-expression integral over selected elements |
| `THREED` | Modeller 3D display | Post field contour/vector/geometry display |

### Highest-risk hidden state

1. Picked order for directed Boolean operations.
2. WCS and LCS active when primitive coordinates or transforms are stated.
3. Component view versus model-body view.
4. Surface versus volume mesh completion (`MESH=1` versus `MESH=2`).
5. Active database, selected case, transient time and harmonic phase.
6. Active field buffer and latest producer of `INTEGRAL`/extrema.
7. Transient time-step stage and whether a step was accepted or only an adaptive trial.

## Syntax templates and review checklist

Use named parameters where the installed command supports them. These are **shape templates**, deliberately not complete executable recipes.

```text
/ Modeller: choose exact PICK selector from installed help
PICK OPTION=... PROPERTY=... LABEL='...'
CELLDATA OPTION=MODIFY MATERIALLABEL=... GROUPLABEL=... SIZE=...

/ Modeller Boolean: pick target/cutter in intentional order first
COMBINE OPERATION=SUBTRACT REGULAR=YES

/ Model + mesh sequence
MODEL OPTION=CREATE
MESH SIZE=... TYPE=...
FILL

/ Post: choose database/case/frame before sampling
ACTIVATE FILE=...
LOAD
SET ...
LINE X1=... Y1=... Z1=... X2=... Y2=... Z2=... NP=... BUFFERNAME=...

/ Post: preserve volatile result
MAP COMPONENT=...
$CONSTANT #result INTEGRAL
```

Before handing off a COMI file, verify:

1. Program context and installed OPERA version are stated.
2. Every command has the required prior state (pick list, WCS, model body, active case, buffer or stream).
3. Exact command parameters were checked in installed help/Examples rather than inferred from this atlas.
4. Model/solver/post files use separate case-local outputs; `OVERWRITE` is intentional.
5. Static/low-drive baseline, mesh/sample convergence and output sanity checks precede automation or a large sweep.
