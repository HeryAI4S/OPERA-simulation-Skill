#!/usr/bin/env python3
"""Initialize a new unsolved OPERA project without modifying existing models."""
import argparse
import json
from pathlib import Path


def create_project(target, name, solver):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    for folder in ('source', 'scripts', 'cases', 'results'):
        (target / folder).mkdir()
    contract = dict(name=name, status='NOT_SOLVED', solver=solver,
                    opera_version=None, units=None, coordinates=None, symmetry=None,
                    source_model=None, materials=[], observables=[],
                    requested_threads=None, maximum_concurrent_jobs=1,
                    time_step_s=None, output_times_s=[],
                    acceptance_checks=['solver completion', 'saved database reload',
                                       'units and material audit', 'independent physical check'])
    (target / 'project.json').write_text(json.dumps(contract, indent=2), encoding='utf-8')
    (target / 'README.md').write_text(
        '# ' + name + '\n\nStatus: NOT_SOLVED. No geometry, mesh or solution generated.\n\n'
        'Complete project.json from actual model requirements before building or solving.\n'
        'Preserve originals in source/; put generated cases in cases/ and evidence in results/.\n'
        'Check the installed release help before writing executable COMI.\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path)
    parser.add_argument('--name', required=True)
    parser.add_argument('--solver', required=True, help='Installed-release solver identifier, e.g. ELEKTRATR.')
    args = parser.parse_args()
    create_project(args.target, args.name, args.solver)
    print(args.target.resolve())


if __name__ == '__main__':
    main()
