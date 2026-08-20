"""Rolls-Royce Engine Performance Cycle Deck — command line demo.

Runs the pyCycle high-bypass turbofan deck (NASA / OpenMDAO example physics)
over a small flight-envelope sweep and renders Rolls-Royce branded output:
a blue-header cycle summary table in the terminal and branded plots on disk.

    python -m rr_demo.run_demo
"""

import argparse
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from rr_demo import branding  # noqa: E402
from rr_demo.cycle_deck import (DEFAULT_SWEEP, DESIGN_ALT, DESIGN_MN,  # noqa: E402
                                build_deck, collect, run_sweep)

SUMMARY_HEADERS = ['  POINT', 'MACH', 'ALT (ft)', 'W (lbm/s)', 'Fn (lbf)',
                   'OPR', 'TSFC', 'BPR', 'T4 (R)']


def summary_row(label, res):
    return [f'  {label}', f"{res['MN']:.3f}", f"{res['alt_ft']:,.0f}",
            f"{res['W_lbm_s']:.1f}", f"{res['Fn_lbf']:,.0f}",
            f"{res['OPR']:.2f}", f"{res['TSFC']:.4f}",
            f"{res['BPR']:.3f}", f"{res['T4_degR']:,.0f}"]


def print_summary(design, sweep):
    rows = [summary_row('Design (cruise)', design)]
    rows += [summary_row(f'Off-design {i + 1}', r) for i, r in enumerate(sweep)]
    print()
    print(branding.BLUE_TEXT + '  Cycle summary' + branding.RESET)
    print(branding.blue_table(SUMMARY_HEADERS, rows))
    print()


def plot_sweep(sweep, design, out_path, throttle=1.0):
    branding.apply_matplotlib_theme()
    fig, axes = branding.new_branded_figure(
        'Rolls-Royce Engine Performance Cycle Deck',
        f'High-bypass turbofan — flight envelope sweep at {throttle:.0%} throttle',
        nrows=2, ncols=2, figsize=(11, 7.5))

    mach = [r['MN'] for r in sweep]
    series = [
        ('Net thrust', 'Fn_lbf', 'Fn (lbf)'),
        ('Thrust specific fuel consumption', 'TSFC', 'TSFC (lbm/hr/lbf)'),
        ('Overall pressure ratio', 'OPR', 'OPR (-)'),
        ('Turbine entry temperature', 'T4_degR', 'T4 (degR)'),
    ]

    for idx, (ax, (title, key, ylabel)) in enumerate(zip(axes.ravel(), series)):
        ax.plot(mach, [r[key] for r in sweep], marker='o', color=branding.RR_BLUE,
                label='Off-design sweep')
        ax.scatter([design['MN']], [design[key]], color=branding.RR_BLUE_LIGHT,
                   zorder=5, s=70, marker='D', label='Design point')
        ax.set_title(title)
        ax.set_xlabel('Flight Mach number')
        ax.set_ylabel(ylabel)
        ax.ticklabel_format(axis='y', useOffset=False, style='plain')
        if idx == 0:
            ax.legend(loc='best', fontsize=8)

    fig.subplots_adjust(left=0.08, right=0.97, top=0.82, bottom=0.09,
                        hspace=0.45, wspace=0.25)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


def plot_summary_table(design, sweep, out_path):
    branding.apply_matplotlib_theme()
    headers = [h.strip() for h in SUMMARY_HEADERS]
    rows = [summary_row('Design (cruise)', design)]
    rows += [summary_row(f'Off-design {i + 1}', r) for i, r in enumerate(sweep)]

    fig = plt.figure(figsize=(11, 1.5 + 0.42 * (len(rows) + 1)))
    branding.brand_figure(fig, 'Rolls-Royce Engine Performance Cycle Deck',
                          'Cycle summary — high-bypass turbofan')
    ax = fig.add_axes([0.04, 0.08, 0.92, 0.72])
    ax.axis('off')

    cells = [[c.strip() for c in row] for row in rows]

    table = ax.table(cellText=cells, colLabels=headers, cellLoc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor(branding.RR_BORDER)
        if row == 0:
            cell.set_facecolor(branding.RR_BLUE)
            cell.set_text_props(color=branding.RR_WHITE, fontweight='bold')
        elif row % 2 == 0:
            cell.set_facecolor(branding.RR_GREY)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=branding.PRODUCT_NAME)
    parser.add_argument('--thermo', default='TABULAR', choices=['TABULAR', 'CEA'],
                        help='thermodynamic package (TABULAR is ~3x faster)')
    parser.add_argument('--throttle', type=float, default=0.9,
                        help='part-power throttle setting, fraction of max thrust')
    parser.add_argument('--points', type=int, default=len(DEFAULT_SWEEP),
                        help='number of flight-envelope points to run')
    args = parser.parse_args(argv)

    print(branding.cli_banner())
    start = time.time()

    print(branding.BLUE_TEXT + '\n  Building the cycle deck…' + branding.RESET)
    prob = build_deck(thermo_method=args.thermo)

    print(branding.BLUE_TEXT +
          f'  Solving design point (Mach {DESIGN_MN}, {DESIGN_ALT:,.0f} ft)…' + branding.RESET)
    prob['OD_part_pwr.PC'] = args.throttle
    prob.run_model()
    design = collect(prob, 'DESIGN')

    def progress(MN, alt):
        print(branding.BLUE_TEXT + f'  Solving off-design Mach {MN}, {alt:,.0f} ft…' + branding.RESET)

    sweep = run_sweep(prob, DEFAULT_SWEEP[:args.points], PC=args.throttle, progress=progress)

    print_summary(design, sweep)

    out_dir = branding.OUTPUT_DIR
    table_png = plot_summary_table(design, sweep, out_dir / 'rr_cycle_summary.png')
    sweep_png = plot_sweep(sweep, design, out_dir / 'rr_flight_envelope.png', args.throttle)

    total = time.time() - start
    print(branding.BLUE_TEXT + '  Branded output written to:' + branding.RESET)
    print(f'    {table_png}')
    print(f'    {sweep_png}')
    print(branding.BLUE_TEXT + f'  Total runtime: {total:.1f} s ({args.thermo} thermodynamics)'
          + branding.RESET)
    print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
