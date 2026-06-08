import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sandfly Data Pipeline",
    page_icon="🪰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg: #f5f7fa;
    --surface: #ffffff;
    --surface2: #eef1f6;
    --accent: #0a7c5c;
    --accent-light: #e6f5f0;
    --accent2: #e05c2a;
    --text: #1a2030;
    --muted: #6b7280;
    --border: #dde3ec;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text);
}

/* Streamlit app background */
.stApp {
    background-color: var(--bg) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: 'Space Mono', monospace;
    color: var(--accent);
}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
    color: var(--text) !important;
}

/* Main header */
.hero {
    background: linear-gradient(135deg, #e6f5f0 0%, #f0f7ff 60%, #fef9f6 100%);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(10,124,92,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.hero h1 {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    color: var(--accent);
    margin: 0 0 0.4rem 0;
    letter-spacing: -1px;
}
.hero p {
    color: var(--muted);
    font-size: 1rem;
    margin: 0;
}

/* Step cards */
.step-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}
.step-card .step-num {
    font-family: 'Space Mono', monospace;
    color: var(--accent);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
}
.step-card .step-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text);
}
.step-card .step-desc {
    color: var(--muted);
    font-size: 0.85rem;
    margin-top: 0.2rem;
}

/* Metric boxes */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1.5rem 0;
}
.metric-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
}
.metric-box .val {
    font-family: 'Space Mono', monospace;
    font-size: 1.8rem;
    color: var(--accent);
    font-weight: 700;
}
.metric-box .lbl {
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Buttons */
.stButton > button {
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 1px !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #085e45 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(10,124,92,0.25) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 8px 8px 0 0 !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    color: var(--muted) !important;
    padding: 0.8rem 1.5rem !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* Alerts / info boxes */
.stSuccess {
    background: rgba(0,212,170,0.1) !important;
    border-color: var(--accent) !important;
}
.stWarning {
    background: rgba(255,107,53,0.1) !important;
    border-color: var(--accent2) !important;
}
.info-box {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    color: var(--muted);
    font-size: 0.88rem;
    margin-bottom: 1rem;
}

/* Section titles */
.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: var(--accent);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin: 2rem 0 1rem 0;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
}

/* Log output */
.log-box {
    background: #f8fafb;
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.78rem;
    color: var(--text);
    max-height: 300px;
    overflow-y: auto;
    line-height: 1.8;
}
.log-ok   { color: #0a7c5c; }
.log-warn { color: #b45309; }
.log-info { color: #1d4ed8; }
</style>
""", unsafe_allow_html=True)


# ── Hero banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🪰 Sandfly Data Pipeline</h1>
  <p>Phlebotomus presence/absence matrix builder · Upload → Process → Download</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar – pipeline overview ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Pipeline Steps")
    steps = [
        ("01", "Filter Phlebotomus", "Keep rows where PestGroup = Phlebotomus"),
        ("02", "Select Fields",      "Species, quantity, ID, date, coords"),
        ("03", "Join Sites",         "Merge latitude/longitude from sites file"),
        ("04", "Filter Season & Qty","Remove Nov–Apr & zero-quantity rows"),
        ("05", "Clean Species Names","Strip spaces, fix duplicates"),
        ("06", "Pivot Table",        "One row per site, one col per species"),
        ("07", "Special Cases",      "Sergentomia-only → 0 others; ND-only → drop"),
        ("08", "Binarise",           "Any value > 0 → 1, else → 0"),
    ]
    for num, title, desc in steps:
        st.markdown(f"""
        <div class="step-card">
          <div class="step-num">Step {num}</div>
          <div class="step-title">{title}</div>
          <div class="step-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Settings")
    drop_nd_only = st.checkbox("Remove ND-only rows", value=True)
    zero_sergentomia = st.checkbox("Zero-fill Sergentomia-only rows", value=True)


# ── File upload ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📂 Upload Source Files</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Samples file** — `backup_samples`")
    samples_file = st.file_uploader("Upload samples (Excel or CSV)", type=["xlsx","xls","csv"], key="samples")
with col2:
    st.markdown("**Sites file** — `backup_sites`")
    sites_file   = st.file_uploader("Upload sites (Excel or CSV)",   type=["xlsx","xls","csv"], key="sites")


# ── Helper: read uploaded file ────────────────────────────────────────────────
@st.cache_data(show_spinner="Reading file… (this may take a moment on large Excel files)")
def read_file(file_bytes: bytes, file_name: str):
    """Cached on raw bytes – re-runs never re-parse the same upload."""
    if file_name.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8-sig")
    else:
        try:
            return pd.read_excel(io.BytesIO(file_bytes), engine="calamine")
        except Exception:
            return pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")


# ── Pipeline function ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner="⏳ Running pipeline… This may take 1–2 minutes on large datasets. Please wait.")
def run_pipeline(samples_df, sites_df, drop_nd, zero_serg, pestgroup_col="SamplePestGroup"):
    log = []

    # Step 1 – filter Phlebotomus
    log.append(('info', f"Step 1 · Raw samples rows: {len(samples_df):,}"))
    if pestgroup_col and pestgroup_col in samples_df.columns:
        samples_df = samples_df[samples_df[pestgroup_col].astype(str).str.strip() == 'Phlebotomus'].copy()
        log.append(('ok', f"Step 1 · Filtered on '{pestgroup_col}' = Phlebotomus"))
    else:
        log.append(('warn', f"Column '{pestgroup_col}' not found – skipping filter"))
    log.append(('ok', f"Step 1 · After Phlebotomus filter: {len(samples_df):,} rows"))

    # Step 2 – select fields
    keep = ['SampleSpecies','SampleQuantity','SampleIDMOH','SampleVisitDate',
            'SamplePointXITM','SamplePointYITM']
    missing = [c for c in keep if c not in samples_df.columns]
    if missing:
        log.append(('warn', f"Step 2 · Missing columns (will be skipped): {missing}"))
    keep = [c for c in keep if c in samples_df.columns]
    samples_df = samples_df[keep].copy()
    log.append(('ok', f"Step 2 · Selected {len(keep)} columns"))

    # Step 3 – join sites
    site_cols = ['SiteIDMOH','SiteLatitude','SiteLongitude']
    available = [c for c in site_cols if c in sites_df.columns]
    if 'SiteIDMOH' in available and 'SampleIDMOH' in samples_df.columns:
        sites_sub = sites_df[available].drop_duplicates('SiteIDMOH')
        before = len(samples_df)
        samples_df = samples_df.merge(sites_sub, left_on='SampleIDMOH', right_on='SiteIDMOH', how='left')
        log.append(('ok', f"Step 3 · Joined sites; {len(samples_df):,} rows (was {before:,})"))
    else:
        log.append(('warn', "Step 3 · Could not join sites – check SiteIDMOH / SampleIDMOH columns"))

    # Step 4 – filter quantity & season
    if 'SampleQuantity' in samples_df.columns:
        samples_df['SampleQuantity'] = pd.to_numeric(samples_df['SampleQuantity'], errors='coerce').fillna(0)
        before = len(samples_df)
        samples_df = samples_df[samples_df['SampleQuantity'] > 0]
        log.append(('ok', f"Step 4 · Removed zero-quantity rows: {before - len(samples_df):,} dropped"))

    if 'SampleVisitDate' in samples_df.columns:
        samples_df['SampleVisitDate'] = pd.to_datetime(samples_df['SampleVisitDate'], errors='coerce')
        before = len(samples_df)
        off_season = [11, 12, 1, 2, 3, 4]
        samples_df = samples_df[~samples_df['SampleVisitDate'].dt.month.isin(off_season)]
        log.append(('ok', f"Step 4 · Removed off-season (Nov–Apr): {before - len(samples_df):,} dropped"))

    log.append(('info', f"Step 4 · Remaining rows: {len(samples_df):,}"))

    # Step 5 – clean species names
    if 'SampleSpecies' in samples_df.columns:
        samples_df['SampleSpecies'] = (samples_df['SampleSpecies']
            .astype(str).str.strip()
            .str.replace(r'\s+', ' ', regex=True)
            .str.title())
        n_species = samples_df['SampleSpecies'].nunique()
        log.append(('ok', f"Step 5 · Species cleaned; {n_species} unique species"))

    # Step 6 – pivot
    coord_cols = [c for c in ['SamplePointXITM','SamplePointYITM','SiteLatitude','SiteLongitude']
                  if c in samples_df.columns]
    if 'SampleIDMOH' not in samples_df.columns or 'SampleSpecies' not in samples_df.columns:
        log.append(('warn', "Step 6 · Cannot pivot – missing SampleIDMOH or SampleSpecies"))
        return None, log

    wide = (samples_df
            .groupby(['SampleIDMOH'] + coord_cols + ['SampleSpecies'])['SampleQuantity']
            .sum()
            .unstack(fill_value=0)
            .reset_index())
    wide.columns.name = None
    log.append(('ok', f"Step 6 · Pivot done: {len(wide):,} sites × {len(wide.columns):,} columns"))

    species_cols = [c for c in wide.columns if c not in ['SampleIDMOH'] + coord_cols]

    # Step 7 – special cases
    serg_cols = [c for c in species_cols if 'Sergentomia' in c]
    nd_cols   = [c for c in species_cols if c.upper() == 'ND' or c.lower() == 'nd']
    other_sp  = [c for c in species_cols if c not in serg_cols + nd_cols]

    if zero_serg and serg_cols and other_sp:
        mask_serg_only = (wide[serg_cols].sum(axis=1) > 0) & (wide[other_sp].sum(axis=1) == 0)
        wide.loc[mask_serg_only, other_sp] = 0
        log.append(('ok', f"Step 7 · Sergentomia-only rows zeroed: {mask_serg_only.sum():,}"))

    if drop_nd and nd_cols and other_sp + serg_cols:
        mask_nd_only = (wide[nd_cols].sum(axis=1) > 0) & (wide[other_sp + serg_cols].sum(axis=1) == 0)
        wide = wide[~mask_nd_only]
        log.append(('ok', f"Step 7 · ND-only rows dropped: {mask_nd_only.sum():,}"))

    # Step 8 – binarise
    for c in species_cols:
        if c in wide.columns:
            wide[c] = (wide[c] > 0).astype(int)
    log.append(('ok', f"Step 8 · Binarised: {len(wide):,} sites, {len(species_cols):,} species"))

    return wide, log


# ── Run button & output ───────────────────────────────────────────────────────
can_run = samples_file is not None and sites_file is not None

if not can_run:
    st.markdown("""
    <div class="info-box">
      ⬆️ Please upload both files above to enable the pipeline.
    </div>""", unsafe_allow_html=True)

if can_run:
    samples_raw = read_file(samples_file.getvalue(), samples_file.name)
    sites_raw   = read_file(sites_file.getvalue(), sites_file.name)

    st.markdown('<div class="section-title">⚙️ Run Pipeline</div>', unsafe_allow_html=True)

    # PestGroup column selector — narrow width
    all_cols = list(samples_raw.columns)
    default_candidates = [c for c in all_cols if 'pestgroup' in c.lower()]
    default_idx = all_cols.index(default_candidates[0]) if default_candidates else 0
    sel_col, _ = st.columns([1, 2])
    with sel_col:
        pestgroup_col = st.selectbox(
            "🔎 PestGroup column",
            options=all_cols,
            index=default_idx,
            help="Column containing pest group values (e.g. Phlebotomus)."
        )

    st.caption("⏱ First run may take 1–2 minutes depending on file size. Subsequent runs are instant.")
    if st.button("▶  RUN PIPELINE"):
        result_df, log_entries = run_pipeline(
            samples_raw, sites_raw,
            drop_nd=drop_nd_only, zero_serg=zero_sergentomia,
            pestgroup_col=pestgroup_col
        )
        st.session_state["result_df"]   = result_df
        st.session_state["log_entries"] = log_entries

    result_df   = st.session_state.get("result_df")
    log_entries = st.session_state.get("log_entries")

    if log_entries is not None:

        # Log
        log_html = ""
        for kind, msg in log_entries:
            cls = f"log-{kind}"
            prefix = {"ok":"✔","warn":"⚠","info":"ℹ"}[kind]
            log_html += f'<div class="{cls}">{prefix}  {msg}</div>'
        st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

        if result_df is not None and len(result_df) > 0:
            st.success(f"✅ Pipeline complete — {len(result_df):,} sites, {len(result_df.columns):,} columns")

            # Metrics
            meta_cols = [c for c in result_df.columns if c in
                         ['SampleIDMOH','SamplePointXITM','SamplePointYITM','SiteLatitude','SiteLongitude']]
            sp_cols  = [c for c in result_df.columns if c not in meta_cols]
            n_presence = int(result_df[sp_cols].sum().sum()) if sp_cols else 0

            st.markdown(f"""
            <div class="metric-row">
              <div class="metric-box"><div class="val">{len(result_df):,}</div><div class="lbl">Sites</div></div>
              <div class="metric-box"><div class="val">{len(sp_cols)}</div><div class="lbl">Species</div></div>
              <div class="metric-box"><div class="val">{n_presence:,}</div><div class="lbl">Presences (1s)</div></div>
              <div class="metric-box"><div class="val">{round(n_presence/max(len(result_df)*len(sp_cols),1)*100,1)}%</div><div class="lbl">Occupancy</div></div>
            </div>""", unsafe_allow_html=True)

            # Output preview
            st.markdown('<div class="section-title">📊 Output Preview</div>', unsafe_allow_html=True)
            tab_a, tab_b = st.tabs(["🗺 Full table", "📈 Species totals"])
            with tab_a:
                st.dataframe(result_df, use_container_width=True, height=400)
            with tab_b:
                if sp_cols:
                    totals = result_df[sp_cols].sum().sort_values(ascending=False).reset_index()
                    totals.columns = ['Species','Sites with presence']
                    st.dataframe(totals, use_container_width=True, height=400)

            # Download
            st.markdown('<div class="section-title">⬇ Download</div>', unsafe_allow_html=True)
            csv_buf = result_df.to_csv(index=False).encode("utf-8-sig")
            xl_buf = io.BytesIO()
            with pd.ExcelWriter(xl_buf, engine="openpyxl") as writer:
                result_df.to_excel(writer, index=False, sheet_name="SandflyMatrix")
            dl1, dl2, _ = st.columns([1, 1, 2])
            with dl1:
                st.download_button("⬇ CSV", csv_buf,
                                   file_name=f"sandfly_matrix_{datetime.today().strftime('%Y%m%d')}.csv",
                                   mime="text/csv", use_container_width=True)
            with dl2:
                st.download_button("⬇ Excel", xl_buf.getvalue(),
                                   file_name=f"sandfly_matrix_{datetime.today().strftime('%Y%m%d')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
        else:
            st.error("Pipeline returned no data. Check your files and column names.")