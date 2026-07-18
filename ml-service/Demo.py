import math

import streamlit as st

from app.parser import parse_raw_address
from app.standardizer import (
    standardize_parsed_components,
    format_canonical_address
)
from app.features import extract_features
from app.model import predict_confidence

# ──────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Address Standardization",
    layout="wide",
    initial_sidebar_state="collapsed",
)

AUTO_ACCEPT_THRESHOLD = 0.80
REVIEW_THRESHOLD = 0.50

# ──────────────────────────────────────────────────────────────────────────
# Theme
# ──────────────────────────────────────────────────────────────────────────
dark_mode = st.toggle("🌙", value=False, key="dark_mode", label_visibility="collapsed")

if dark_mode:
    THEME = dict(
        bg="#0b0e14", panel="#12151c", panel_alt="#161a23", border="#222631",
        text="#e7e9ee", subtext="#8b93a3",
        primary="#6e8bf5", success="#3ecf8e", warn="#f5a623", danger="#f25c5c",
        shadow="0 1px 2px rgba(0,0,0,0.4)",
    )
else:
    THEME = dict(
        bg="#f7f8fa", panel="#ffffff", panel_alt="#fafbfc", border="#e6e8ec",
        text="#14161a", subtext="#6b7280",
        primary="#4f5fd1", success="#0f9d58", warn="#b7791f", danger="#c0362c",
        shadow="0 1px 2px rgba(20,22,30,0.06)",
    )

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: {THEME['bg']}; color: {THEME['text']}; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    div[data-testid="stToggle"] {{ display: flex; justify-content: flex-end; }}

    /* ---- Top navbar ----------------------------------------------------- */
    .navbar {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.85rem 1.4rem;
        background: {THEME['panel']};
        border: 1px solid {THEME['border']};
        border-radius: 10px;
        margin-bottom: 1.2rem;
        box-shadow: {THEME['shadow']};
    }}
    .navbar-brand {{ font-size: 1.05rem; font-weight: 700; letter-spacing: -0.01em; }}
    .navbar-tabs {{ display: flex; gap: 1.4rem; font-size: 0.85rem; color: {THEME['subtext']}; }}
    .navbar-tabs span.active {{ color: {THEME['primary']}; font-weight: 600; }}
    .navbar-status {{
        font-size: 0.75rem; color: {THEME['subtext']};
        border: 1px solid {THEME['border']}; border-radius: 999px;
        padding: 0.25rem 0.65rem;
    }}
    .navbar-status .dot {{
        display: inline-block; width: 6px; height: 6px; border-radius: 50%;
        background: {THEME['success']}; margin-right: 0.35rem;
    }}

    /* ---- Command-bar style input ----------------------------------------- */
    .stTextArea textarea {{
        background: {THEME['panel']} !important;
        color: {THEME['text']} !important;
        caret-color: {THEME['primary']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        box-shadow: {THEME['shadow']};
    }}
    .stTextArea textarea:focus {{
        border-color: {THEME['primary']} !important;
        box-shadow: 0 0 0 3px {THEME['primary']}22 !important;
    }}
    .stButton > button {{
        background: {THEME['primary']};
        color: white; border: none; border-radius: 8px;
        font-weight: 600; font-size: 0.88rem; padding: 0.55rem 1.1rem;
        width: 100%;
    }}
    .stButton > button:hover {{ opacity: 0.9; }}

    /* ---- Panels ------------------------------------------------------------ */
    .panel {{
        background: {THEME['panel']};
        border: 1px solid {THEME['border']};
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        box-shadow: {THEME['shadow']};
        height: 100%;
    }}
    .panel-label {{
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.07em;
        text-transform: uppercase; color: {THEME['subtext']}; margin-bottom: 0.6rem;
    }}

    /* ---- KPI tile row ------------------------------------------------------- */
    .kpi-tile {{
        background: {THEME['panel']};
        border: 1px solid {THEME['border']};
        border-left: 3px solid var(--kpi-accent, {THEME['primary']});
        border-radius: 8px;
        padding: 0.85rem 1rem;
        box-shadow: {THEME['shadow']};
    }}
    .kpi-label {{ font-size: 0.7rem; color: {THEME['subtext']}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
    .kpi-value {{ font-size: 1.5rem; font-weight: 700; margin-top: 0.15rem; }}
    .kpi-sub {{ font-size: 0.74rem; color: {THEME['subtext']}; margin-top: 0.1rem; }}

    /* ---- Status pill ------------------------------------------------------- */
    .status-pill {{
        display: inline-flex; align-items: center; gap: 0.35rem;
        padding: 0.3rem 0.75rem; border-radius: 6px;
        font-size: 0.78rem; font-weight: 600;
        background: var(--pill-bg); color: var(--pill-fg);
        border: 1px solid var(--pill-fg);
    }}

    /* ---- Address diff panel ------------------------------------------------- */
    .addr-block {{ margin-bottom: 0.75rem; }}
    .addr-block:last-child {{ margin-bottom: 0; }}
    .addr-text {{
        font-family: 'SFMono-Regular', Consolas, monospace;
        font-size: 0.86rem; background: {THEME['panel_alt']};
        border: 1px solid {THEME['border']}; border-radius: 6px;
        padding: 0.55rem 0.7rem; word-break: break-word; color: {THEME['text']};
    }}

    /* ---- Component table ---------------------------------------------------- */
    .comp-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    .comp-table td {{ padding: 0.45rem 0.5rem; border-bottom: 1px solid {THEME['border']}; }}
    .comp-table td.key {{ color: {THEME['subtext']}; width: 40%; font-weight: 500; }}
    .comp-table tr:last-child td {{ border-bottom: none; }}

    @media (max-width: 768px) {{
        .navbar {{ flex-direction: column; align-items: flex-start; gap: 0.5rem; }}
        .navbar-tabs {{ display: none; }}
    }}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# Navbar
# ──────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="navbar">
    <div class="navbar-brand">Address Standardization</div>
    <div class="navbar-tabs">
        <span class="active">Dashboard</span>
        <span>History</span>
        <span>Settings</span>
    </div>
    <div class="navbar-status"><span class="dot"></span>Model v1 · Live</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# Command-bar input
# ──────────────────────────────────────────────────────────────────────────
input_col, button_col = st.columns([5, 1], vertical_alignment="bottom")
with input_col:
    address = st.text_area(
    " ",
    placeholder="e.g. 45 W 34 St Apt 2, NY 12308",
    label_visibility="collapsed",
    height=68,
    key="address_input",
)

_, center_col, _ = st.columns([2, 1, 2])
with center_col:
    submitted = st.button("Standardize", use_container_width=True)


# Autofocus the textarea on page load via JavaScript
st.markdown("""
<script>
    setTimeout(function() {
        const textareas = window.parent.document.querySelectorAll('textarea');
        if (textareas.length > 0) {
            textareas[0].focus();
        }
    }, 200);
</script>
""", unsafe_allow_html=True)

st.write("")


def _draw_radial_gauge(confidence: float, theme: dict) -> str:
    """Builds a true semicircular gauge (colored zones + needle) as raw SVG."""
    cx, cy, r = 110, 110, 90

    def point(angle_deg, radius):
        rad = math.radians(angle_deg)
        return cx + radius * math.cos(rad), cy - radius * math.sin(rad)

    def angle_for(value):
        return 180 - (max(0.0, min(1.0, value)) * 180)

    def arc_path(v_start, v_end, radius):
        a0, a1 = angle_for(v_start), angle_for(v_end)
        x0, y0 = point(a0, radius)
        x1, y1 = point(a1, radius)
        return f"M {x0:.1f},{y0:.1f} A {radius},{radius} 0 0,1 {x1:.1f},{y1:.1f}"

    zones = [
        (0.0, REVIEW_THRESHOLD, theme["danger"]),
        (REVIEW_THRESHOLD, AUTO_ACCEPT_THRESHOLD, theme["warn"]),
        (AUTO_ACCEPT_THRESHOLD, 1.0, theme["success"]),
    ]
    arcs = "".join(
        f'<path d="{arc_path(start, end, r)}" stroke="{color}" stroke-width="14" '
        f'fill="none" stroke-linecap="butt"/>'
        for start, end, color in zones
    )

    needle_angle = angle_for(confidence)
    nx, ny = point(needle_angle, r * 0.72)

    return f"""
    <svg viewBox="0 0 220 130" width="85%" height="auto" style="max-width:320px;">
        {arcs}
        <line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}"
              stroke="{theme['text']}" stroke-width="3" stroke-linecap="round"/>
        <circle cx="{cx}" cy="{cy}" r="6" fill="{theme['text']}"/>
    </svg>
    """


# ──────────────────────────────────────────────────────────────────────────
# Main dashboard
# ──────────────────────────────────────────────────────────────────────────
if submitted:

    if not address.strip():
        st.warning("Please enter an address before standardizing.")
        st.stop()

    with st.spinner("Parsing, standardizing, and scoring..."):
        parsed = parse_raw_address(address)
        canonical_components = standardize_parsed_components(parsed)
        standardized_address = format_canonical_address(canonical_components)
        features = extract_features(address, standardized_address, parsed, canonical_components)
        confidence = predict_confidence(features)

    if confidence >= AUTO_ACCEPT_THRESHOLD:
        status_color, status_label = THEME["success"], "Auto-Accepted"
        status_detail = "High confidence — no human review required."
    elif confidence >= REVIEW_THRESHOLD:
        status_color, status_label = THEME["warn"], "Review Queue"
        status_detail = "Medium confidence — awaiting human validation."
    else:
        status_color, status_label = THEME["danger"], "Manual Resolution"
        status_detail = "Low confidence — needs hands-on correction."

    components_found = sum(1 for v in canonical_components.values() if v not in (None, ""))

    # ---- KPI tile row -------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f'<div class="kpi-tile" style="--kpi-accent:{status_color};">'
            f'<div class="kpi-label">Confidence</div>'
            f'<div class="kpi-value">{confidence * 100:.1f}%</div>'
            f'<div class="kpi-sub">{status_label}</div></div>',
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'<div class="kpi-tile" style="--kpi-accent:{THEME["primary"]};">'
            f'<div class="kpi-label">Routing</div>'
            f'<div class="kpi-value" style="font-size:1.1rem;">{status_label}</div>'
            f'<div class="kpi-sub">{status_detail}</div></div>',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'<div class="kpi-tile" style="--kpi-accent:{THEME["primary"]};">'
            f'<div class="kpi-label">Components Parsed</div>'
            f'<div class="kpi-value">{components_found}</div>'
            f'<div class="kpi-sub">of {len(canonical_components)} fields</div></div>',
            unsafe_allow_html=True,
        )
    with k4:
        delta = (confidence - AUTO_ACCEPT_THRESHOLD) * 100
        delta_label = f"{delta:+.1f} pts vs. auto-accept" if confidence < AUTO_ACCEPT_THRESHOLD else "Above auto-accept line"
        st.markdown(
            f'<div class="kpi-tile" style="--kpi-accent:{THEME["primary"]};">'
            f'<div class="kpi-label">Threshold Gap</div>'
            f'<div class="kpi-value" style="font-size:1.1rem;">{delta_label}</div>'
            f'<div class="kpi-sub">Auto-accept at {AUTO_ACCEPT_THRESHOLD * 100:.0f}%</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")

    # ---- Main grid: address diff (left) | radial gauge (right) -------------
    left, right = st.columns([1.3, 1])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Address Comparison</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="addr-block"><div style="font-size:0.72rem;color:{THEME["subtext"]};margin-bottom:0.2rem;">INPUT</div>'
            f'<div class="addr-text">{address}</div></div>'
            f'<div class="addr-block"><div style="font-size:0.72rem;color:{THEME["subtext"]};margin-bottom:0.2rem;">STANDARDIZED</div>'
            f'<div class="addr-text">{standardized_address}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="margin-top:0.85rem;">'
            f'<span class="status-pill" style="--pill-bg:{status_color}18;--pill-fg:{status_color};">'
            f'{status_label}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel" style="text-align:center;">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Confidence Gauge</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="display:flex; justify-content:center;">'
            f'{_draw_radial_gauge(confidence, THEME)}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="text-align:center; margin-top:0.3rem;">'
            f'<div style="font-size:1.6rem;font-weight:700;">{confidence * 100:.1f}%</div>'
            f'<div style="font-size:0.72rem;color:{THEME["subtext"]};margin-top:0.2rem;">'
            f'<span style="color:{THEME["danger"]};">●</span> &lt;{REVIEW_THRESHOLD*100:.0f}% &nbsp;'
            f'<span style="color:{THEME["warn"]};">●</span> {REVIEW_THRESHOLD*100:.0f}-{AUTO_ACCEPT_THRESHOLD*100:.0f}% &nbsp;'
            f'<span style="color:{THEME["success"]};">●</span> &gt;{AUTO_ACCEPT_THRESHOLD*100:.0f}%'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")

    # ---- Parsed components table, full width --------------------------------
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">Parsed Components</div>', unsafe_allow_html=True)
    rows_html = "".join(
        f'<tr><td class="key">{k.replace("_", " ").title()}</td><td>{v}</td></tr>'
        for k, v in canonical_components.items() if v not in (None, "")
    )
    st.markdown(f'<table class="comp-table">{rows_html}</table>', unsafe_allow_html=True)
    with st.expander("View raw JSON"):
        st.json(canonical_components)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown(
        f'<div class="panel" style="text-align:center; padding:2.5rem 1rem; color:{THEME["subtext"]};">'
        "Enter an address above and click <b>Standardize</b> to populate the dashboard.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    f"<p style='color:{THEME['subtext']}; font-size:0.74rem; margin-top:1.6rem;'>"
    "Regex Parser · LightGBM · FastAPI · Streamlit</p>",
    unsafe_allow_html=True,
)