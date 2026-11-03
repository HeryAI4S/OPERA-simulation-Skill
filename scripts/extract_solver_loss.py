#!/usr/bin/env python3
"""Integrate a completed single-run OPERA transient solver loss log (stdlib only)."""
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

NUMBER = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?'


def number(value):
    return float(value.replace('D', 'E').replace('d', 'e'))


def parse_loss(text, initial_power=None):
    if len(re.findall(r'Opera[^\n]*complete on', text)) != 1:
        raise ValueError('Require one completed run; reject incomplete/concatenated logs.')
    if re.search(r'(?i)fatal|aborted|terminated abnormally', text):
        raise ValueError('Fatal/aborted status in log.')
    if initial_power is None or not math.isfinite(initial_power) or initial_power < 0:
        raise ValueError('Supply finite nonnegative --initial-power after checking initial state.')
    points = []
    pending = None
    for line in text.splitlines():
        m = re.search(r'Performing full step from\s+('+NUMBER+r')\s+to\s+('+NUMBER+')', line)
        if m:
            if pending is not None:
                raise ValueError('Step missing loss output; adaptive/retried steps need native review.')
            a, b = map(number, m.groups())
            if not points:
                points.append((a, initial_power))
            if not b > a or not math.isclose(a, points[-1][0], abs_tol=1e-9, rel_tol=1e-9):
                raise ValueError('Nonmonotonic, duplicate or missing time step.')
            pending = b
        m = re.search(r'Ohm Loss in meshed volume\s*=\s*('+NUMBER+r')\s*\[W\]', line)
        if m:
            p = number(m[1])
            if pending is None or not math.isfinite(p) or p < 0:
                raise ValueError('Unmatched, nonfinite or negative loss power.')
            points.append((pending, p))
            pending = None
    if pending is not None or len(points) < 2:
        raise ValueError('Missing power history or final step power.')
    saved = re.findall(r'saved with solution at time\s+('+NUMBER+')', text)
    if not saved or not math.isclose(number(saved[-1]), points[-1][0], abs_tol=1e-9):
        raise ValueError('Final stored result and power history do not match.')
    cumulative = [0.0]
    for (t0, p0), (t1, p1) in zip(points, points[1:]):
        cumulative.append(cumulative[-1] + (t1-t0)*(p0+p1)/2)
    threads = re.search(r'Number of threads\s*=\s*(\d+)', text)
    residuals = [number(x) for x in re.findall(r'Convergence indicator \(Residual\):\s*('+NUMBER+')', text)]
    peak = max(points, key=lambda x: x[1])
    return dict(status='COMPLETED_LOG_POSTPROCESSED', points=points,
                cumulative_energy_J=cumulative, energy_J=cumulative[-1],
                start_s=points[0][0], end_s=points[-1][0],
                mean_power_W=cumulative[-1]/(points[-1][0]-points[0][0]),
                sampled_peak_power_W=peak[1], sampled_peak_time_s=peak[0],
                initial_power_source='user_supplied',
                threads=int(threads[1]) if threads else None,
                slow_convergence_warnings=text.count('Converge too slow'),
                max_final_nonlinear_residual=max(residuals) if residuals else None,
                warnings=list(dict.fromkeys(line.strip() for line in text.splitlines()
                                             if 'warning' in line.lower() or 'did not converge' in line.lower())),
                quantity='Ohm Loss in meshed volume [W]',
                scope='Native mesh-volume total, no additional symmetry multiplier; not whole-magnet loss.',
                validation='Log extraction and quadrature only; no native database reload, mesh or time-step convergence.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--initial-power', type=float, required=True, help='Initial W, verified by caller; never silently assumed zero.')
    parser.add_argument('--out', type=Path, required=True, help='New output directory; existing paths are refused.')
    args = parser.parse_args()
    raw = args.log.read_bytes()
    result = parse_loss(raw.decode('utf-8', errors='replace'), args.initial_power)
    result['source_log'] = str(args.log.resolve())
    result['source_sha256'] = hashlib.sha256(raw).hexdigest()
    if args.log.read_bytes() != raw:
        raise ValueError('Log changed during extraction.')
    args.out.mkdir(parents=True, exist_ok=False)
    with (args.out / 'loss_history.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['time_s', 'mesh_ohmic_power_W', 'cumulative_energy_J', 'power_source'])
        for i, ((t, p), e) in enumerate(zip(result['points'], result['cumulative_energy_J'])):
            writer.writerow([t, p, e, 'user_supplied' if i == 0 else 'native_solver_log'])
    (args.out / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('points', 'cumulative_energy_J')}, indent=2))


if __name__ == '__main__':
    main()
