"""Thin wrapper around pyCycle's high-bypass turbofan example.

The engine model itself is the upstream NASA / OpenMDAO example
(`example_cycles/high_bypass_turbofan.py`); this module only builds it,
sets the design point and runs off-design points, returning plain dicts
that are easy to table and plot.
"""

import sys
import time
from pathlib import Path

import openmdao.api as om

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from example_cycles.high_bypass_turbofan import MPhbtf  # noqa: E402

DESIGN_MN = 0.8
DESIGN_ALT = 35000.0

DESIGN_INPUTS = {
    'DESIGN.fan.PR': 1.685,
    'DESIGN.fan.eff': 0.8948,
    'DESIGN.lpc.PR': 1.935,
    'DESIGN.lpc.eff': 0.9243,
    'DESIGN.hpc.PR': 9.369,
    'DESIGN.hpc.eff': 0.8707,
    'DESIGN.hpt.eff': 0.8888,
    'DESIGN.lpt.eff': 0.8996,
    'DESIGN.fc.MN': DESIGN_MN,
}

INITIAL_GUESSES = {
    'DESIGN.balance.FAR': 0.025,
    'DESIGN.balance.W': 100.0,
    'DESIGN.balance.lpt_PR': 4.0,
    'DESIGN.balance.hpt_PR': 3.0,
    'DESIGN.fc.balance.Pt': 5.2,
    'DESIGN.fc.balance.Tt': 440.0,
}

OD_GUESSES = {
    'balance.FAR': 0.02467,
    'balance.W': 300.0,
    'balance.BPR': 5.105,
    'balance.lp_Nmech': 5000.0,
    'balance.hp_Nmech': 15000.0,
    'hpt.PR': 3.0,
    'lpt.PR': 4.0,
    'fan.map.RlineMap': 2.0,
    'lpc.map.RlineMap': 2.0,
    'hpc.map.RlineMap': 2.0,
}

OD_POINT = 'OD_part_pwr'


def build_deck(thermo_method='TABULAR', quiet=True):
    """Build and set up the multi-point turbofan deck.

    `TABULAR` thermodynamics is roughly 3x faster than `CEA` and is the
    default here so the demo stays interactive; pass `CEA` for the
    upstream reference answers.
    """
    prob = om.Problem(reports=False)
    prob.model = MPhbtf(thermo_method=thermo_method)
    prob.setup()

    for name, value in DESIGN_INPUTS.items():
        prob.set_val(name, value)
    prob.set_val('DESIGN.fc.alt', DESIGN_ALT, units='ft')
    prob.set_val('DESIGN.T4_MAX', 2857, units='degR')
    prob.set_val('DESIGN.Fn_DES', 5900.0, units='lbf')
    prob.set_val('OD_full_pwr.T4_MAX', 2857, units='degR')

    for name, value in INITIAL_GUESSES.items():
        prob[name] = value
    for pt in ('OD_full_pwr', OD_POINT):
        for name, value in OD_GUESSES.items():
            prob[f'{pt}.{name}'] = value

    if quiet:
        prob.set_solver_print(level=-1)
    return prob


def collect(prob, pt):
    """Pull the headline cycle results for a point out of the problem."""
    if pt == 'DESIGN':
        mach = prob['DESIGN.fc.Fl_O:stat:MN'][0]
        far = prob['DESIGN.balance.FAR'][0]
    else:
        mach = prob[f'{pt}.fc.Fl_O:stat:MN'][0]
        far = prob[f'{pt}.balance.FAR'][0]

    return {
        'point': pt,
        'MN': mach,
        'alt_ft': prob[f'{pt}.fc.alt'][0],
        'W_lbm_s': prob[f'{pt}.inlet.Fl_O:stat:W'][0],
        'Fn_lbf': prob[f'{pt}.perf.Fn'][0],
        'Fg_lbf': prob[f'{pt}.perf.Fg'][0],
        'Fram_lbf': prob[f'{pt}.inlet.F_ram'][0],
        'OPR': prob[f'{pt}.perf.OPR'][0],
        'TSFC': prob[f'{pt}.perf.TSFC'][0],
        'BPR': prob[f'{pt}.splitter.BPR'][0],
        'T4_degR': prob[f'{pt}.burner.Fl_O:tot:T'][0],
        'FAR': far,
    }


def run_point(prob, MN, alt_ft, PC=1.0):
    """Run one off-design point and return its results plus wall time."""
    for pt in ('OD_full_pwr', OD_POINT):
        prob[f'{pt}.fc.MN'] = MN
        prob[f'{pt}.fc.alt'] = alt_ft
    prob[f'{OD_POINT}.PC'] = PC

    start = time.time()
    prob.run_model()
    elapsed = time.time() - start

    result = collect(prob, OD_POINT)
    result['PC'] = PC
    result['runtime_s'] = elapsed
    return result


DEFAULT_SWEEP = [
    (0.8, 35000.0),
    (0.7, 30000.0),
    (0.6, 25000.0),
    (0.5, 20000.0),
    (0.4, 10000.0),
]


def run_sweep(prob, points=None, PC=1.0, progress=None):
    """Run a list of (Mach, altitude) points at a fixed throttle setting."""
    results = []
    for MN, alt in (points or DEFAULT_SWEEP):
        if progress is not None:
            progress(MN, alt)
        results.append(run_point(prob, MN, alt, PC))
    return results
