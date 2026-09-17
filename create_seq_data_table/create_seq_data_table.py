"""
Create Seq Data Table — Streamlit app

Reimplements the logic of app_create_seq_data_bs.ps1 + create_seq_data_table.py.

Takes an Illumina SampleSheet (.csv, with a [Cloud_Data] section containing
Sample_ID / ProjectName) and produces the TSV table ready to import as a
"seq_data" entity table into Terra.
"""

import csv
import datetime as dt
import io

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# Config & constants (carried over as-is from create_seq_data_table.py)
# --------------------------------------------------------------------------

st.set_page_config(page_title="Create Seq Data Table", page_icon="🧬", layout="wide")

SPECIES = {
    "SH": "Salmonella",
    "SO": "Salmonella",
    "LC": "Listeria monocytogenes",
    "LF": "Listeria monocytogenes",
    "SG": "Shigella",
    "CA": "Campylobacter",
    "VIB": "Vibrio",
    "V": "Vibrio",
    "EC": "Escherichia coli",
    "FEC": "Escherichia coli",
    "F-EC": "Escherichia coli",
    "SA": "Staphylococcus aureus",
    "BP": "Bordetella pertussis",
    "ST": "Streptococcus",
    "SP": "Streptococcus pneumoniae",
    "LG": "Legionella pneumophila",
    "LW": "Legionella pneumophila",
    "CB": "Corynebacterium diphtheriae",
    "HI": "Haemophilus influenzae",
    "NM": "Neisseria meningitidis",
    "M": "Neisseria meningitidis",
}
SPECIES_KEYS_SORTED = sorted(SPECIES.keys(), key=len, reverse=True)

DB_NAME_OPTIONS = ["tmp_id", "seq_data_id", "custom_id"]
FACILITY_OPTIONS = ["MOH-JLM", "GGA", "Tel-Aviv", "Guivat-Ram"]
PLATFORM_OPTIONS = ["NextSeq_2000", "MiSeq"]

# --------------------------------------------------------------------------
# Styling — genomics-inspired teal/navy theme
# --------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"]  {
    font-family: 'Space Grotesk', sans-serif;
}
code, pre, .stCode, [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
}

:root {
    --seq-navy: #0b1f2a;
    --seq-teal: #0d9488;
    --seq-teal-deep: #0f766e;
    --seq-teal-soft: #ccfbf1;
    --seq-border: #d7ece8;
    --seq-bg: #f6faf9;
}

.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(13, 148, 136, 0.06), transparent 45%),
        radial-gradient(circle at 85% 10%, rgba(13, 148, 136, 0.05), transparent 40%),
        var(--seq-bg);
}

.seq-hero {
    padding: 1.6rem 1.8rem;
    border-radius: 14px;
    background: linear-gradient(135deg, #ffffff 0%, #eafbf7 100%);
    border: 1px solid var(--seq-border);
    box-shadow: 0 1px 3px rgba(11, 31, 42, 0.06);
    margin-bottom: 1.4rem;
}
.seq-hero h1 {
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--seq-navy);
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.02em;
}
.seq-hero p {
    color: #4b6b66;
    font-size: 0.95rem;
    margin: 0;
}
.seq-hero code {
    background: var(--seq-teal-soft);
    color: var(--seq-teal-deep);
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    font-size: 0.85rem;
}

.seq-step {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    color: var(--seq-teal-deep);
    text-transform: uppercase;
    border: 1px solid var(--seq-border);
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    margin-bottom: 0.6rem;
    background: var(--seq-teal-soft);
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid var(--seq-border);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    box-shadow: 0 1px 2px rgba(11, 31, 42, 0.04);
}

[data-testid="stFileUploaderDropzone"] {
    border: 1px dashed var(--seq-teal) !important;
    border-radius: 12px !important;
    background: #ffffff !important;
}

.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, var(--seq-teal), var(--seq-teal-deep));
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 8px;
}
.stDownloadButton > button:hover, .stButton > button:hover {
    background: linear-gradient(135deg, var(--seq-teal-deep), var(--seq-teal));
    color: #ffffff;
}

section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid var(--seq-border);
}
section[data-testid="stSidebar"] h2 {
    color: var(--seq-navy) !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def fetch_specie_name(sample_id: str) -> str:
    """Same matching logic as fetch_specie_name() in the original script."""
    parts = sample_id.split("_")
    for part in parts:
        for key in SPECIES_KEYS_SORTED:
            if part.startswith(key):
                return SPECIES[key]
    return "Unknown"


def generate_columns(db_name: str):
    return [
        f"entity:{db_name}",
        "species",
        "bs_samplename",
        "run_name",
        "wgs_facility",
        "platform",
        "wgs_sending_date",
        "run_date",
    ]


def parse_samplesheet(raw_text: str):
    """
    Same logic as create_bs_fetcher_table():
    - locate the [Cloud_Data] section
    - read the Sample_ID / ProjectName columns
    - return (rows, warnings)
    """
    lines = raw_text.splitlines()
    start_idx = next((i for i, line in enumerate(lines) if "[Cloud_Data]" in line), None)
    if start_idx is None:
        raise ValueError(
            "Could not find a [Cloud_Data] section in this file. "
            "Is this a full Illumina SampleSheet (including the Cloud_Data section)?"
        )

    table_lines = [line.strip() for line in lines[start_idx + 1:] if line.strip()]
    if not table_lines:
        raise ValueError("No data found after [Cloud_Data].")

    reader = csv.reader(table_lines)
    headers = next(reader, None)
    if not headers or "Sample_ID" not in headers or "ProjectName" not in headers:
        raise ValueError("Missing 'Sample_ID' and/or 'ProjectName' column under [Cloud_Data].")

    sample_id_idx = headers.index("Sample_ID")
    project_name_idx = headers.index("ProjectName")

    rows = []
    warnings = []
    for row in reader:
        if len(row) <= max(sample_id_idx, project_name_idx):
            warnings.append(f"Skipped malformed row: {row}")
            continue
        sample = row[sample_id_idx].strip()
        project_name = row[project_name_idx].strip()
        if not sample:
            continue
        specie_name = fetch_specie_name(sample)
        if specie_name == "Unknown":
            warnings.append(f"Unrecognized species for sample '{sample}' (prefix not mapped)")
        rows.append(
            {
                "sample": sample,
                "species": specie_name,
                "project_name": project_name,
            }
        )

    if not rows:
        raise ValueError("No valid sample rows found under [Cloud_Data].")

    return rows, warnings


def build_output_df(rows, db_name, facility, platform, sending_date, run_date):
    cols = generate_columns(db_name)
    data = [
        [
            r["sample"],
            r["species"],
            r["sample"],
            r["project_name"],
            facility,
            platform,
            sending_date,
            run_date,
        ]
        for r in rows
    ]
    return pd.DataFrame(data, columns=cols)


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------

st.markdown(
    """
    <div class="seq-hero">
        <h1>🧬 Create Seq Data Table</h1>
        <p>Turns an Illumina SampleSheet into a <code>seq_data</code> entity table ready to import into Terra —
        the web equivalent of <code>app_create_seq_data_bs.ps1</code> → <code>create_seq_data_table.py</code>.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Parameters")

    db_name_choice = st.selectbox("Database name", DB_NAME_OPTIONS, index=0)
    if db_name_choice == "custom_id":
        db_name = st.text_input("Custom entity column name", value="custom_id")
    else:
        db_name = db_name_choice

    facility_choice = st.selectbox("WGS facility", FACILITY_OPTIONS + ["Other..."], index=0)
    if facility_choice == "Other...":
        facility = st.text_input("Custom facility", value="")
    else:
        facility = facility_choice

    platform_choice = st.selectbox("Platform", PLATFORM_OPTIONS + ["Other..."], index=0)
    if platform_choice == "Other...":
        platform = st.text_input("Custom platform", value="")
    else:
        platform = platform_choice

    sending_date = st.date_input("Sending date", value=dt.date.today())
    run_date = st.date_input("Run date", value=dt.date.today())

st.markdown('<div class="seq-step">Step 1 · Upload</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Illumina SampleSheet (.csv) — must contain a [Cloud_Data] section",
    type=["csv"],
)

if uploaded_file is not None:
    raw_text = uploaded_file.read().decode("utf-8", errors="replace")

    try:
        rows, warnings = parse_samplesheet(raw_text)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    df = build_output_df(
        rows,
        db_name=db_name,
        facility=facility,
        platform=platform,
        sending_date=sending_date.strftime("%Y-%m-%d"),
        run_date=run_date.strftime("%Y-%m-%d"),
    )

    st.markdown('<div class="seq-step">Step 2 · Result</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Samples", len(df))
    c2.metric("Project(s) (run_name)", df["run_name"].nunique())
    c3.metric("Unrecognized species", sum(1 for r in rows if r["species"] == "Unknown"))

    if warnings:
        with st.expander(f"⚠️ {len(warnings)} warning(s)", expanded=False):
            for w in warnings:
                st.write("- " + w)

    st.dataframe(df, use_container_width=True, hide_index=True)

    # File name: {project_name}_bs_transfer__{timestamp}.tsv, same convention as the original script
    project_name = df["run_name"].iloc[-1] if not df.empty else "output"
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{project_name}_bs_transfer__{timestamp}.tsv"

    tsv_buffer = io.StringIO()
    df.to_csv(tsv_buffer, sep="\t", index=False)

    st.markdown('<div class="seq-step">Step 3 · Download</div>', unsafe_allow_html=True)
    st.download_button(
        label=f"⬇️  Download {output_filename}",
        data=tsv_buffer.getvalue(),
        file_name=output_filename,
        mime="text/tab-separated-values",
    )
else:
    st.info("Upload a SampleSheet to generate the table.")

with st.expander("ℹ️ Species mapping (recognized prefixes)"):
    st.table(
        pd.DataFrame(
            [{"Prefix": k, "Species": v} for k, v in SPECIES.items()]
        )
    )