"""Rolls-Royce visual identity helpers for the cycle-deck demo.

Colours and layout follow the public Rolls-Royce brand palette used on
rolls-royce.com. The upstream pyCycle library (NASA / OpenMDAO) is unmodified
by this module; it only styles the presentation layer.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

RR_BLUE = '#10069F'
RR_BLUE_LIGHT = '#4B3FD1'
RR_BLUE_PALE = '#8C86E0'
RR_WHITE = '#FFFFFF'
RR_BLACK = '#111111'
RR_GREY = '#F2F2F4'
RR_BORDER = '#E5E5EA'

SERIES_COLORS = [RR_BLUE, RR_BLUE_LIGHT, RR_BLUE_PALE, '#5A5A6E', RR_BLACK]

PRODUCT_NAME = 'Rolls-Royce Engine Performance Cycle Deck'
PRODUCT_SHORT = 'Rolls-Royce Cycle Deck'

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = REPO_ROOT / 'docs' / 'assets' / 'rolls-royce-logo.png'
OUTPUT_DIR = Path(__file__).resolve().parent / 'outputs'


def apply_matplotlib_theme():
    """Apply the Rolls-Royce plot theme to the global matplotlib rcParams."""
    mpl.rcParams.update({
        'figure.facecolor': RR_WHITE,
        'axes.facecolor': RR_WHITE,
        'axes.edgecolor': RR_BORDER,
        'axes.labelcolor': RR_BLACK,
        'axes.titlecolor': RR_BLUE,
        'axes.titlesize': 13,
        'axes.titleweight': 'bold',
        'axes.titlelocation': 'left',
        'axes.grid': True,
        'axes.prop_cycle': mpl.cycler(color=SERIES_COLORS),
        'grid.color': RR_BORDER,
        'grid.linewidth': 0.8,
        'text.color': RR_BLACK,
        'xtick.color': RR_BLACK,
        'ytick.color': RR_BLACK,
        'font.family': 'sans-serif',
        'font.sans-serif': ['DejaVu Sans', 'Inter', 'Montserrat', 'Arial'],
        'legend.frameon': False,
        'lines.linewidth': 2.2,
        'lines.markersize': 6,
        'figure.dpi': 120,
    })


def brand_figure(fig, title, subtitle=''):
    """Add the Rolls-Royce header bar, wordmark and badge logo to a figure."""
    fig.subplots_adjust(top=0.82)
    header = fig.add_axes([0, 0.9, 1, 0.1])
    header.set_facecolor(RR_BLUE)
    header.set_xticks([])
    header.set_yticks([])
    for spine in header.spines.values():
        spine.set_visible(False)

    header.text(0.075, 0.62, title, color=RR_WHITE, fontsize=13, fontweight='bold',
                va='center', ha='left', transform=header.transAxes)
    if subtitle:
        header.text(0.075, 0.22, subtitle, color=RR_WHITE, fontsize=9,
                    va='center', ha='left', alpha=0.85, transform=header.transAxes)

    if LOGO_PATH.exists():
        logo_ax = fig.add_axes([0.012, 0.902, 0.055, 0.096])
        logo_ax.imshow(mpimg.imread(str(LOGO_PATH)))
        logo_ax.axis('off')

    fig.text(0.99, 0.012, 'Rolls-Royce  |  built on NASA/OpenMDAO pyCycle',
             color=RR_BLUE, fontsize=7, ha='right', va='bottom', alpha=0.75)
    return fig


def new_branded_figure(title, subtitle='', nrows=1, ncols=1, figsize=(10, 6)):
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    brand_figure(fig, title, subtitle)
    return fig, axes


# --- terminal branding ------------------------------------------------------

def _rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _bg(hex_color):
    r, g, b = _rgb(hex_color)
    return f'\033[48;2;{r};{g};{b}m'


def _fg(hex_color):
    r, g, b = _rgb(hex_color)
    return f'\033[38;2;{r};{g};{b}m'


RESET = '\033[0m'
BOLD = '\033[1m'
BLUE_BAR = _bg(RR_BLUE) + _fg(RR_WHITE) + BOLD
BLUE_TEXT = _fg(RR_BLUE) + BOLD

LOGO_ASCII = [
    '  ____  ____  ',
    ' |  _ \\|  _ \\ ',
    ' | |_) | |_) |',
    ' |  _ <|  _ < ',
    ' |_| \\_\\_| \\_\\',
]


def cli_banner(subtitle='High-bypass turbofan cycle deck'):
    """Return the Rolls-Royce CLI banner as a string."""
    width = 78
    lines = [BLUE_BAR + ' ' * width + RESET]
    body = [
        f'  {PRODUCT_NAME}',
        f'  {subtitle}',
    ]
    for i, logo_line in enumerate(LOGO_ASCII):
        text = body[i - 1] if 0 < i <= len(body) else ''
        content = f' {logo_line}   {text}'
        lines.append(BLUE_BAR + content.ljust(width)[:width] + RESET)
    lines.append(BLUE_BAR + ' ' * width + RESET)
    lines.append(_fg(RR_BLUE) + '─' * width + RESET)
    lines.append(_fg(RR_BLACK) + '  Powered by pyCycle (NASA / OpenMDAO) — upstream physics unmodified.' + RESET)
    return '\n'.join(lines)


def blue_table(headers, rows, col_widths=None):
    """Render a table with a Rolls-Royce blue header row for the terminal."""
    if col_widths is None:
        col_widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) + 2
                      if rows else len(str(h)) + 2
                      for i, h in enumerate(headers)]

    header_line = ''.join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    out = [BLUE_BAR + header_line + RESET]
    for idx, row in enumerate(rows):
        line = ''.join(str(c).ljust(w) for c, w in zip(row, col_widths))
        colour = _fg(RR_BLACK) if idx % 2 == 0 else _fg(RR_BLUE)
        out.append(colour + line + RESET)
    return '\n'.join(out)
