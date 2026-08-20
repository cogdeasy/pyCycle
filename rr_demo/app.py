"""Rolls-Royce Engine Performance Cycle Deck — Streamlit dashboard.

    streamlit run rr_demo/app.py

Wraps pyCycle's high-bypass turbofan example (NASA / OpenMDAO physics) so a
Mach / altitude / throttle case can be solved interactively and shown with
Rolls-Royce branding.
"""

import base64
import sys
import threading
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rr_demo import branding  # noqa: E402
from rr_demo.cycle_deck import (DEFAULT_SWEEP, DESIGN_ALT, DESIGN_MN,  # noqa: E402
                                build_deck, collect, run_point)
from rr_demo.run_demo import plot_sweep  # noqa: E402

st.set_page_config(page_title=branding.PRODUCT_NAME,
                   page_icon=str(branding.LOGO_PATH) if branding.LOGO_PATH.exists() else None,
                   layout='wide')

CSS = f"""
<style>
  html, body, [class*="css"] {{
      font-family: Inter, Montserrat, "Helvetica Neue", Arial, sans-serif;
      color: {branding.RR_BLACK};
  }}
  .stApp {{ background-color: {branding.RR_WHITE}; }}
  .rr-nav {{
      display: flex; align-items: center; gap: 18px;
      background: {branding.RR_WHITE};
      border-bottom: 1px solid {branding.RR_BORDER};
      padding: 10px 4px 16px 4px; margin-bottom: 8px;
  }}
  .rr-nav img {{ height: 54px; }}
  .rr-nav .rr-title {{ font-size: 1.5rem; font-weight: 700; color: {branding.RR_BLUE}; }}
  .rr-nav .rr-sub {{ font-size: 0.9rem; color: #5A5A6E; }}
  .rr-hero {{
      background: {branding.RR_BLUE}; color: {branding.RR_WHITE};
      padding: 26px 30px; border-radius: 4px; margin-bottom: 22px;
  }}
  .rr-hero h1 {{ font-size: 1.6rem; font-weight: 700; margin: 0 0 6px 0; color: {branding.RR_WHITE}; }}
  .rr-hero p {{ margin: 0; opacity: 0.9; }}
  .rr-card {{
      background: {branding.RR_GREY}; border: 1px solid {branding.RR_BORDER};
      border-radius: 4px; padding: 16px 18px; height: 100%;
  }}
  .rr-card .rr-label {{ font-size: 0.75rem; letter-spacing: 0.08em;
      text-transform: uppercase; color: #5A5A6E; }}
  .rr-card .rr-value {{ font-size: 1.6rem; font-weight: 700; color: {branding.RR_BLUE}; }}
  .stButton > button {{
      background: {branding.RR_WHITE}; color: {branding.RR_BLUE};
      border: 2px solid {branding.RR_BLUE}; border-radius: 999px;
      text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700;
      padding: 0.45rem 1.6rem;
  }}
  .stButton > button:hover {{ background: {branding.RR_BLUE}; color: {branding.RR_WHITE}; }}
  section[data-testid="stSidebar"] {{ background: {branding.RR_GREY};
      border-right: 1px solid {branding.RR_BORDER}; }}
  a {{ color: {branding.RR_BLUE}; }}
  .rr-table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
  .rr-table th {{ background: {branding.RR_BLUE}; color: {branding.RR_WHITE};
      text-align: right; padding: 8px 12px; font-weight: 700; }}
  .rr-table th:first-child, .rr-table td:first-child {{ text-align: left; }}
  .rr-table td {{ padding: 8px 12px; text-align: right;
      border-bottom: 1px solid {branding.RR_BORDER}; }}
  .rr-table tr:nth-child(even) td {{ background: {branding.RR_GREY}; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def logo_data_uri():
    if not branding.LOGO_PATH.exists():
        return ''
    encoded = base64.b64encode(branding.LOGO_PATH.read_bytes()).decode()
    return f'data:image/png;base64,{encoded}'


st.markdown(
    f"""
    <div class="rr-nav">
      <img src="{logo_data_uri()}" alt="Rolls-Royce"/>
      <div>
        <div class="rr-title">Rolls-Royce Engine Performance Cycle Deck</div>
        <div class="rr-sub">High-bypass turbofan · thermodynamic cycle analysis</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True)

st.markdown(
    """
    <div class="rr-hero">
      <h1>Engine performance, from design point to flight envelope</h1>
      <p>Set the flight condition and throttle, then solve the cycle to see thrust,
      fuel burn, pressure ratio and turbine entry temperature.</p>
    </div>
    """,
    unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def get_deck(thermo_method):
    """Build the deck once per thermodynamics package.

    The OpenMDAO problem is mutated in place by every solve, so it is shared
    behind a lock: this is a single-engine demo deck, not a multi-tenant service.
    """
    prob = build_deck(thermo_method=thermo_method)
    prob.run_model()
    return prob, collect(prob, 'DESIGN'), threading.Lock()


with st.sidebar:
    st.markdown('<div class="rr-title" style="font-size:1.1rem">Flight condition</div>',
                unsafe_allow_html=True)
    mach = st.slider('Flight Mach number', 0.20, 0.85, 0.80, 0.05)
    altitude = st.slider('Altitude (ft)', 0, 40000, 35000, 1000)
    throttle = st.slider('Throttle (fraction of max thrust)', 0.70, 1.00, 0.90, 0.05)
    thermo = st.selectbox('Thermodynamics', ['TABULAR', 'CEA'], index=0,
                          help='TABULAR is roughly 3x faster; CEA gives the upstream reference answers.')
    run_case = st.button('Run cycle')
    run_env = st.button('Run flight envelope')
    st.caption('Each off-design point takes roughly 7 s (TABULAR) or 25 s (CEA).')
    st.caption('Physics: pyCycle high-bypass turbofan example — NASA / OpenMDAO.')

with st.spinner('Building the Rolls-Royce cycle deck and solving the design point…'):
    prob, design, solve_lock = get_deck(thermo)


def metric_cards(result, columns):
    cards = [
        ('Net thrust', f"{result['Fn_lbf']:,.0f} lbf"),
        ('TSFC (lbm/hr/lbf)', f"{result['TSFC']:.4f}"),
        ('Overall pressure ratio', f"{result['OPR']:.2f}"),
        ('Bypass ratio', f"{result['BPR']:.2f}"),
        ('Turbine entry temp', f"{result['T4_degR']:,.0f} °R"),
    ]
    for col, (label, value) in zip(columns, cards):
        col.markdown(f'<div class="rr-card"><div class="rr-label">{label}</div>'
                     f'<div class="rr-value">{value}</div></div>', unsafe_allow_html=True)


st.subheader(f'Design point — Mach {DESIGN_MN}, {DESIGN_ALT:,.0f} ft')
metric_cards(design, st.columns(5))

if run_case:
    with st.spinner(f'Solving Mach {mach}, {altitude:,} ft at {throttle:.0%} throttle…'):
        with solve_lock:
            result = run_point(prob, mach, altitude, throttle)
    st.session_state['case'] = result

if 'case' in st.session_state:
    result = st.session_state['case']
    st.subheader(f"Off-design case — Mach {result['MN']:.2f}, {result['alt_ft']:,.0f} ft, "
                 f"{result['PC']:.0%} throttle")
    metric_cards(result, st.columns(5))
    st.caption(f"Solved in {result['runtime_s']:.1f} s")

    table = pd.DataFrame([
        {'Point': 'Design (cruise)', **{k: design[k] for k in
                                        ('MN', 'alt_ft', 'W_lbm_s', 'Fn_lbf', 'OPR', 'TSFC', 'BPR', 'T4_degR')}},
        {'Point': 'Selected case', **{k: result[k] for k in
                                      ('MN', 'alt_ft', 'W_lbm_s', 'Fn_lbf', 'OPR', 'TSFC', 'BPR', 'T4_degR')}},
    ]).rename(columns={'MN': 'Mach', 'alt_ft': 'Alt (ft)', 'W_lbm_s': 'W (lbm/s)',
                       'Fn_lbf': 'Fn (lbf)', 'TSFC': 'TSFC', 'T4_degR': 'T4 (°R)'})
    st.markdown(table.to_html(index=False, float_format='{:,.3f}'.format,
                              classes='rr-table', border=0),
                unsafe_allow_html=True)

if run_env:
    progress = st.progress(0.0, text='Solving the flight envelope…')
    results = []
    with solve_lock:
        for i, (MN, alt) in enumerate(DEFAULT_SWEEP):
            progress.progress(i / len(DEFAULT_SWEEP), text=f'Solving Mach {MN}, {alt:,.0f} ft…')
            results.append(run_point(prob, MN, alt, throttle))
    progress.empty()
    st.session_state['sweep'] = (results, throttle)

if 'sweep' in st.session_state:
    results, sweep_throttle = st.session_state['sweep']
    st.subheader('Flight envelope sweep')
    out_path = branding.OUTPUT_DIR / 'rr_flight_envelope_app.png'
    plot_sweep(results, design, out_path, sweep_throttle)
    st.image(str(out_path), width='stretch')

st.markdown(
    f'<hr style="border-color:{branding.RR_BORDER}"/>'
    '<p style="font-size:0.8rem;color:#5A5A6E">Rolls-Royce Engine Performance Cycle Deck — '
    'demo built on <a href="https://github.com/OpenMDAO/pyCycle">pyCycle</a>, '
    '© NASA / OpenMDAO contributors. Upstream cycle physics unmodified.</p>',
    unsafe_allow_html=True)
