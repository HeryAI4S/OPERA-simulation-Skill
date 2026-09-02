# OPERA Python and solver hooks

Use standard Python for analysis and orchestration. Use the in-OPERA Python interface only when the computation must access a current simulation/database during pre-processing, post-processing, or an active solve.

## 2D Python

The OPERA-2d reference documents a Python Console, export to Python, writing scripts, an IDE/package workflow, and example categories for pre-processing, circuit editing, solver control, post-processing and interface work. Start by exporting a small known-good GUI model, then refactor the output into parameters and functions. Keep the exported file alongside the version it was generated from.

Do not assume that 2D Python APIs match 3D `operafea` APIs.

## 3D solver-hook pattern

The 3D user guide documents this architecture:

```text
solver.comi                  # loaded once at solver startup
  -> $PYTHON FILE=<hooks.py> # import case-local Python
  -> $PYTHON COMMAND=<...>   # register a selected callback

hooks.py
  -> callback obtains the current simulation
  -> extracts/calculates a small derived quantity
  -> logs/stores an explicitly named result
```

Verify the exact `$PYTHON` syntax, module spelling, and callback identifier in the installed release. The converted local source contains errors in some rendered command/API names.

The guide distinguishes callbacks at the end of every time step from callbacks at stored output times. Use output-time callbacks for histories that should align with saved result states; use every-step callbacks only when the algorithm needs all solver steps (for example, a steady-state detector). Make the sampling cadence explicit.

## Callback template

```python
# hooks.py -- adapt names/API calls after checking the installed OPERA example
import operafea

state = {"samples": 0}

def on_store_time_output():
    simulation = operafea.currentSimulation()
    time_value = operafea.getSysVar("TTIME")
    # Extract only the labels/components this case declares.
    # Calculate a deterministic scalar/array with NumPy if needed.
    state["samples"] += 1
    # Write a case-local row or add a documented database quantity.

# In solver.comi, register this exact callable at the verified hook name.
```

Avoid expensive full-model extraction in every callback. Precompute label indices once when valid, sample only the required components, and retain enough metadata (time, case ID, label, units) for post-run interpretation.

## Database arrays and labels

The 3D Python material describes obtaining a current simulation with `operafea.currentSimulation()`, selecting data by model labels, extracting component vectors such as `RBX/RBY/RBZ`, storing time samples, and adding derived arrays back to a database. It also states that OPERA node/element indices are one-based whereas Python arrays are zero-based.

Apply this rule carefully:

```python
# `opera_indices` identify elements/nodes in an OPERA database.
# Convert only while indexing the matching NumPy component vector.
python_indices = opera_indices - 1
subset = component_vector[python_indices]
```

Never use a nodal index vector with an element-associated array, or vice versa. Preserve association type, component name, label and units with all derived data.

## Typical use cases

| Goal | Suitable pattern |
| --- | --- |
| Report B at a point during a transient solve | `solver.comi` imports Python; callback extracts at a chosen solve/output event |
| Detect periodic steady state | update detector at time-step end; enable output sampling only after criterion is met |
| Calculate losses from transient field history | store selected components at output times; calculate after a complete sample window; write derived arrays with explicit units |
| Coupled EM–thermal solve | use named COMI post-processing transfer files/arrays; optionally use hooks to avoid unnecessary solver stops; validate conservation and time alignment |
| Run many independent design points | external Python, one case folder/database per point; do not rely on a long-lived in-solver global state |

## Python validation

- Test import and callback registration before a long transient solve.
- Run two or three output times with known field/label values, then inspect both `.res`/logs and produced data.
- Guard callback state against duplicate initialization and write exceptions with case/time context.
- For NumPy calculations, test a tiny synthetic vector and an actual one-label case; validate array length, association and unit expression before uploading results.
- Prefer post-processing for heavy operations unless in-solve feedback is necessary.
