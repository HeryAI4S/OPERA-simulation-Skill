# OPERA Simulation Skill

[![Validate skill](https://github.com/zxcvbnm22003Hyl/OPERA-simulation-Skill/actions/workflows/validate.yml/badge.svg)](https://github.com/zxcvbnm22003Hyl/OPERA-simulation-Skill/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reusable Agent Skill for planning, scripting, automating, post-processing, and validating CST Studio Suite OPERA 2D/3D electromagnetic simulations. It includes guidance for COMI, OPERA Python/`operafea`, accelerator magnets, particle tracking, transient losses, parameter studies, and electromagnetic-thermal-motion workflows.

中文说明：这是一个面向 CST Studio Suite OPERA 2D/3D 的可复用智能体技能，覆盖 COMI、Python、磁铁建模、后处理、粒子跟踪、瞬态损耗以及电磁-热-运动耦合。仓库不包含 OPERA 软件、许可证、官方手册、厂商示例数据库或用户模型。

## Capabilities

- Select appropriate OPERA-2d/3d solvers and modelling representations.
- Design version-aware COMI and `operafea` automation.
- Build accelerator-magnet geometry, conductor, material, mesh, and analysis workflows.
- Extract fields, integrated quantities, harmonics, forces, trajectories, and beam statistics.
- Distinguish transient Joule, eddy-current, hysteresis, periodic iron, and thermal-loss paths.
- Prepare isolated parameter studies with static preflight and machine-readable result contracts.
- Reject incomplete solver/Post evidence instead of treating process exit as physical acceptance.

## Prerequisites

- A separately licensed and installed CST Studio Suite OPERA release appropriate to the model.
- Access to the matching local OPERA help and installed Examples folder for command/version verification.
- Codex or another Agent Skills-compatible runtime.
- Python 3.10 or newer for the bundled helper scripts.

The skill is documentation and automation guidance; it is not an OPERA solver and does not bypass product licensing.

## Installation

### Codex on Windows

```powershell
$skillDirectory = Join-Path $env:USERPROFILE '.codex\skills\opera-simulation'
git clone https://github.com/zxcvbnm22003Hyl/OPERA-simulation-Skill.git $skillDirectory
```

### Codex on macOS or Linux

```bash
git clone https://github.com/zxcvbnm22003Hyl/OPERA-simulation-Skill.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/opera-simulation"
```

For runtimes that discover cross-agent skills, clone to `~/.agents/skills/opera-simulation` instead. Restart or refresh the agent runtime after installation. To update an existing clone, run `git pull --ff-only` inside the installed skill directory.

## Usage

Ask the agent to use `opera-simulation`, for example:

```text
Use $opera-simulation to design an OPERA-3d ELEKTRATR workflow for a pulsed magnet,
including conductor loss, eddy-current loss, Post integration, and TEMPOTR transfer.
```

The entry point is [`SKILL.md`](SKILL.md). It routes tasks to the focused material in [`references/`](references/) and the reusable helpers in [`scripts/`](scripts/).

## Repository layout

```text
SKILL.md
agents/openai.yaml
references/                 # focused OPERA workflow and evidence references
scripts/comi_preflight.py   # static COMI safety/preparation checks
scripts/run_cases.py        # isolated case preparation and opt-in execution
tests/validate_repository.py
```

No OPERA manuals, binaries, licence files, `.op2`/`.op3` databases, trajectories, or private project artifacts are distributed here.

## Validation

Run the repository checks from the clone root:

```powershell
python -m unittest -v tests.validate_repository
python scripts\comi_preflight.py --help
python scripts\run_cases.py --help
```

The validation checks skill discovery frontmatter, required files, relative Markdown links, local anchors, Python syntax, private absolute paths, and accidental inclusion of vendor/user artifacts. CI runs the same checks on Windows and Linux.

## Documentation corpus

Some references cite sections in a locally converted OPERA 2025 SP1 documentation corpus. Those manuals are not part of this repository. If you maintain a lawful local corpus, set an `OPERA_DOCS` environment variable pointing to a directory with the documented `opera2D_comi`, `opera2D_ref`, `opera3D_ref`, and `opera3D_userguide` layout. Always compare executable COMI/API syntax with the matching installed release and Examples folder because converted text can contain OCR/transcoding defects.

## License and third-party boundary

Original content and helper scripts in this repository are licensed under the [MIT License](LICENSE). See [NOTICE.md](NOTICE.md) for third-party attribution, trademark, documentation, and redistribution boundaries.

CST, CST Studio Suite, OPERA, Opera-2d, and Opera-3d are products or trademarks of their respective owner. This community project is not affiliated with, endorsed by, or sponsored by Dassault Systèmes.

## Contributing

Keep contributions reproducible and version-aware. Do not commit proprietary manuals, product binaries, licence files, private models/results, credentials, or machine-specific absolute paths. Add or update tests whenever the public skill structure, links, scripts, or safety boundaries change.
