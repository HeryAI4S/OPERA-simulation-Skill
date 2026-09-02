# Local OPERA documentation map

Use this map to select evidence before generating OPERA-specific commands. The source corpus used to prepare this skill documented OPERA 2025 SP1 (November 2024). It is not redistributed here. When a user has lawful local copies, refer to the root as `<OPERA_DOCS>` or set an `OPERA_DOCS` environment variable. Consult the matching installed release and its Examples folder when they differ.

## 2D

| Source | Scope | Use for |
| --- | --- | --- |
| `opera2D_comi\ref-2d-comi-1\full.md` | COMI manual: command-language syntax, values/expressions, text functions, conditionals, loops, variables/functions, input files/dialogs, file I/O and external programs; start of pre/post commands | COMI grammar and programmable 2D workflows |
| `opera2D_comi\ref-2d-comi-2\full.md` | Continuation of 2D pre/post commands, including region manipulation, field points, plotting and solve command | Exact 2D pre/post command parameters |
| `opera2D_ref\ref-2d-1\full.md` | 2D GUI, Python console/export/script workflow, Machines Designer, worked examples | Exported Python and 2D scripting workflow |
| `opera2D_ref\ref-2d-2\full.md` | Continuation: analysis programs and additional features, including materials/loss methods | 2D solver/model options and material analysis |

## 3D reference manual

| Source | Scope | Use for |
| --- | --- | --- |
| `opera3D_ref\ref-3d-part1\full.md` | System overview; full command-language foundation; geometric modeller; start of conductors, analysis, post-processing, Python contents | Solver selection, COMI language, geometry foundations |
| `opera3D_ref\ref-3d-part2\full.md` | Continuation of modeller commands; conductors; analysis-program material | Exact geometry/conductor and solver setup commands |
| `opera3D_ref\ref-3d-part3\full.md` | Post-processor continuation | Field evaluation, plots, data export and post-processing commands |
| `opera3D_ref\ref-3d-part4\full.md` | Python and OPERA | `operafea` interface, database access/update, callbacks and Python patterns |

## 3D user guide

| Source | Scope | Use for |
| --- | --- | --- |
| `opera3D_userguide\user-3d-1\full.md` | Introduction, getting started, modeller features; electrostatic, transient EM, machine, winding, induction heating, quench, particle, HF, stress, application-note and Python-package contents | End-to-end examples and physics-specific starting points |
| `opera3D_userguide\user-3d-2\full.md` | Continuation of worked examples | Example setup and solver control patterns |
| `opera3D_userguide\user-3d-3\full.md` | Stress, application notes and Python applications | Multiphysics/application-note patterns |
| `opera3D_userguide\user-3d-4\full.md` | Motion control, Python applications, coupled EM–thermal examples, supplied Python functionality | `control_carmen.comi`, solver hooks, loss evaluation, coupling |

## Search workflow

Search the corpus narrowly, retaining line numbers for review. Examples in the converted Markdown can contain OCR/transcoding errors, so compare all executable lines with the actual OPERA help/Examples of the installed release.

```powershell
$docs = $env:OPERA_DOCS
if (-not $docs) { throw 'Set OPERA_DOCS to your lawful local documentation corpus.' }
Select-String -Path "$docs\opera3D_ref\ref-3d-part4\full.md" `
  -Pattern 'registerHookCallback|currentSimulation|PYTHON FILE' -Encoding UTF8
```

Use the 3D user-guide examples to understand workflow intent, and use the 3D reference manual to verify command/API details. For 2D, use the COMI reference for command syntax and the 2D reference manual for Python/UI behaviour.

## Transient-loss evidence map

The transient-loss reference was built after an inventory and keyword audit of all 12 converted manuals listed above: four OPERA-2d volumes, four OPERA-3d reference volumes, and four OPERA-3d user-guide volumes. The audit searched every volume for Joule/ohmic, eddy-current, hysteresis/core/iron, `JHD`, `LOSS`, `POWER`, thermal/heat, `ELEKTRATR`, `TEMPOTR`, Motional EM, and Quench terms. The executable and semantic claims retained in [transient losses and electromagnetic-thermal heat sources](transient-losses.md) come from the following source sections and were cross-checked against the installed CST Studio Suite 2025 OPERA package where possible:

| Question | Primary manual evidence |
| --- | --- |
| Per-material transient power/energy and hysteresis variables | `opera3D_ref\ref-3d-part3\full.md:1950-1967` |
| `J`, `JM`, `HLOSS`, `SIBCLOSS`, `LOSS` semantics | `opera3D_ref\ref-3d-part3\full.md:2424-2460` |
| `JHD`, `LOSS`, and default thermal data transfer | `opera3D_ref\ref-3d-part2\full.md:1140-1150` |
| `ENERGY` integration, `POWER`, `HYSPOWER`, and symmetry | `opera3D_ref\ref-3d-part3\full.md:3791-3831` |
| 3D transient hysteresis and the stored-energy caveat | `opera3D_userguide\user-3d-3\full.md:2195-2269` |
| Bulk-conductor pulsed magnet and loss extraction | `opera3D_userguide\user-3d-3\full.md:3263-3358` |
| Periodic Fourier/Steinmetz/Bertotti iron loss | `opera3D_userguide\user-3d-4\full.md:764-981` |
| Supplied time-average loss package | `opera3D_userguide\user-3d-4\full.md:2507-2539` |
| Transient-thermal equation and heat-table association | `opera3D_ref\ref-3d-part3\full.md:1037-1083` |
| 3D periodic EM-to-thermal worked case | `opera3D_userguide\user-3d-4\full.md:2053-2094` |
| 2D transient hysteresis and eddy-loss integration | `opera2D_ref\ref-2d-2\full.md:108-177` |
| 2D motional/thermal loss workflow | `opera2D_ref\ref-2d-1\full.md:4026-4270` |

Installed-release checks used `<CST_INSTALL>\Examples\Opera` and `<CST_INSTALL>\Opera\code\bin\Lib\site-packages\OperaLossCalculation`. In particular, the supplied `3D\Multiphysics\Coupled_EMTR_THST_Racetrack` example distinguishes element-associated time-averaged `JHD`, node-associated `J·E`, node-associated iron-loss fields, and the cumulative `RNODALHEAT` / `RELEMENTHEAT` fields. Example files can age or contain inconsistencies, so use them to verify the installed API and field naming, then validate the generated database fields instead of copying an old example blindly.

## Corpus-derived cautions

- The 3D guide describes `solver.comi` as an initialization script for importing Python and registering solve callbacks; it distinguishes per-step callbacks from output-time callbacks.
- The guide describes transient control files that are discovered in the working directory, including `control_carmen.comi` for Motional EM. Do not reuse that filename for a different solver without checking its solver documentation.
- The guide describes automatic post-processing COMI in coupled examples. Keep transferred quantities named, versioned, and validated.
- The conversion visibly corrupts some symbols and occasional module/function spelling. Treat it as a searchable research corpus, not an executable source of truth.
