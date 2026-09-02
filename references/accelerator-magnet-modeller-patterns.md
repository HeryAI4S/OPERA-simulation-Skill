# Accelerator-magnet modeller patterns

Use these patterns when generating or reviewing OPERA-3d COMI for iron-dominated accelerator magnets. They were distilled from three user-provided models, not from generic geometry assumptions:

## Contents

1. [Common build order](#common-build-order)
2. [2D-to-3D quadrupole workflow](#2d-to-3d-quadrupole-workflow)
3. [Curved dipole workflow](#curved-dipole-workflow)
4. [BRICK20 saddle-coil workflow](#brick20-saddle-coil-workflow)
5. [Air regions, mesh, materials and boundaries](#air-regions-mesh-materials-and-boundaries)
6. [Solve and regression checklist](#solve-and-regression-checklist)

| Source pattern | Pattern extracted | Solver at end of source |
| --- | --- | --- |
| Curved-dipole user model (not redistributed) | Arc-defined pole/yoke, local coordinate systems, segmented `ARC`/`STRAIGHT` coils, end features | `TOSCAMAGN` magnetostatic |
| 2D-to-3D quadrupole user model (not redistributed) | 2D quadrupole import/extrusion, hyperbolic pole source, end plates/chamfers, racetrack-style coil pieces | `TOSCAMAGN` magnetostatic |
| Fast-pulsed window-frame dipole user model (not redistributed) | Multi-turn saddle coil assembled from `BRICK20` segments and graded air mesh | `TOSCAMAGN` magnetostatic |

The source models and their machine-specific paths are intentionally excluded from the public skill. The reusable patterns below are paraphrased engineering guidance, not redistributed OPERA databases or private COMI files.

The third source is associated with a fast-pulsed dipole design, but this particular COMI ends with a magnetostatic solve. Treat it as a geometry/current-density/mesh template. Add an ELEKTRA transient analysis, circuit and solver-specific control file only after the pulse waveform, conductor model, eddy-current requirements and output cadence are specified.

## Common build order

Build in this order. Do not mix material, mesh, or solve setup into geometry commands until the corresponding geometry is complete and named.

```text
1. Declare inputs and calculated dimensions.
2. Build/import the iron cross-section and create named bodies.
3. Add end features using local coordinate systems and Boolean cuts.
4. Create conductors with an explicitly checked current-sign convention.
5. Create good-field, coil-air, iron-air and far-background volumes.
6. Select cells/faces and apply mesh, material and boundary labels.
7. Load B-H data and configure nonlinear analysis.
8. Create, mesh, fill, save and solve a case-local OP3.
```

Use a short preamble that makes external resources and output locations configurable. The source files contain machine-specific `.op2`, `.bh`, and `.op3` paths; never copy those paths into a new project.

```text
$STRING source_op2 'source\cross_section.op2'
$STRING bh_file 'materials\steel.bh'
$STRING case_op3 'cases\case_001\model.op3'

$EXIST %QUOTE(&source_op2&)
$IF FILEEXISTS EQ 0
  / Write a clear diagnostic and stop before modelling.
  $ABORTCOMI
$END IF
```

Use the exact `$EXIST` spelling and abort/reporting behavior verified by the installed OPERA version. Keep both source and generated output paths quoted when they contain spaces.

## 2D-to-3D quadrupole workflow

The quadrupole sample imports a known 2D OP2 section and sweeps it through a specified length, then uses imported region labels to remove air/auxiliary bodies and set material/mesh properties.

```text
$PARAMETER #length 460
INSERTOP2FILE OPTION=CLEAR
INSERTOP2FILE FILE=%QUOTE(&source_op2&) SWEEPDISTANCE=#length IGNOREAIR=YES GROUPLABEL=YES MATERIALLABEL=YES REGIONLABEL=YES USEGROUP=NO OPTION=LOAD

/ Inspect the imported labels before any PICK/DELETE command.
/ Displace the imported magnet from its source reference plane if required.
```

### Rules for imported sections

- Model the ideal hyperbolic pole profile in the OP2 source when that is the design source of truth. Keep the 3D COMI responsible for extrusion, end shaping, coil, air and analysis setup.
- Preserve group/material/region labels on import. `OPERA_2d_R_...` labels appearing in a generated source are not stable API names; inspect them after every source change and map them to project-level names before automating selection.
- Use `PICK` plus `COMBINE OPERATION=SUBTRACT` to remove unnecessary imported pieces. After Boolean subtraction, inspect/select surviving cells before `DELETE`, because cell identifiers can change.
- Add end plates and chamfers using an `LCS`/`WCS` followed by a temporary `BLOCK`, `TRANSFORM`, and `COMBINE ... SUBTRACT`. Unset the WCS explicitly after each local operation.
- Build a cylindrical/high-resolution aperture volume and a larger far-field background. Apply quadratic elements and smaller target size near the pole/aperture; permit coarser linear elements in remote air.

### Quadrupole coil pattern

The sample closes a coil with two `STRAIGHT` and multiple `ARC` conductors. Treat the coordinate transforms and `CURD` signs as one circuit topology, not independent primitives:

```text
/ Pseudocode: exact orientation must be verified visually and by field sign.
STRAIGHT OPTION=NEW ... CURD=#J ... THETA2=... PHI2=... PSI2=...
STRAIGHT OPTION=NEW ... CURD=-#J ... THETA2=... PHI2=... PSI2=...
ARC      OPTION=NEW ... CURD=-#J ... R1=<end-turn radius> ...
ARC      OPTION=NEW ... CURD= #J ... R1=<corner radius> ...
```

Verify all four poles produce the quadrupole symmetry: zero dipole component at the reference origin, correct gradient sign, and expected alternating current direction. Do not copy `RXY/RYZ/RZX` values without checking which reflection planes the chosen conductor primitive uses.

## Curved dipole workflow

The curved-dipole sample parameterizes a bend radius, pole angle, gap, pole/yoke dimensions, end/chamfer values and current density. It derives geometric angles with `ASIND`, then uses those values for both iron cuts and coil placement.

### Make curvature a first-class input

```text
$PARAMETER #bend_radius 2000
$PARAMETER #pole_angle 30
$PARAMETER #sin_angle SIND(#pole_angle)
$PARAMETER #cos_angle COSD(#pole_angle)
/ Derive all arc positions/angles from these values; do not duplicate literals.
```

- Keep bend geometry in degrees when using `SIND/COSD/ASIND`; do not mix it with radian functions.
- Build round/sector openings with `CYLINDER` and Boolean subtraction when the aperture/end follows the bend radius.
- Create an `LCS` at each end-turn or end-chamfer feature. Put the primitive in that LCS, transform/cut it, then restore global WCS. This keeps formulas local and avoids fragile global-coordinate algebra.
- Use named temporary cut bodies and delete/regularise them only after confirming the target iron body remains valid.

### Segmented curved coils

The source joins `ARC` conductor pieces on the curved sides to `STRAIGHT` pieces in the connecting regions. The arrangement is physically coherent only when all of these agree:

1. `WIDTH`/`THICKNESS` match the conductor cross-section convention;
2. each segment has the same intended `DRIVELABEL`/circuit identity;
3. the local axes (`LCNAME`, `THETA2`, `PHI2`, `PSI2`) make adjacent conductor ends meet;
4. `CURD` signs implement a continuous current path; and
5. symmetry/reflection values do not duplicate a segment with the wrong current direction.

After building, visually inspect every coil segment and evaluate the centre field sign before mesh refinement. A geometrically closed coil with one reversed `CURD` can yield an apparently converged but physically wrong field.

## BRICK20 saddle-coil workflow

The NICA source constructs each turn from five `BRICK20` solids in a `$DO` loop: axial straight, first end arc, transverse straight, second end arc, and return straight. The 20 points encode the curved/second-order conductor geometry; its use is appropriate when simple `ARC`/`STRAIGHT` primitives cannot represent the complete saddle path.

```text
$PARAMETER #turn_count 10
$PARAMETER #current_density -#current/#cable_area

$DO #i 1 #turn_count/2
  / Create the five BRICK20 segments for one half-turn.
  / Derive each segment's longitudinal and transverse offset from #i.
  / Keep CURD, drive label and symmetry convention identical across the five pieces.
$END DO
```

### BRICK20 safeguards

- Keep a documented point-order convention. In the supplied generator in the documentation workspace, P1–P4/P5–P8 are end corners, P9–P12/P17–P20 are end-edge midpoints, and P13–P16 are longitudinal midpoints. Do not rearrange points based on visual intuition.
- Derive current density as `current / actual conductive area`, not nominal cable outer area. The NICA source applies a filling-factor correction to its cable area; make such factors named inputs with units/source.
- Compute turn offsets from cable outer diameter plus insulation/clearance interval. Validate clearance at end bends separately from straight sections.
- Set `DRIVELABEL`, local-coordinate fields, and reflection/symmetry flags explicitly on every segment. An omitted field can inherit a loaded/default primitive state.
- Use `BRICK20 OPTION=LOAD` only as an initialisation pattern; write the complete `OPTION=NEW` parameters for each generated segment.
- Generate a one-turn prototype first. Check continuity, minimum bend radius, conductor overlap, current direction and total ampere-turns before enabling the `$DO` loop for all turns.

## Air regions, mesh, materials and boundaries

All three samples use named volumes and targeted mesh controls. Preserve this hierarchy rather than assigning one global mesh size:

| Region | Purpose | Typical treatment |
| --- | --- | --- |
| Good field | Field quality / harmonics | Explicit named air volume; quadratic elements; smallest target size |
| Coil air | Resolve conductor proximity and fringe field | Quadratic; fine-to-medium size |
| Iron/pole/yoke | Capture saturation and pole-face field | Nonlinear B-H material; quadratic; refinement near pole/gap |
| Far background | Truncate open boundary economically | Large air volume; coarse, often linear elements |

Apply properties only after `FILTER TYPE=CELL` and selection by a stable body/cell identity. In generated models, `IDENTIFIER=A.00001` etc. may change after Boolean operations; do not assume an identifier from a previous geometry revision still selects the intended cell.

The samples label groups of background faces `nm` and `tm`, then assign `NORMMAGN` and `TANGMAGN` through the boundary editor. Interpret these as symmetry/field boundary conditions, not arbitrary default labels:

- derive the boundary plane and expected field parity from magnet symmetry;
- select faces by their actual geometry/orientation;
- confirm the normal/tangential field condition matches that parity; and
- for a full model, use an appropriate open-boundary treatment rather than copying symmetry-plane conditions to every external face.

For nonlinear iron, the samples load B-H data with `BHDATA OPTION=LOAD`, assign `MULINEARITY=NONLINEAR`, and configure `TOSCAMAGN` with a Newton nonlinear solve. Make the B-H filepath, material label and steel grade explicit inputs, then verify the selected curve and saturation range against the intended material.

## Solve and regression checklist

The sample closing sequence is broadly reusable:

```text
MODEL CREATE
MESH ...
FILL ...
ANALYSISDATA OPTION=LOAD PROGRAM=TOSCAMAGN
ANALYSISDATA OPTION=SET PROGRAM=TOSCAMAGN LINEAR=NO NLITERTYPE=NEWTON NITERATIONS=<limit> TOLERANCE=<criterion> ...
/ Use the installed-version SOLVERS form with FILE=%QUOTE(&case_op3&), UNITS=MM, ELEMENT=MIXED and SURFACE=CURVED as appropriate.
```

Before declaring a model reusable, check:

1. Each physical region has the expected material, current density and mesh class.
2. Conductors have no unintended overlap; total current/ampere-turns and field sign are correct.
3. The reference centre and good-field volume are correct for the intended multipole convention.
4. At least one mesh refinement produces stable central field/gradient and harmonic results.
5. The nonlinear residual/convergence log is acceptable and no severe saturation is hidden by a too-coarse pole mesh.
6. The saved OP3 is case-local and none of the source OP2/B-H/model files were overwritten.

For a pulse study, add these tests before moving from the static geometry model to transient simulation: waveform/circuit units, conductor conductivity and eddy-current regions, time-step convergence, stored-output interval, energy/current balance, and agreement with the static solution at a matched quasi-DC current.
