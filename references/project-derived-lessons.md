# Project-derived OPERA workflow lessons

This is a reusable synthesis of a transient dipole/dewar/shield project reviewed in November 2026 using OPERA 2025 SP1. It records methods and corrected interpretations, without distributing user models, raw result databases, vendor macros or private machine paths. Numerical design results remain in the originating project.

## What the project established

| Work performed | Reusable capability | Evidence boundary |
| --- | --- | --- |
| Completed transient solver-log loss extraction | Integrate accepted-step mesh-volume power, keep input hashes and runtime warnings | Log extraction does not establish native result reload or convergence |
| Native material-labelled Post integration across saved times | Partition J dot E into yoke, aluminium, stainless and air contributions and close against the total | A consistent material sum is an accounting check on the represented domain |
| Geometry/activation/volume audit | Correct an octant mesh total into a conditional complete-magnet estimate | Equal physical copies and no previous expansion must be established independently |
| Conductivity interventions and material changes | Compare shielding response, material losses and absolute integrated field | The changed whole-system total is not direct component loss or a mesh convergence test |
| Native integrated Br harmonics at explicit saved cases | Compare raw main field, signed relative terms and absolute units at matched states | Main normalization to 10000 hides absolute-field changes |
| Reflection correction and angle/longitudinal/radius checks | Diagnose missing vector symmetry, post quadrature sensitivity and high-order numerical floors | Sampling stability does not certify the underlying field mesh or engineering field quality |

## Corrections worth preserving

1. A database/log reporting no active symmetry can still contain only one physical octant. Material/solver agreement did not reveal the missing whole-magnet factor. Check physical geometry and integration volume separately from activation metadata.
2. A full-circle cylindrical field integral needs the correct component reflection signs. A template's assumption that full symmetry is already active is an input requirement that must be tested.
3. A numeric COMI export must be checked as data. One identity stream printed literal `TTIME` because of its format descriptor sequence. Case inventory and native load evidence were needed to recover the comparison's time identity.
4. Turning off aluminium/stainless conductivity left yoke eddy loss and changed the rest of the solution. Total subtraction could not stand in for direct aluminium/stainless loss integration.
5. Changing anisotropic yoke conductivity changed yoke loss. Preserve tensor components, units and material provenance; numerical model consistency is not material qualification.
6. A normally completed solve, zero activation status and small final nonlinear residual coexisted with linear-solver warnings and appreciable J-field error estimates. Report these separately and require actual mesh/time-step checks before acceptance.
7. A ramp plus hold did not include a down-ramp or a complete repetition period. Its mean power was an interval statistic, not a complete-cycle cryogenic load.
8. A completed run printed a trial endpoint loss before rolling back to a smaller step. The strict single-pass solver-log helper correctly rejected it. Saved native states remained usable for a declared saved-state quadrature; discarded trial powers could not be included in an accepted all-step history. Preserve the retry records and use native case/save evidence rather than deleting them to satisfy the parser.

## Reusable workflow

Start with the [runtime evidence audit](project-and-runtime-evidence.md), use the [native material and domain workflow](native-loss-and-symmetry-audit.md) for per-material loss, and use [integrated-harmonic diagnostics](integrated-harmonic-diagnostics.md) for field quality. Retain the source identity, actual case/time, unscaled outputs, temporary symmetry settings, numeric tables and limitations with each result.

Review the latest run status before reuse. A terminated or still-running case does not inherit an earlier model's completion or numerical acceptance. The skill update itself requires no solver rerun and does not alter the originating model.
