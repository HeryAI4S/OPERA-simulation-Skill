# Transient losses and electromagnetic-thermal heat sources

Use this reference to decide whether an OPERA-2d or OPERA-3d model can answer a transient-loss question, select the correct loss representation, integrate power into energy, and transfer the heat source to a thermal analysis. It covers single pulses, arbitrary nonperiodic waveforms, repetitive steady cycles, meshed conductors, eddy-current regions, transient hysteresis, frequency-domain iron-loss models, surface-impedance loss, and EM-to-thermal coupling.

The core answer is **yes: OPERA supports transient-loss calculation**, but there is no single universal “transient loss” result. The valid solver, material model, result field, spatial association, time interpretation, and integration route depend on the physical loss mechanism. A converged transient field solution is not by itself a validated loss or temperature result.

## Contents

1. [Choose the loss question before the solver](#choose-the-loss-question-before-the-solver)
2. [Represent conductors and materials correctly](#represent-conductors-and-materials-correctly)
3. [Know the 3D result variables](#know-the-3d-result-variables)
4. [Integrate power and energy](#integrate-power-and-energy)
5. [Treat transient hysteresis separately](#treat-transient-hysteresis-separately)
6. [Separate a single pulse from periodic iron loss](#separate-a-single-pulse-from-periodic-iron-loss)
7. [Transfer loss to thermal analysis](#transfer-loss-to-thermal-analysis)
8. [Apply the 2D-specific rules](#apply-the-2d-specific-rules)
9. [Use energy balance and convergence gates](#use-energy-balance-and-convergence-gates)
10. [Build an auditable result package](#build-an-auditable-result-package)
11. [Source and installed-example map](#source-and-installed-example-map)

## Choose the loss question before the solver

| Physical question | OPERA route | Result interpretation | Do not substitute |
| --- | --- | --- | --- |
| Joule loss in a circuit-connected, volume-meshed conductor during a pulse | 3D Transient EM (`ELEKTRATR`) or applicable Quench/Motional/Magnetization solve | `JH_<name>` is instantaneous power; `EJ_<name>` is accumulated Joule energy; `JHD` is an element-associated Joule heat density where provided | A Biot-Savart-only coil or peak `I²R` multiplied by pulse width |
| Eddy-current loss in a conductive plate, shield, vessel, yoke, or bulk conductor | 3D `ELEKTRATR` or Motional EM with conductive meshed volumes | `LOSS = J·E`; integrate selected volumes with `ENERGY` to obtain `POWER`, or use a verified loss-density field | A sequence of `TOSCAMAGN` static cases |
| Transient magnetic hysteresis for an arbitrary waveform | Nonlinear Transient EM, Motional EM, or Magnetization with a hysteretic material trajectory | `HLOSS` is accumulated stored-plus-dissipated energy density since the transient start; `HLOSS_<name>` is the per-material accumulated result | Harmonic complex-permeability `HYSPOWER` or a generic Steinmetz cycle average |
| Periodic steady-state core/iron loss | Run a transient/motional model until periodic steady state, sample one complete cycle, then use `OperaLossCalculation` or the documented iron-loss scripts | Time-averaged loss density from Fourier/Steinmetz, quadratic, Bertotti, IEM, or measured loss data | A single nonperiodic pulse unless a defensible periodic equivalent is explicitly defined |
| Steady-state AC loss represented by complex permeability | Harmonic EM | `HYSPOWER` is additional time-average power from hysteretic complex permeability | Transient `HLOSS` |
| Surface-impedance conductor loss | Harmonic, Transient, or Motional EM where SIBC is supported | `SIBCLOSS` is SIBC power-loss density; `ISSIBC` identifies SIBC elements | A volume-conductor `J·E` integral without checking the boundary representation |
| Temperature rise from electromagnetic loss | Static Thermal or `TEMPOTR`, one-way or weakly coupled to EM | Node- or element-associated heat-source density with an explicit time/averaging contract | A total scalar energy entered as though it were a spatial heat-density field |
| Mechanical braking/power balance in Motional EM | Motional EM plus torque/speed or force/velocity history | Compare `T·ω` or `F·v` with electrical and magnetic loss/energy balance | An assumption that OPERA automatically models bearings, windage, or friction not present in the model |

Use `ELEKTRATR` for a real pulse when conductive shielding, current redistribution, eddy-current lag, or circuit dynamics matter. A magnetostatic current scan may remain useful as a low-frequency or peak-field baseline, but it cannot produce the causal current-density history or transient energy loss.

## Represent conductors and materials correctly

### Conductor gate

Distinguish these two representations before asking for loss:

- A mesh-independent Biot-Savart conductor is a source representation. It does not resolve eddy currents or current redistribution inside the winding body.
- A circuit-connected bulk/volume-meshed conductor can resolve the electric field, current distribution, impedance variation, local Joule heating, and coupling to a transient circuit.

If winding skin/proximity effect or local hot spots matter, model the relevant winding as a conductive meshed region with terminals/circuit connectivity. If only an imposed source current and external-field response matter, a Biot-Savart source may be appropriate, but it cannot support a claim about internal transient winding loss.

### Material gate

For every lossy volume record:

1. material and volume labels;
2. conductivity and its unit, anisotropy, and temperature dependence;
3. whether the material uses nonlinear anhysteretic B-H, trajectory-following hysteresis, complex permeability, lamination/effective properties, SIBC, or a fitted iron-loss law;
4. whether the region is electrically connected, isolated, laminated, or split by thin gaps;
5. the model fraction and all reflection/rotation symmetries;
6. node- or element-association of every imported or generated loss field.

A laminated yoke declared nonconducting cannot produce resolved lamination eddy currents. A homogenized iron-loss model and a resolved conductive-lamination model answer different questions; document which approximation is used.

## Know the 3D result variables

### Direct scalar and field results

| Result | Meaning | Time semantics | Association/symmetry caution |
| --- | --- | --- | --- |
| `R_<name>` | Wire resistance for a material-labelled meshed conductor | Current output time/state | Manual states this includes the complete model including symmetry |
| `QV_<name>` | Quenched/resistive volume where wire properties apply | Current output time/state | Volume is for the finite-element mesh fraction |
| `JH_<name>` | Joule heat power for the named meshed conductor/material | Instantaneous power at the current transient state | Power is for the finite-element mesh fraction; restore symmetry deliberately |
| `EJ_<name>` | Joule heat energy for the named meshed conductor/material | Accumulated energy; use a difference between two times for an interval | Energy is for the finite-element mesh fraction |
| `ET_<name>` | Stored thermal energy | State/cumulative thermal quantity, solver-dependent | Available for Quench/Transient Thermal contexts described by the manual |
| `JHD` / database `RJHD` | Joule heat density associated with conductor `I²R` loss | Instantaneous in a transient result; supplied utility can time-average it | Installed `OperaJHDLossCalculator` treats `RJHD` as element-associated |
| `J` | Current density including eddy currents and current in meshed conductors | Current transient state; harmonic results use harmonic conventions | Vector field; do not infer loss from magnitude alone without conductivity/electric field |
| `JM` | Current density in meshed conductors | Current transient state | Helps distinguish meshed-conductor current from the broader `J` result |
| `LOSS` | Power-loss density `J·E` | Instantaneous in transient/current-flow results; time-average in time-harmonic results | Confirm units and selected physical region |
| `POWER` | Volume integral of the `ENERGY` command's `J·E` integrand | Instantaneous in a transient case; harmonic evaluation depends on `TIMEOPTION` | `ENERGY` includes activated reflected/rotated copies; selection must be explicit |
| `HLOSS` | Hysteresis energy density for trajectory-following transient hysteretic material | Accumulated stored plus dissipated energy since transient start | Field quantity; interpret its difference with the stored-energy caveat below |
| `HLOSS_<name>` | Accumulated hysteresis energy for a named material | Accumulated material total | Record material name and verify model-fraction/symmetry convention in the target database |
| `SIBCLOSS` | Power-loss density in SIBC elements | Solver/time convention of the active harmonic/transient/motional result | Use `ISSIBC` and selected SIBC regions to verify support; inspect the installed database unit and documented integration measure rather than assuming surface or volume integration from the name alone |
| `HYSPOWER` | Additional hysteretic complex-permeability power | Time-average steady-state AC quantity | Not the arbitrary-transient `HLOSS` result |

The suffix `<name>` is the material label of the volume-meshed conductor and is also the conductor's circuit-element name in the documented workflow. Inspect the active database rather than assuming the label was normalized or truncated.

### Avoid double counting `JHD` and `LOSS`

The multiphysics reference defines `JHD` as conductor `I²R` heat density and `LOSS` as `J·E` heat density, including SIBC material treatment. It also states that, in a multiphysics thermal sequence, OPERA applies `JHD + LOSS` to eligible cells unless volume properties supply explicit heat.

That built-in rule does **not** justify manually adding independently integrated `JHD` and `LOSS` over the same physical label without inspection. The supplied 2025 example uses element-associated `JHD` for the racetrack conductor and node-associated `J·E` for the stainless plate, i.e. distinct mechanisms/regions. Before forming a custom total:

1. query both fields on each selected region;
2. confirm which field is defined/nonzero and how the conductor is represented;
3. preserve node/element association;
4. sum only disjoint mechanisms or a documented built-in combination;
5. compare the total with circuit input power and energy balance.

## Integrate power and energy

For a volumetric power-density field `q(x,t)`:

\[
P_\Omega(t)=\int_\Omega q(\mathbf{x},t)\,dV,
\qquad
E_\Omega[t_0,t_1]=\int_{t_0}^{t_1}P_\Omega(t)\,dt.
\]

### Preferred 3D routes

Choose the narrowest direct result that matches the question:

1. For a named meshed conductor, log `JH_<name>` and `EJ_<name>`. Check that `JH` agrees with the derivative/increment of `EJ` to within output/time-integration error.
2. For eddy-current or current-flow volumes, select labels with `ENERGY ACTION=RESET/ADD/INTEGRATE` using installed-release syntax and capture `POWER` immediately after integration.
3. For a custom density field, use `VOLUME` on explicitly selected labels and capture `INTEGRAL` immediately. Demonstrate quadrature convergence where field interpolation is material.
4. For a full pulse, integrate the sampled `P(t)` using a declared quadrature rule. A trapezoidal rule is normally transparent; refine output times around switching edges, extrema, and fast decay.
5. If `EJ_<name>` is available, use `EJ(t_1)-EJ(t_0)` as the direct interval Joule energy and compare it with the numerical integral of `JH(t)`.

Do not compute pulse energy as `P_peak × pulse_width` unless the actual power trace is constant over that interval within a declared tolerance. The correct current waveform may make Joule power proportional to `I(t)^2`; eddy-current and hysteresis components can lag, persist after switch-off, or change sign conventions in intermediate energy terms.

### Symmetry is command-dependent

The 3D reference states:

- `R_<name>` represents the complete model including symmetry;
- `JH_<name>` and `EJ_<name>` cover only the finite-element mesh fraction;
- `ENERGY` includes reflected/rotated copies specified at activation;
- a generic `VOLUME` integral excludes those copies.

Therefore, never apply one global symmetry multiplier to every reported quantity. Store a per-observable symmetry policy and test it on a hand-checkable model fraction.

Activation metadata saying no symmetry does not prove full physical coverage: geometry can still be an unexpanded octant. Material-sum/solver-total agreement establishes accounting within their common domain, not whole-magnet loss. Use the [native material and symmetry audit](native-loss-and-symmetry-audit.md) to check extents, volumes, boundaries, source replication and prior expansion before applying a scalar factor. Integrate each material directly in the same field solution; conductivity-on/off total differences include changes in other regions and are not generally the removed material's loss.

### Time sampling contract

Include the following times in the output schedule:

- pulse start and end;
- every drive/circuit discontinuity and ramp corner;
- points dense enough to resolve the shortest electrical diffusion/circuit time constant;
- the current and loss extrema;
- the post-pulse decay until the omitted tail energy is below a declared fraction of total energy.

Then halve the fixed step or tighten adaptive tolerances and compare peak power, pulse energy, and tail energy separately. Solver substeps and stored output times are not interchangeable; a converged solve can still miss a narrow loss peak if it is not stored or logged.

## Treat transient hysteresis separately

OPERA-3d's trajectory-following hysteretic material model is available with nonlinear Transient EM, Motional EM, and Magnetization analyses. The user supplies the major hysteresis loop; OPERA reconstructs minor loops and turning-point history.

At output time `t`, `HLOSS(x,t)` is documented as the sum of stored and dissipated energy density accumulated since the beginning of the transient. Thus:

\[
\frac{\int_\Omega HLOSS(t_2)\,dV-\int_\Omega HLOSS(t_1)\,dV}{t_2-t_1}
\]

contains both the change in stored magnetic energy and hysteresis dissipation. It is a pure average hysteresis-dissipation power only when the material state at the two endpoints has the same stored-energy contribution, as in a repeatable steady cycle or another explicitly verified same-state comparison.

For a single nonperiodic pulse:

- report the raw `HLOSS` change as “stored-plus-dissipated hysteretic energy change” unless stored energy has been separated;
- if claiming irreversible hysteresis loss, close an energy balance or choose endpoints with demonstrably equivalent magnetic state;
- retain the remanent state and post-pulse interval; returning current to zero does not imply returning stored magnetic energy to the initial state;
- do not replace `HLOSS` with harmonic `HYSPOWER`.

The reviewed 2025 SP1 manuals do not expose a separate direct field for instantaneous irreversible hysteresis heat density during an arbitrary single pulse. Do not invent one by differentiating raw `HLOSS` unless the stored-energy contribution has first been separated and the result has passed an energy-balance check.

## Separate a single pulse from periodic iron loss

### Single pulse or arbitrary waveform

Use the time-domain model for directly resolved conductor/structure eddy loss and, when supplied, trajectory-following `HLOSS` for magnetic hysteresis history. Steinmetz/Bertotti coefficients fitted to periodic material data do not automatically define irreversible energy for an arbitrary one-shot waveform. If an engineering approximation is required, document the equivalent-frequency/cycle assumption and keep it separate from the direct transient result.

### Repetitive steady cycle

For a periodic machine, inductor, transformer, or repeated pulse train:

1. run beyond the initial transient until a steady cycle is demonstrated;
2. select one complete electrical/excitation cycle;
3. store equally spaced outputs over that cycle;
4. use at least `2n+1` output points for a highest retained harmonic order `n`, and increase sampling for sharp PWM/commutation features;
5. label stationary and moving iron separately where rotation compensation is required;
6. apply a declared loss law and material coefficients/measurement data;
7. store the resulting time-averaged loss-density fields and integrate them over the intended volumes.

The installed `OperaLossCalculation` package supports:

- `OperaJHDLossCalculator`: time-average of element-centroid `RJHD`;
- `OperaJdotELossCalculator`: time-average of node-associated `J·E`;
- `OperaTimeAverageLossCalculator`: time-average of a generic same-association database vector;
- two-term Steinmetz, quadratic Steinmetz, and Steinmetz-Bertotti iron-loss calculators based on Fourier analysis of `B`;
- cumulative node/element heat fields and separate labelled loss fields.

The 3D guide additionally documents a five-parameter IEM formulation and user-defined measured loss tables in `W/m³` versus `B` and frequency. These postprocessed values are cycle-average power density, not arbitrary single-pulse energy density.

The generic `JHD`, `J·E`, and same-association time-average classes are numerical averaging tools and may be applied to a declared finite interval only after their sample coverage and integration behaviour are verified. Using one over a pulse interval does not make the waveform periodic, recover an omitted post-pulse tail, or turn the Fourier/Steinmetz iron-loss calculators into a valid single-pulse hysteresis model. To recover interval energy from an average power density, retain the exact interval and verify it against direct time integration.

## Transfer loss to thermal analysis

The transient thermal equation uses volumetric heat-source density `Q`:

\[
\rho C\frac{\partial T}{\partial t}-\nabla\cdot(k\nabla T)=Q.
\]

OPERA accepts expression-based heat and imported node- or element-based heat tables. For a heat table, the first three columns are node coordinates or element-centroid coordinates, and the fourth column must be named:

- `RNODALHEAT` for a node-associated heat source;
- `RELEMENTHEAT` for an element-associated heat source.

The receiving volumes must select the matching `HEATTYPE`. Do not relabel an element field as nodal, or vice versa, merely to satisfy an example script.

### One-way transient thermal workflow

Use this when temperature feedback into electrical/magnetic properties is negligible:

1. solve the complete electromagnetic pulse, including post-pulse loss tail;
2. export `q(x,t)` at energy-resolving times, or construct interval-averaged fields `q̄_k(x)` whose time integral exactly preserves the EM energy;
3. import each field with its association, units, interval, source database/case/time, mesh identity, and symmetry convention;
4. drive `TEMPOTR` over the corresponding intervals;
5. compare integrated thermal input energy with the EM loss energy.

If the thermal time constant is much longer than the pulse and only end-of-pulse temperature matters, a deposited-energy initial/source treatment may be defensible, but declare the approximation and preserve spatial energy density. A scalar total energy is insufficient to predict a local temperature field.

`TABLE`-based cross-mesh transfer is interpolation/data transfer, not an automatically conservative projection. Measure both global energy error and local hot-spot distortion; a global rescaling that restores total energy can still corrupt material-interface or skin-depth peaks.

### Weakly coupled workflow

Use this when conductivity, permeability, loss coefficients, or circuit resistance change materially with temperature:

1. solve EM for the current material state;
2. construct the node/element heat field for a declared exchange interval;
3. solve `TEMPOTR` to the next exchange time;
4. transfer temperature back to EM and update temperature-dependent properties;
5. repeat until the coupled observables converge.

The supplied periodic racetrack example calculates time-averaged conductor, plate, and iron losses after steady state and uses them for a static thermal solve. It demonstrates field association and database update mechanics; it is not a template for collapsing a nonperiodic single pulse to a cycle average.

### Heat-transfer acceptance checks

At every exchange verify:

- field name and node/element association;
- source and receiving coordinate/unit systems;
- source case/time and averaging interval;
- selected material/volume coverage and missing-value count;
- `∫q dV` before and after interpolation, including symmetry;
- `∫∫q dVdt` against `EJ` or integrated `POWER` where applicable;
- one hand-checkable point and one global integral;
- temperature-step and exchange-interval convergence.

Also verify which heat path is active. Do not let an automatic multiphysics `JHD + LOSS` source and an explicitly imported table derived from the same fields heat the same receiving volume simultaneously. Prove, in a small installed-version baseline, whether explicit volume heat/`HEATTYPE` overrides or supplements the automatic source.

## Apply the 2D-specific rules

OPERA-2d transient/motional examples support eddy-current and hysteresis-loss evaluation at output times. For an XY model:

\[
P'_E(t)=\iint_\Omega \frac{|J|^2}{\sigma}\,dA,
\]

which is power per unit axial length. Average `P'_E(t)` over the requested interval/cycle, then multiply by the declared physical axial length only when the 2D model convention requires it. Apply rotational/reflection symmetry explicitly.

For 2D trajectory hysteresis, `HLOSS` is cumulative energy density. A cycle-average hysteresis power per unit length is obtained from the difference of area-integrated `HLOSS` at same-state endpoints divided by the cycle duration. The 2D guide uses mechanical braking power as an independent balance check against hysteresis plus eddy-current power.

The 2D motional/thermal worked example defines instantaneous conductor heat density as `J²/σ`, exports it, and warns that one instantaneous case is only a demonstration: a realistic periodic thermal source should average enough output cases over a cycle. Keep 2D results labelled `W/m` or `J/m` until physical length is applied.

## Use energy balance and convergence gates

### Minimum physics checks

For a transient electrical model, compare as applicable:

\[
E_{source}
= E_{Joule}+E_{eddy}+E_{hyst,diss}
+\Delta E_{mag}+\Delta E_{electric}
+E_{mechanical}+E_{unresolved}.
\]

This balance is diagnostic, not a license to double count. Circuit `V·I`, field `POWER`, `JH`, `EJ`, `HLOSS`, stored magnetic energy, and mechanical work may overlap depending on representation. Define the accounting boundary and sign convention before summing.

### Numerical gates

Require all of the following before accepting a loss result:

1. solver completed at every required output time with no aborted/pending/unconverged case;
2. correct active database, case/time, labels, units, and field association;
3. time-step/output refinement changes peak power and interval energy below declared tolerances;
4. mesh refinement changes each important volume-integrated loss below tolerance, especially near skin-depth/thin-gap regions;
5. spatial integration/quadrature refinement is demonstrated where `VOLUME` or `ENERGY ADAPTIVE` matters;
6. symmetry is handled per observable rather than by one blanket multiplier;
7. the post-pulse tail or periodic-cycle closure is quantified;
8. circuit/field/thermal energy balance closes within a declared residual;
9. no nonfinite, missing, silently zero, or wrong-association heat fields;
10. temperature feedback is either iterated or explicitly shown negligible.

### Rejection rules

Reject a claim of “OPERA-validated transient loss” when any of these is true:

- only magnetostatic current snapshots were solved;
- a Biot-Savart-only winding is used to claim internal winding eddy loss;
- peak loss was multiplied by pulse width without validating constant power;
- transient `HLOSS` difference is called irreversible hysteresis loss without endpoint/stored-energy control;
- periodic Steinmetz/Bertotti power is presented as direct single-pulse energy;
- `SIBCLOSS` is integrated with an assumed surface or volume measure without checking the active database unit and installed-release documentation;
- node and element loss fields were interchanged;
- an automatic `JHD + LOSS` heat path and an imported table apply the same electromagnetic loss twice;
- `JHD` and `LOSS` were summed over an overlapping region without verifying semantics;
- symmetry was applied twice or omitted;
- a heat table was generated but not registered/selected and verified in the receiving thermal database;
- only script exit status or a plot is available, without solver/Post logs and numeric outputs.

## Build an auditable result package

For every transient-loss case retain:

```text
case/
  source_model.op3-or-op2
  model-build.comi
  control_elektratr.comi-or-control_carmen.comi
  solver.comi-and-hooks.py
  post-loss.comi
  loss_history.csv
  heat_fields/
    manifest.json
    heat-<time-or-interval>.table
  solver.log
  post.log
  acceptance.json
```

The loss-history schema should include at least:

```text
case_id,time,region,mechanism,observable,association,
instantaneous_power,cumulative_energy,unit,model_fraction,
symmetry_policy,mesh_id,solver_status
```

The manifest must distinguish raw instantaneous density, interval-average density, cycle-average density, cumulative energy density, and total energy. Do not use a generic column named only `loss`.

## Source and installed-example map

This reference was prepared from an inventory/keyword audit of all 12 local converted OPERA 2025 SP1 manual volumes. Exact semantic evidence came primarily from:

- `<OPERA_DOCS>\opera3D_ref\ref-3d-part2\full.md:1140-1150` — `JHD`, `LOSS`, and thermal data-transfer defaults.
- `<OPERA_DOCS>\opera3D_ref\ref-3d-part3\full.md:1950-1967` — `R_<name>`, `QV_<name>`, `JH_<name>`, `EJ_<name>`, `ET_<name>`, and `HLOSS_<name>`.
- `<OPERA_DOCS>\opera3D_ref\ref-3d-part3\full.md:2424-2460` — `J`, `JM`, `HLOSS`, `SIBCLOSS`, and `LOSS`.
- `<OPERA_DOCS>\opera3D_ref\ref-3d-part3\full.md:3791-3831` — `ENERGY`, `POWER`, `HYSPOWER`, integration, and symmetry.
- `<OPERA_DOCS>\opera3D_userguide\user-3d-3\full.md:2195-2269` — trajectory-following hysteresis and the stored-plus-dissipated interpretation of `HLOSS`.
- `<OPERA_DOCS>\opera3D_userguide\user-3d-3\full.md:3263-3358` — circuit-connected bulk conductor in a pulsed septum and `POWER` extraction.
- `<OPERA_DOCS>\opera3D_userguide\user-3d-4\full.md:764-981` — periodic iron-loss postprocessing.
- `<OPERA_DOCS>\opera3D_userguide\user-3d-4\full.md:2053-2094` and `:2507-2539` — three-mechanism coupled example and `OperaLossCalculation`.
- `<OPERA_DOCS>\opera3D_ref\ref-3d-part3\full.md:1037-1083` — transient thermal equation and `RNODALHEAT` / `RELEMENTHEAT` tables.
- `<OPERA_DOCS>\opera2D_ref\ref-2d-2\full.md:108-177` — 2D transient hysteresis/eddy-current power and symmetry.
- `<OPERA_DOCS>\opera2D_ref\ref-2d-1\full.md:4026-4270` — 2D motional heat export and periodic iron-loss workflow.

The installed CST Studio Suite 2025 OPERA release was also inspected at:

- `<CST_INSTALL>\Opera\code\bin\Lib\site-packages\OperaLossCalculation` — installed Python loss calculators and node/element heat-field generation.
- `<CST_INSTALL>\Examples\Opera\3D\Multiphysics\Coupled_EMTR_THST_Racetrack` — element `JHD`, nodal `J·E`, iron loss, `RNODALHEAT` / `RELEMENTHEAT`, and post-integration example.
- `<CST_INSTALL>\Examples\Opera\3D\Multiphysics\Coupled_EMSS_THTR` — weak EM/thermal table-transfer pattern; this older example must be revalidated before copying syntax.

Converted manual COMI lines can contain OCR/transcoding corruption. Treat the physics and variable semantics above as evidence, but verify every executable command spelling and generated database field against the installed release, its help, its current Examples folder, and a small baseline database before running a production case.
