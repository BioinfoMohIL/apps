"""
Freeze Bact — Streamlit interface
==================================
Web interface for the sample-freezing selection tool.
Replaces the Tkinter launcher (app.py): the computation is called directly
in-process (no subprocess), with a preview of the result before download.

Run with:  streamlit run streamlit_app.py
"""

import io
import os
import sys
import shutil
import tempfile
import contextlib
from datetime import datetime

import chardet
import pandas as pd
import streamlit as st

# Calculation engines (same scripts used by the Tkinter launcher)
import freeze_bact as engine_v1
import freeze_bact_v2 as engine_v2

ENGINES = {"v2": engine_v2, "v1": engine_v1}


def parse_tofreeze_sheet(raw_df, engine):
    """Turn the raw ToFreeze sheet (title rows, repeated headers, blank
    separators all interleaved in the same columns) into:
    - a tidy DataFrame of real sample rows only, with a 'Category' column
    - a small summary DataFrame of Needed/Found/Added per category
    """
    rows = raw_df.values.tolist()
    if not rows:
        return pd.DataFrame(), pd.DataFrame()

    headers = [str(h) if h is not None else "" for h in rows[0]]
    titles = set(engine.TITLES)

    clean_rows = []
    summary_rows = []
    current_category = None

    for row in rows[1:]:
        if all(pd.isna(v) or (isinstance(v, str) and v.strip() == "") for v in row):
            continue  # blank separator row

        first = row[0]
        if not pd.isna(first) and first in titles:
            current_category = first
            needed = row[1] if len(row) > 1 else None
            found = row[2] if len(row) > 2 else None
            added = row[3] if len(row) > 3 else None
            summary_rows.append({
                "Category": first,
                "Needed": needed if not pd.isna(needed) else "—",
                "Found": found if not pd.isna(found) else "—",
                "Added": added if not pd.isna(added) else "—",
            })
            continue

        if not pd.isna(first) and first == headers[0] and len(row) > 1 and row[1] == headers[1]:
            continue  # repeated header row

        clean_rows.append([current_category] + list(row))

    clean_df = pd.DataFrame(clean_rows, columns=["Category"] + headers)
    summary_df = pd.DataFrame(summary_rows)
    return clean_df, summary_df

st.set_page_config(page_title="Freeze Bact", page_icon="🧊", layout="wide")

# ---------------------------------------------------------------------------
# Style — light theme, navy/teal accents
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }
    .stCodeBlock, code, pre, .stDataFrame { font-family: 'JetBrains Mono', monospace !important; }

    div[data-testid="stMetric"] {
        background: rgba(13, 148, 136, 0.06);
        border: 1px solid rgba(13, 148, 136, 0.25);
        border-radius: 10px;
        padding: 10px 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧊 Freeze Bact")
st.caption("Automatic selection of samples to freeze — preview before export.")

if "result" not in st.session_state:
    st.session_state.result = None  # dict: output_path, sheets, logs, n_selected, n_requested

# ---------------------------------------------------------------------------
# Sidebar — parameters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Settings")

    version = st.radio(
        "Script version",
        options=["v2", "v1"],
        index=0,
        format_func=lambda v: f"{v} (default)" if v == "v2" else v,
        help="v2 takes all available MRSA PVL-negative Blood samples. "
             "v1 takes a computed proportion instead.",
    )

    num_of_specimen = st.number_input(
        "Number of samples to freeze",
        min_value=1, max_value=500, value=30, step=1,
    )

    st.divider()
    st.caption("Expected file: Excel (.xlsx) — a .csv is converted automatically.")

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader("Sample file", type=["xlsx", "xls", "csv"])

if uploaded_file is None:
    st.info("Drop an Excel or CSV file to get started.")
    st.stop()

# Temporary working folder, dedicated to this session
if "work_dir" not in st.session_state:
    st.session_state.work_dir = tempfile.mkdtemp(prefix="freeze_bact_")
work_dir = st.session_state.work_dir
input_dir = os.path.join(work_dir, "input")
output_dir = os.path.join(work_dir, "output")
os.makedirs(input_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

raw_path = os.path.join(input_dir, uploaded_file.name)
with open(raw_path, "wb") as f:
    f.write(uploaded_file.getbuffer())

# Convert a CSV to xlsx (same logic as the Tkinter launcher)
excel_path = raw_path
if raw_path.lower().endswith(".csv"):
    with open(raw_path, "rb") as f:
        detected_encoding = chardet.detect(f.read(100_000))["encoding"]
    try:
        df_csv = pd.read_csv(raw_path, encoding=detected_encoding)
    except Exception as e:
        st.error(f"Could not read the CSV ({detected_encoding}): {e}")
        st.stop()
    excel_path = raw_path[:-4] + ".xlsx"
    df_csv.to_excel(excel_path, index=False)
    default_sheet_names = ["Sheet1"]
else:
    try:
        default_sheet_names = pd.ExcelFile(excel_path).sheet_names
    except Exception as e:
        st.error(f"Could not read this Excel file: {e}")
        st.stop()

sheet_name = st.selectbox("Sheet to use", options=default_sheet_names, index=0)

run_clicked = st.button("▶️ Run selection", type="primary")

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if run_clicked:
    engine = ENGINES[version]
    log_buffer = io.StringIO()
    try:
        with st.spinner(f"Running ({version})…"):
            with contextlib.redirect_stdout(log_buffer):
                data = engine.load_data(excel_path, sheet_name)
                if not data:
                    raise ValueError("The selected sheet is empty.")
                output_path = engine.select_specimens(
                    data, output_dir, num_of_specimen=int(num_of_specimen)
                )

        sheets = pd.read_excel(output_path, sheet_name=None, header=None)
        test_results = pd.read_excel(output_path, sheet_name="TestResults")
        n_selected = int((test_results["Test Result"] == "yes").sum())
        clean_df, summary_df = parse_tofreeze_sheet(sheets["ToFreeze"], engine)

        st.session_state.result = {
            "output_path": output_path,
            "sheets": sheets,
            "clean_df": clean_df,
            "summary_df": summary_df,
            "test_results": test_results,
            "logs": log_buffer.getvalue(),
            "n_selected": n_selected,
            "n_requested": int(num_of_specimen),
            "version": version,
        }
    except Exception as e:
        st.session_state.result = None
        st.error(f"Selection failed: {e}")
        with st.expander("Details"):
            st.code(log_buffer.getvalue() or "(no output)")

# ---------------------------------------------------------------------------
# Result — preview + download
# ---------------------------------------------------------------------------
result = st.session_state.result
if result:
    st.success(f"Selection completed with {result['version']}.")

    c1, c2 = st.columns(2)
    c1.metric("Samples selected", result["n_selected"])
    c2.metric("Requested", result["n_requested"])

    tab_freeze, tab_tests, tab_logs = st.tabs(["📋 ToFreeze", "🧪 TestResults", "📝 Log"])

    with tab_freeze:
        if not result["summary_df"].empty:
            st.caption("Needed / Found / Added per category (categories without a target take all matching samples).")
            st.dataframe(result["summary_df"], use_container_width=True, hide_index=True)

        st.caption("Selected samples, one row per sample.")
        st.dataframe(result["clean_df"], use_container_width=True, height=450)

        with st.expander("Raw sheet (as exported, with section titles)"):
            st.dataframe(result["sheets"]["ToFreeze"], use_container_width=True, height=400)

    with tab_tests:
        st.dataframe(result["test_results"], use_container_width=True, height=500)

    with tab_logs:
        st.code(result["logs"] or "(no output)", language=None)

    with open(result["output_path"], "rb") as f:
        st.download_button(
            "⬇️ Download the Excel file",
            data=f.read(),
            file_name=os.path.basename(result["output_path"]),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
