import streamlit as st
import pandas as pd
import numpy as np
import io
import re
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sandfly Data Pipeline",
    page_icon="🪰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (UNCHANGED) ────────────────────────────────────────────────────
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

.stApp { background-color: var(--bg) !important; }

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: 'Space Mono', monospace;
    color: var(--accent);
}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: var(--text) !important; }

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
.hero p { color: var(--muted); font-size: 1rem; margin: 0; }

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
.step-card .step-title { font-weight: 600; font-size: 0.95rem; color: var(--text); }
.step-card .step-desc { color: var(--muted); font-size: 0.85rem; margin-top: 0.2rem; }

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

[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px !important;
}

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

[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

.stSuccess { background: rgba(0,212,170,0.1) !important; border-color: var(--accent) !important; }
.stWarning { background: rgba(255,107,53,0.1) !important; border-color: var(--accent2) !important; }
.info-box {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    color: var(--muted);
    font-size: 0.88rem;
    margin-bottom: 1rem;
}

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


# ── Sidebar – pipeline overview (updated to reflect colleague's logic) ────────
with st.sidebar:
    st.markdown("## Pipeline Steps")
    steps = [
        ("01", "Filter Phlebotomus", "Keep PestGroup = Phlebotomus (+ ND); or species-name fallback"),
        ("02", "Select Fields",      "Species, quantity, ID, date, coords"),
        ("03", "Join Sites",         "Merge latitude/longitude from sites file (L0Sites)"),
        ("04", "Seasonal Filter",    "Remove ONLY winter (Nov–Apr) zero-catch rows; keep summer absences & winter catches"),
        ("05", "Clean Species Names","Strip spaces, unify 'P.' / 'P ' prefixes"),
        ("06", "Pivot Table",        "One row per site; coords joined once per site"),
        ("07", "Special Cases",      "Sergentomyia-only → 0 others; ND-only → drop"),
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
    zero_sergentomyia = st.checkbox("Zero-fill Sergentomyia-only rows", value=True)


# ── Column canonicalisation ───────────────────────────────────────────────────
# Maps Hebrew detailed-sheet headers AND the older English 'Sample*' headers
# onto a single canonical schema used by the pipeline.
SAMPLE_ALIASES = {
    "מין": "Species", "species": "Species", "samplespecies": "Species",
    "מספר פרטים": "SampleQuantity", "samplequantity": "SampleQuantity", "quantity": "SampleQuantity",
    "מזהה נקודה": "IDMOH", "idmoh": "IDMOH", "sampleidmoh": "IDMOH",
    "תאריך ביקור": "SampleVisitDate", "samplevisitdate": "SampleVisitDate", "visitdate": "SampleVisitDate",
    "point x itm": "PointXITM", "pointxitm": "PointXITM", "samplepointxitm": "PointXITM",
    "point y itm": "PointYITM", "pointyitm": "PointYITM", "samplepointyitm": "PointYITM",
}
SITE_ALIASES = {
    "siteidmoh": "SiteIDMOH", "idmoh": "SiteIDMOH",
    "sitelatitude": "SiteLatitude", "latitude": "SiteLatitude", "lat": "SiteLatitude",
    "sitelongitude": "SiteLongitude", "longitude": "SiteLongitude", "lon": "SiteLongitude", "lng": "SiteLongitude",
}


def _norm(col: str) -> str:
    """Normalise a header for alias matching: drop '*', collapse spaces, lower-case."""
    s = str(col).strip()
    s = s.replace("*", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()


def detect_map(raw_cols, aliases):
    """Return {raw_col: canonical} for columns whose normalised header is a known alias."""
    out = {}
    for c in raw_cols:
        canon = aliases.get(_norm(c))
        if canon and canon not in out.values():
            out[c] = canon
    return out


# ── File helpers ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_sheet_names(file_bytes: bytes, file_name: str):
    if file_name.lower().endswith(".csv"):
        return None
    try:
        return pd.ExcelFile(io.BytesIO(file_bytes), engine="calamine").sheet_names
    except Exception:
        return pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl").sheet_names


@st.cache_data(show_spinner="Reading file… (this may take a moment on large Excel files)")
def read_file(file_bytes: bytes, file_name: str, sheet_name=None):
    """Cached on raw bytes – re-runs never re-parse the same upload."""
    if file_name.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8-sig")
    sheet = sheet_name if sheet_name is not None else 0
    try:
        return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet, engine="calamine")
    except Exception:
        return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet, engine="openpyxl")


# ── Pipeline function (colleague's logic) ─────────────────────────────────────
@st.cache_data(show_spinner="⏳ Running pipeline… This may take 1–2 minutes on large datasets. Please wait.")
def run_pipeline(samples_df, sites_df, drop_nd, zero_serg, group_col=None):
    """
    Implements the validated SDM-prep logic:
      - Phlebotomus kept by PEST-GROUP column (== Phlebotomus) when one is
        provided (e.g. SamplePestGroup); otherwise by SPECIES NAME
        (starts with 'P ' / 'P.'). ND rows are always kept.
      - Seasonal filter removes ONLY winter-zero rows (keeps summer absences
        and winter catches — essential for presence/absence SDM)
      - Pivot by site ID only; coordinates attached once per site
    Canonical columns: Species (pivot), optional PestGroup (filter),
    SampleQuantity, IDMOH, SampleVisitDate, PointXITM, PointYITM (samples)
    and SiteIDMOH, SiteLatitude, SiteLongitude (sites).
    """
    log = []
    df = samples_df.copy()

    # Step 1 – keep Phlebotomus + ND
    log.append(('info', f"Step 1 · Raw samples rows: {len(df):,}"))
    if 'Species' not in df.columns:
        log.append(('warn', "Step 1 · No 'Species' column – cannot filter"))
        return None, log

    use_group = bool(group_col) and group_col in df.columns
    spc = df['Species'].astype(str).str.strip()
    is_nd = spc.str.upper().eq("ND")

    if use_group:
        grp = (df[group_col].astype(str).str.strip()
               .str.replace(r'\s+', ' ', regex=True).str.lower())
        # mark ND also via the group column (undetermined catches)
        is_nd = is_nd | grp.eq("nd")
        mask_phlebo = grp.eq("phlebotomus") | is_nd
        # ensure ND-marked rows carry 'ND' as their species for downstream steps
        sp_blank = df['Species'].isna() | (spc == "") | spc.str.lower().eq("nan")
        df.loc[grp.eq("nd") & sp_blank, 'Species'] = "ND"
        log_label = f"Step 1 · Kept '{group_col}' = Phlebotomus + ND: {{}} rows"
    else:
        mask_phlebo = (
            df['Species'].astype(str).str.startswith("P ") |
            df['Species'].astype(str).str.startswith("P.") |
            is_nd
        )
        log_label = "Step 1 · Kept species starting with 'P' + ND: {} rows"

    df = df[mask_phlebo].copy()
    log.append(('ok', log_label.format(f"{len(df):,}")))

    # Step 2 – select fields
    keep = ['Species', 'SampleQuantity', 'IDMOH', 'SampleVisitDate', 'PointXITM', 'PointYITM']
    missing = [c for c in keep if c not in df.columns]
    if missing:
        log.append(('warn', f"Step 2 · Missing columns (skipped): {missing}"))
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()
    log.append(('ok', f"Step 2 · Selected {len(keep)} columns"))

    # Step 3 – join sites (coords)
    site_cols = [c for c in ['SiteIDMOH', 'SiteLatitude', 'SiteLongitude'] if c in sites_df.columns]
    if 'SiteIDMOH' in site_cols and 'IDMOH' in df.columns:
        sites_sub = sites_df[site_cols].drop_duplicates('SiteIDMOH')
        df = df.merge(sites_sub, left_on='IDMOH', right_on='SiteIDMOH', how='left')
        n_missing = df['SiteLatitude'].isna().sum() if 'SiteLatitude' in df.columns else 0
        log.append(('ok', f"Step 3 · Joined sites; {n_missing:,} rows without coordinate match"))
    else:
        log.append(('warn', "Step 3 · Could not join sites – check SiteIDMOH / IDMOH columns"))

    # Step 4 – SEASONAL filter: remove ONLY winter-zero rows
    if 'SampleQuantity' in df.columns:
        df['SampleQuantity'] = pd.to_numeric(df['SampleQuantity'], errors='coerce')
    if 'SampleVisitDate' in df.columns:
        df['SampleVisitDate'] = pd.to_datetime(df['SampleVisitDate'], errors='coerce')
        winter = [11, 12, 1, 2, 3, 4]
        month = df['SampleVisitDate'].dt.month
        qty0 = df['SampleQuantity'].fillna(0) if 'SampleQuantity' in df.columns else 0
        is_winter_zero = month.isin(winter) & (qty0 == 0)
        before = len(df)
        df = df[~is_winter_zero].copy()
        log.append(('ok', f"Step 4 · Removed winter (Nov–Apr) zero-catch rows: {before - len(df):,} dropped"))
        log.append(('info', "Step 4 · Summer absences and winter catches were KEPT"))
    else:
        log.append(('warn', "Step 4 · No date column – seasonal filter skipped"))
    log.append(('info', f"Step 4 · Remaining rows: {len(df):,}"))

    # Step 5 – clean species names
    def clean_species(name):
        if pd.isna(name):
            return name
        name = str(name).strip()
        name = re.sub(r'\s+', ' ', name)          # collapse multiple spaces
        name = re.sub(r'^P\.\s*', 'P ', name)     # "P." / "P. " -> "P "
        name = re.sub(r'^P\s+', 'P ', name)       # normalise abbreviated prefix only
        return name                                # full names (e.g. "Phlebotomus …") untouched
    df['Species'] = df['Species'].apply(clean_species)
    uniq = sorted([str(x) for x in df['Species'].dropna().unique()])
    log.append(('ok', f"Step 5 · Species cleaned; {len(uniq)} unique"))
    log.append(('info', f"Step 5 · Species: {uniq[:15]}{'…' if len(uniq) > 15 else ''}"))

    # Step 6 – pivot by SITE only, attach coords once per site
    if 'IDMOH' not in df.columns:
        log.append(('warn', "Step 6 · Cannot pivot – missing IDMOH"))
        return None, log
    coord_cols = [c for c in ['PointXITM', 'PointYITM', 'SiteLatitude', 'SiteLongitude'] if c in df.columns]
    coords = (df[['IDMOH'] + coord_cols]
              .drop_duplicates(subset='IDMOH')
              .set_index('IDMOH'))
    pivot = (df.groupby(['IDMOH', 'Species'])['SampleQuantity']
               .sum()
               .unstack(fill_value=0))
    result = coords.join(pivot, how='left').reset_index()
    result.columns.name = None
    log.append(('ok', f"Step 6 · Pivot done: {len(result):,} sites × {len(result.columns):,} columns"))

    fixed_cols = ['IDMOH'] + coord_cols
    species_cols = [c for c in result.columns if c not in fixed_cols]

    # Step 7 – special cases
    serg_cols = [c for c in species_cols if 'sergent' in str(c).lower()]
    nd_cols   = [c for c in species_cols if str(c).strip().upper() == 'ND']
    phlebo_cols = [c for c in species_cols if c not in serg_cols + nd_cols]

    if zero_serg and serg_cols and phlebo_cols:
        mask = (result[serg_cols].sum(axis=1) > 0) & (result[phlebo_cols].sum(axis=1) == 0)
        result.loc[mask, phlebo_cols] = 0
        log.append(('ok', f"Step 7 · Sergentomyia-only rows zeroed: {int(mask.sum()):,}"))

    if drop_nd and nd_cols and phlebo_cols:
        nd_only = (result[nd_cols].sum(axis=1) > 0) & (result[phlebo_cols].sum(axis=1) == 0)
        if serg_cols:
            nd_only = nd_only & (result[serg_cols].sum(axis=1) == 0)
        result = result[~nd_only].copy()
        log.append(('ok', f"Step 7 · ND-only rows dropped: {int(nd_only.sum()):,}"))

    # Step 8 – binarise
    species_cols = [c for c in result.columns if c not in fixed_cols]
    result[species_cols] = (result[species_cols] > 0).astype(int)
    log.append(('ok', f"Step 8 · Binarised: {len(result):,} sites, {len(species_cols):,} species columns"))

    # Step 9 – order columns (coords first, then species A→Z)
    result = result[fixed_cols + sorted(species_cols)]

    return result, log


# ── File upload ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📂 Upload Source Files</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Samples file** — detailed sheet with dates")
    samples_file = st.file_uploader("Upload samples (Excel or CSV)", type=["xlsx", "xls", "csv"], key="samples")
with col2:
    st.markdown("**Sites file** — `backup_sites`")
    sites_file = st.file_uploader("Upload sites (Excel or CSV)", type=["xlsx", "xls", "csv"], key="sites")


# ── Run section ───────────────────────────────────────────────────────────────
can_run = samples_file is not None and sites_file is not None

if not can_run:
    st.markdown("""
    <div class="info-box">
      ⬆️ Please upload both files above to enable the pipeline.
    </div>""", unsafe_allow_html=True)

if can_run:
    # Sheet selection (Excel only)
    samples_sheets = get_sheet_names(samples_file.getvalue(), samples_file.name)
    sites_sheets   = get_sheet_names(sites_file.getvalue(), sites_file.name)

    st.markdown('<div class="section-title">📑 Sheet & Column Setup</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    with sc1:
        if samples_sheets:
            s_default = samples_sheets.index("Sheet1") if "Sheet1" in samples_sheets else 0
            samples_sheet = st.selectbox("Samples sheet", samples_sheets, index=s_default)
        else:
            samples_sheet = None
    with sc2:
        if sites_sheets:
            t_default = sites_sheets.index("L0Sites") if "L0Sites" in sites_sheets else 0
            sites_sheet = st.selectbox("Sites sheet", sites_sheets, index=t_default)
        else:
            sites_sheet = None

    samples_raw = read_file(samples_file.getvalue(), samples_file.name, samples_sheet)
    sites_raw   = read_file(sites_file.getvalue(), sites_file.name, sites_sheet)

    # Auto-detect column mapping
    smap = detect_map(list(samples_raw.columns), SAMPLE_ALIASES)
    tmap = detect_map(list(sites_raw.columns), SITE_ALIASES)
    raw_cols = list(samples_raw.columns)

    # --- Pest-group column (used to SELECT Phlebotomus): default SamplePestGroup ---
    NONE = "— none (filter by species name) —"
    grp_guess = [c for c in raw_cols if "pestgroup" in _norm(c).replace(" ", "")]
    grp_options = [NONE] + raw_cols
    grp_default = grp_options.index(grp_guess[0]) if grp_guess else 0

    # --- Species column (used to BUILD the matrix / pivot) ---
    species_guess = ([r for r, c in smap.items() if c == 'Species'] or
                     [c for c in raw_cols if "species" in _norm(c) or _norm(c) == "מין"])
    sp_default = raw_cols.index(species_guess[0]) if species_guess else 0

    c_grp, c_sp = st.columns(2)
    with c_grp:
        group_choice = st.selectbox(
            "🪲 Pest-group column (filter)",
            options=grp_options,
            index=grp_default,
            help="Rows kept where this equals 'Phlebotomus' (+ ND). "
                 "Choose 'none' if your file has species names only (e.g. 'P papatasi')."
        )
    with c_sp:
        species_choice = st.selectbox(
            "🔎 Species column (matrix)",
            options=raw_cols,
            index=sp_default,
            help="Column whose values become the species columns of the matrix."
        )

    group_col = None if group_choice == NONE else 'PestGroup'

    # Build final rename map: force chosen species → 'Species', chosen group → 'PestGroup'
    sample_rename = {r: c for r, c in smap.items() if c not in ('Species',)}
    sample_rename[species_choice] = 'Species'
    if group_col:
        sample_rename[group_choice] = 'PestGroup'
    samples_canon = samples_raw.rename(columns=sample_rename)
    sites_canon   = sites_raw.rename(columns=tmap)

    # Show detected mapping
    detected = ", ".join(f"{c} ← {r}" for r, c in sample_rename.items())
    st.markdown(f'<div class="info-box">🧭 Column mapping: {detected}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">⚙️ Run Pipeline</div>', unsafe_allow_html=True)
    st.caption("⏱ First run may take 1–2 minutes depending on file size. Subsequent runs are instant.")
    if st.button("▶  RUN PIPELINE"):
        result_df, log_entries = run_pipeline(
            samples_canon, sites_canon,
            drop_nd=drop_nd_only, zero_serg=zero_sergentomyia,
            group_col=group_col,
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
            prefix = {"ok": "✔", "warn": "⚠", "info": "ℹ"}[kind]
            log_html += f'<div class="{cls}">{prefix}  {msg}</div>'
        st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

        if result_df is not None and len(result_df) > 0:
            st.success(f"✅ Pipeline complete — {len(result_df):,} sites, {len(result_df.columns):,} columns")

            meta_cols = [c for c in result_df.columns if c in
                         ['IDMOH', 'PointXITM', 'PointYITM', 'SiteLatitude', 'SiteLongitude']]
            sp_cols = [c for c in result_df.columns if c not in meta_cols]
            n_presence = int(result_df[sp_cols].sum().sum()) if sp_cols else 0

            st.markdown(f"""
            <div class="metric-row">
              <div class="metric-box"><div class="val">{len(result_df):,}</div><div class="lbl">Sites</div></div>
              <div class="metric-box"><div class="val">{len(sp_cols)}</div><div class="lbl">Species</div></div>
              <div class="metric-box"><div class="val">{n_presence:,}</div><div class="lbl">Presences (1s)</div></div>
              <div class="metric-box"><div class="val">{round(n_presence/max(len(result_df)*len(sp_cols),1)*100,1)}%</div><div class="lbl">Occupancy</div></div>
            </div>""", unsafe_allow_html=True)

            st.markdown('<div class="section-title">📊 Output Preview</div>', unsafe_allow_html=True)
            tab_a, tab_b = st.tabs(["🗺 Full table", "📈 Species totals"])
            with tab_a:
                st.dataframe(result_df, use_container_width=True, height=400)
            with tab_b:
                if sp_cols:
                    totals = result_df[sp_cols].sum().sort_values(ascending=False).reset_index()
                    totals.columns = ['Species', 'Sites with presence']
                    st.dataframe(totals, use_container_width=True, height=400)

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
            st.error("Pipeline returned no data. Check your files, sheet, and column mapping.")