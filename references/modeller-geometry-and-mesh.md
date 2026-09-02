# OPERA-3d modeller, labels and mesh

Use this reference while constructing or changing an OPERA-3d model before a solver database is made. It captures the stateful parts of the Modeller that make COMI replay fragile: selection order, working coordinates, labels, booleans, model-body creation and meshing. It is based on the local OPERA 2025 SP1 manuals and three supplied accelerator-magnet COMI files. Confirm exact command spelling and every version-specific parameter in the installed OPERA help before running.

## Contents

1. [Build as a state machine](#build-as-a-state-machine)
2. [Stable naming and selection](#stable-naming-and-selection)
3. [Coordinate systems and transforms](#coordinate-systems-and-transforms)
4. [Geometry and Boolean operations](#geometry-and-boolean-operations)
5. [Labels, materials and boundaries](#labels-materials-and-boundaries)
6. [Create the model body](#create-the-model-body)
7. [Surface and volume mesh](#surface-and-volume-mesh)
8. [Magnet construction patterns](#magnet-construction-patterns)
9. [Pre-solver audit](#pre-solver-audit)

## Build as a state machine

Separate an OP3 build file into explicit stages. A command which assumes a current WCS, picked list, or component view should establish that state itself; never rely on a prior GUI action or a side effect in an included file.

```text
/ 1. Units, tolerances, named parameters and materials
/ 2. Create component bodies / conductors / named LCS
/ 3. Pick and edit: Boolean operations, CELLDATA, FACEDATA
/ 4. Build model body
/ 5. Surface mesh, inspect, then volume mesh
/ 6. Create database / solver configuration
```

Keep the model build, analysis data, solver execution and post-processing in separate COMI files. Stop after every stage that changes topology or mesh state and write the resulting `.opc`/`.op3` only to a case-local folder.

Set modelling tolerances before any geometry. `PRECISIONDATA ABSTOL=... SMALLFACE=...` controls the minimum resolved distance and the removal threshold for negligible faces. The manual states that changing these after geometry exists can make later operations fail. A physically tiny gap must be large relative to the geometry tolerance and adequately resolved by the intended mesh; it must not be represented by accidental coincident or nearly tangent surfaces.

## Stable naming and selection

### Prefer names and labels to entity numbers

The Modeller has both a **picked-item list** and a graphical `FILTER`. `FILTER` only controls cursor interaction; it is not a reliable substitute for an explicit COMI `PICK`. A later command usually consumes the current picked list, often clearing it afterwards.

- Use stable `NAME` and, where the command supports it, `UNIQUENAME`/`COPYIDENTIFIER` for bodies made by a script.
- Use labels to select sets with physical meaning: `YOKE`, `POLE`, `COIL_A`, `AIR`, `END_FACE`, rather than a displayed number.
- Use `LIST` and `PICKEDBODIES`, `PICKEDCELLS`, `PICKEDFACES`, etc. to inspect selection state while developing a script.
- Make a selection immediately adjacent to the operation that consumes it. Clear or replace it deliberately before a different operation.
- Do not replay generated `UNDO STATE=...` or `REDO` records from a GUI log: their state names depend on history length.

The command manual supports selection by entity type and attached properties. Entity identifiers/numbers can change after Boolean operations, imports and topology changes. Current OPERA versions use unique identifiers to improve replay reliability, but the manual still cautions that kernel/version changes can alter numbering. Treat a raw `PICK ... NUMBER=...` as a last-resort, version-pinned action.

### Selection order is physics-relevant for Boolean operations

For `COMBINE`, the **first picked body** determines both the retained name and, for directed operations, the operand that is changed. Never select an unordered multi-body set before `SUBTRACT`, `TRIM` or `CUTAWAY`.

| Operation | Result | First picked body |
| --- | --- | --- |
| `UNION` | Geometric sum | Supplies resulting body name |
| `INTERSECT` | Common volume only | Supplies resulting body name |
| `SUBTRACT` | First body minus each later body; later bodies deleted | Target/kept shape |
| `TRIM` | First body cut by later bodies; later bodies kept | Target/kept shape |
| `CUTAWAY` | First body kept; first body cut away from every later body | Cutter |

`REGULAR=YES` regularizes the Boolean result and removes unnecessary internal faces/sheet artifacts. `REGULAR=NO` can intentionally retain sheet faces but is more likely to create geometry that cannot be meshed; use it only with a stated purpose and inspect the result.

## Coordinate systems and transforms

### LCS versus WCS

`LCS` creates or resets a named local coordinate system using an origin and Euler orientation. Its values are stated in the **current WCS**. `WCS OPTION=SET LCNAME=...` makes that LCS the working system; `WCS OPTION=UNSET` returns to the global system.

The WCS affects positions/vectors in primitive creation, `LCS`, `TRANSFORM`, `SWEEP`, and morphing commands. It does not magically change existing global geometry. At the start and end of every local construction block, set the WCS explicitly:

```text
LCS LCNAME=POLE_END X0=... Y0=... Z0=... THETA=... PHI=... PSI=...
WCS OPTION=SET LCNAME=POLE_END
/ create, cut, or sweep local geometry here
WCS OPTION=UNSET
```

`WCS OPTION=PICKED` can derive a local frame from a picked vertex/edge/face and is excellent for interactive work, but it is only robust in an automated script if the picked entities are unambiguous and named/selected deterministically.

### Transform deliberately

`TRANSFORM OPTION=APPLY` changes the selected geometry; `OPTION=COPY` creates transformed copies; `OPTION=WCS` transforms the working frame. Main types are `DISPLACE`, `ROTATE`, `REFLECT`, `SCALE`, and `EULER`. Displacements and axes are interpreted in the WCS.

- Use `COPY` with a `LABEL` and `COPYIDENTIFIER` when creating repeated pole/coils; it makes later inspection and re-selection possible.
- Use `KEEP=YES` only if several transformations intentionally apply to the same selection. Otherwise clear selection after each transform to prevent accidental re-use.
- Transforming an individual face edits its underlying surface and may invalidate a solid's topology. Prefer rebuilding/sweeping a body for large rotations or reflections.
- LCS and conductor transformations preserve handedness/size: scaling/reflection does not behave like body scaling for them.

## Geometry and Boolean operations

### Choose geometry that matches the intended physics

Use primitives (`BLOCK`, `CYLINDER`, `PRISM`, `SPHERE`, `TORUS`) for yokes, air and simple poles. Use a local coordinate system plus `SWEEP`/`BEND` for curved end packs or bent bodies. Use filamentary/analytical conductor primitives for magnetostatic coil fields when eddy currents and voltage distribution are out of scope; use meshed conductors/circuits when the dynamic physics requires them.

The supplied examples give three reusable patterns:

- Curved dipole: local frames, cylindrical/arc geometry, repeated cuts and Boolean construction around a curved beam line.
- Quadrupole from OPERA-2d: `INSERTOP2FILE` with explicit propagation of group/material/region labels, then transform/extrude and create 3D ends/coils.
- NICA window-frame coil: a `$DO` loop constructs each turn from five `BRICK20` pieces (straight/arc/straight/arc/straight), with current density set from current divided by effective cable area.

For a coil represented by separate pieces, confirm all segment directions before solving. A valid-looking solid can still have a sign reversal in `CURD` or conductor orientation. Perform a low-current Biot–Savart/magnetostatic test and inspect the field direction at a named reference point.

### Repair before meshing

Run `CHECK` on bodies after complex Boolean, import, morph, bend or sweep operations. Use `REPAIR=YES` only after retaining a copy of the pre-repair model and reviewing the report; repair may change topology. Typical mesh failures originate in glancing curved contacts, overlapping or zero-volume regions, tiny sliver faces, or a feature smaller than the current tolerance/mesh size.

Do not use a mesh-size reduction as the first response to a topology failure. First repair or remodel the invalid feature; finer mesh can turn a small geometric defect into a huge, unstable mesh.

## Labels, materials and boundaries

### Cell data carries volume meaning

After component geometry is stable, attach physics and mesh intent to the **picked cells** using `CELLDATA`. Its important fields include:

| Field | Use |
| --- | --- |
| `MATERIALLABEL` | Links the cell to properties defined by `MATERIALS`/B-H data |
| `POTENTIAL` | `DEFAULT`, `REDUCED`, or `TOTAL`; solver-dependent formulation choice |
| `VOLUMELABEL` | Stable post-processing/selection label |
| `GROUPLABEL` | Rigid motion group for `CARMEN` |
| `SIZE`, `NORMALTOL`, `SURFACETOL` | Local mesh refinement controls |
| `ELEMENTTYPE`, `ELEMSHAPEPREF` | Linear/quadratic and tetra/prism/hexa preference |
| `LEVEL` | Conflict precedence when topology is merged |

New cells default to `MATERIALLABEL=AIR`, default potential and linear elements. Do not assume an imported or Boolean-created region retained its intended material; inspect it before `MODEL OPTION=CREATE`.

For Motional EM, every moving/stationary cell needs a `GROUPLABEL`. Cells in one rigid group use the same label; adjacent groups with different labels require a separating group labelled `GAP`. This is a solver validity requirement, not merely visualization metadata. Use unique two-character group prefixes when motion control variables are derived from them.

### Face data separates geometry from boundary condition

Use `FACEDATA` on picked faces to attach a `BOUNDARYLABEL`, local surface mesh controls, element type, and optional boundary-layer information. Define the physical condition separately through `BOUNDARY` by selecting the boundary label (`OPTION=PICK`) and applying it (`OPTION=MODIFY`).

The `BOUNDARY` condition family includes electromagnetic, thermal and stress conditions. Examples such as `NORMMAGN`, `TANGMAGN`, `NORMELEC`, `TANGELEC`, voltage/current-source, thermal temperature/flux/transfer and structural constraints are not interchangeable. Select a condition from the analysis type and the physical symmetry, not from a visual face orientation.

For transient/harmonic functional conditions, a `DRIVELABEL` connects the boundary data to a time/frequency drive. Record its waveform, units, sign convention and the face normal convention next to the assignment.

### Mesh layering is targeted, not a global fix

`FACEDATA` can request forward/backward layers. `FORMMETHOD=GEOMETRY` creates additional geometric faces when the model body is built; `MESH` asks for prism/hexa layers without adding geometry where compatible. Use layers sparingly for actual thin boundary regions or skin/thermal gradients. Geometry layering adds complexity to `MODEL OPTION=CREATE`; it should not be used just to make a display look smoother.

## Create the model body

`MODEL OPTION=CREATE` merges included component bodies into the single analysis model. It is mandatory before `MESH`, and a subsequent geometry edit requires deleting/rebuilding the model body.

1. Pick any deliberately excluded helper/cutter/display bodies and set `MODEL OPTION=EXCLUDE`.
2. Ensure all physical bodies and the background are included; use `MODEL OPTION=LOAD` to inspect inclusion state when debugging.
3. Build the model body.
4. Accept that components are then hidden/locked: only the model body is visible until `MODEL OPTION=DELETE` returns to component view.

Bodies named `BACKGROUND` have special behavior: the created model is trimmed to their union boundary before unioning them. Use one intentional air/background envelope; do not accidentally name a cutter `BACKGROUND`. Cells whose material label is `NULL` are deleted during model-body creation, which can be useful for controlled voids but dangerous if a material label was misspelled.

## Surface and volume mesh

### Mesh sequence and precedence

The required sequence is:

```text
MODEL OPTION=CREATE
MESH ...          / surface facets; system MESH becomes 1 on success
FILL ...          / volume elements; system MESH becomes 2 on success
```

`MESH` global `SIZE`, `NORMALTOL`, and `SURFACETOL` are upper limits. At a cell/face/edge/vertex, OPERA uses the smallest applicable mesh control. Therefore, a forgotten small face/cell value can dominate a whole connected mesh through subdivision matching. Inspect local controls before blaming the global `SIZE`.

`NORMALTOL` limits the normal-angle change between neighboring facets; nonzero `SURFACETOL` limits centroid deviation from a curved surface. Both are geometry-accuracy controls and can increase mesh density sharply on small radii.

### Choose element strategy by topology

| Need | Prefer |
| --- | --- |
| General complex iron/air model | Tetrahedral or `PREFERTETRA` baseline |
| Structured extrusion/sweep and a genuine boundary layer | Hexa/prism preference for suitable cells, then `PREFERTETRA` or mosaic |
| Force hexa/prism wherever topology supports it | Mosaic strategy after a meshability check |
| Debug an element-shape conflict | Tetrahedral mesh first, then restore local preference |

`CELLDATA ELEMSHAPEPREF=HEXORPRISM` is a preference, not a guarantee. The manual requires compatible topology and matching edge subdivisions; otherwise tetrahedra result. `MESH GENERATOR=ONE` is required in cases needing mosaic/prism/hexa behavior, filamentary circuit conductors or multiple periodicities; `TWO` is a tetrahedral-focused generator. Let `AUTOMATIC` choose only after one audited baseline.

### Treat mesh errors as information

- On surface failure, first run `CHECK` and inspect the flagged geometry.
- If faces have no mesh, holes or degenerate facets, search for tiny/sliver faces and near-coincident edges before changing solver settings.
- Use `ACISMESHCHECK` extra tests only while diagnosing a geometry problem; the stronger tests slow meshing.
- Check `NODES`, `ELEMENTS`, `SURFACEFACETS`/`VOLUMEELEMENTS` and compare them with the nominal case. A dramatic jump from a small parameter change is a warning, not an automatic refinement success.
- Refine only field-critical regions (gap, pole tip, conductor/skin layer, end-field feature). Repeat the requested observable at at least two meaningful mesh levels and require convergence of the observable, not merely successful meshing.

## Magnet construction patterns

### Dipole and quadrupole

Use symmetry only after proving its field parity. A wrong magnetic/electric normal/tangential boundary can yield a smooth but wrong multipole. Validate the full/symmetry contract at centre and on two mirrored points before doing a large sweep.

For a 2D-to-3D quadrupole import, treat `INSERTOP2FILE` as an import boundary: verify its sweep distance, coordinate orientation and the intended propagation of `GROUPLABEL`, `MATERIALLABEL`, `REGIONLABEL`, and `USEGROUP`. Confirm that the imported air region, iron quadrants and pole labels survived before applying 3D end geometry.

### Imported quadrupole quick recipe

Use the following short sequence as a review checklist, not as a substitute for the installed `INSERTOP2FILE` example syntax:

1. Create a fresh case folder and state OP2/OP3 units, transverse axes, longitudinal axis and intended symmetry fraction.
2. Import one verified 2D section with an explicit extrusion/sweep length; record the import options for air, material, region and group-label propagation.
3. Inspect the imported air, iron and coil regions by material/region label. Repair labels now; do not create 3D end geometry on an unverified import.
4. Define named end LCS frames, then add end plates, pole-end shaping and coils. Confirm coil `CURD`/circuit orientation at a centre reference point.
5. Create one intentional background, attach symmetry/far-field labels, then run `CHECK` after all Boolean operations.
6. Run `MODEL -> MESH -> FILL`, solve a low-current static baseline and compare the centre-field sign, gradient and symmetry points with the 2D expectation.
7. Only then run the field-quality routine at named reference radius and longitudinal interval; retain raw coefficients before normalising them.

For a curved dipole, establish the beam/reference curve and all LCS before constructing coils and iron. Store the reference radius, bend angle, local tangent and field sign in named parameters. Do not infer an integrated-field direction from the global axis in a curved local magnet.

### Pulsed/window-frame magnets

The supplied NICA example is structurally valuable for `BRICK20` coil generation, but it ends with a static `TOSCAMAGN` analysis. A fast-pulse problem requires a new transient contract: meshed conductive parts, electrical material data, current/voltage drive or waveform, time-step/output plan and an eddy-current validation. Do not label a static model transient merely because the intended magnet is pulsed.

## Pre-solver audit

Before creating the database, report or check all of the following:

1. Expected bodies/cells, no leftover cutters, no unintended `NULL` material, and one intentional background envelope.
2. Material, B-H, conductivity, coil current/current-density and circuit labels for every physics region.
3. Boundary labels exist on the intended faces; their condition matches analysis physics and symmetry.
4. Current sign produces the expected dominant field at one named point.
5. WCS is reset/explicit at construction boundaries and all local coordinate systems are named.
6. `MODEL`, `MESH` and `FILL` completed; element/node counts and local refinement make physical sense.
7. One coarse and one refined mesh reproduce the required scalar observable within the agreed tolerance.
8. A model snapshot, COMI inputs, OPERA version, solver log and mesh statistics are retained in the case folder.
