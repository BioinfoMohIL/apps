"""Interface Streamlit pour strain_predict (la logique est dans strain_predict.py).

Lancement:
    python strain_predict.py --app --model strain_model.pkl
    # ou directement:
    streamlit run app.py -- --model strain_model.pkl
"""
import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from kmer_utils import find_pairs
from strain_predict import MIN_READS_WARN, load_bundle, predict_folder

MAX_SAMPLES = int(os.environ.get("STRAIN_MAX_SAMPLES", 4))  # limite de samples par run

st.set_page_config(page_title="Species Classifier", page_icon="🧬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp button,
.stApp input, .stApp textarea, [data-testid="stMarkdownContainer"] { font-family: 'Space Grotesk', system-ui, sans-serif; }
/* ne jamais écraser la police des icônes Streamlit (sinon on voit "arrow_right" en texte) */
[data-testid="stIconMaterial"], [class*="material-symbols"], .material-icons, .material-symbols-rounded
  { font-family: 'Material Symbols Rounded', 'Material Icons' !important; }
code, .stDataFrame, [data-testid="stDataFrame"] { font-family: 'JetBrains Mono', ui-monospace, monospace; }
h1 { font-weight: 700; letter-spacing: -0.02em;
     background: linear-gradient(90deg, #0d9488, #0284c7); -webkit-background-clip: text;
     -webkit-text-fill-color: transparent; }
.card { background: #ffffff; border: 1px solid #cfe3e8; border-left: 4px solid #0d9488;
        border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; }
.card.warn { border-left-color: #f59e0b; } .card.err { border-left-color: #ef4444; }
.card .sp { font-size: 1.25rem; font-weight: 600; } .card .meta { color: #4b6b7d; font-size: .85rem; }
</style>
""", unsafe_allow_html=True)


def get_model_path():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--threshold", type=float)
    a, _ = ap.parse_known_args(sys.argv[1:])
    return (a.model or os.environ.get("STRAIN_MODEL", "strain_model.pkl")), a.threshold


MODEL_PATH, THRESHOLD_OVERRIDE = get_model_path()


@st.cache_resource(show_spinner="Loading model…")
def get_bundle(path):
    return load_bundle(path)


def save_uploads(files, dest):
    """Écrit les uploads sur disque en streaming (sans doubler la RAM)."""
    for uf in files:
        with open(Path(dest) / uf.name, "wb") as out:
            shutil.copyfileobj(uf, out)


def card(row):
    if row["predicted"] == "ERROR":
        return (f'<div class="card err"><div class="sp">{row["sample"]}</div>'
                f'<div class="meta">Error: {row["qc"]}</div></div>')
    cls = "card" if row["predicted"] not in ("UNKNOWN",) and row["qc"] == "ok" else "card warn"
    return (f'<div class="{cls}"><div class="sp">{row["sample"]} → <i>{row["predicted"]}</i></div>'
            f'<div class="meta">confidence {row["confidence"]:.0%} · 2nd guess {row["second_guess"]} '
            f'({row["second_confidence"]:.0%}) · {row["n_reads_used"]:,} reads · QC: {row["qc"]}</div></div>')


# ------------------------------------------------------------------ UI
st.title("Species Classifier")
st.caption("Quick species check from paired-end reads (R1/R2) — a fast sanity check, "
           "not a replacement for Kraken2 on Terra.")

try:
    bundle = get_bundle(MODEL_PATH)
except Exception as e:
    st.error(f"Could not load model `{MODEL_PATH}`: {e}")
    st.stop()

default_threshold = THRESHOLD_OVERRIDE if THRESHOLD_OVERRIDE is not None else bundle["threshold"]

with st.sidebar:
    st.subheader("Model")
    st.write(f"**Species:** {len(bundle['model'].classes_)}")
    with st.expander("List"):
        st.write(", ".join(map(str, bundle["model"].classes_)))
    threshold = st.slider(
        "Confidence threshold", 0.0, 1.0, float(default_threshold), 0.05,
        help="Below this confidence, the species is reported as UNKNOWN. "
             "Higher = fewer wrong calls but more UNKNOWN. Applies instantly to current results.",
    )
    st.caption(f"Model default: {bundle['threshold']:.2f}")
    st.write(f"**Max samples per run:** {MAX_SAMPLES}")

files = st.file_uploader(
    "Upload FASTQ files (R1 + R2 per sample, `.fastq`, `.fq` or `.gz`)",
    type=["fastq", "fq", "gz"], accept_multiple_files=True,
)

if files and st.button("Analyze", type="primary"):
    with tempfile.TemporaryDirectory() as tmp:
        save_uploads(files, tmp)
        pairs = find_pairs(tmp)
        paired_names = {Path(p).name for _, r1, r2 in pairs for p in (r1, r2)}
        orphans = sorted({f.name for f in files} - paired_names)

        if orphans:
            st.warning("No R1/R2 mate found for: " + ", ".join(orphans)
                       + " — these files were ignored.")
        if not pairs:
            st.error("No complete R1/R2 pair detected. Check the file names (R1/R2).")
            st.stop()
        if len(pairs) > MAX_SAMPLES:
            st.error(f"{len(pairs)} samples uploaded, max is {MAX_SAMPLES}. Split into several runs.")
            st.stop()

        bar = st.progress(0.0, text="Starting…")
        df = predict_folder(
            tmp, bundle, threshold,
            on_sample=lambda i, n, row: bar.progress(i / n, text=f"{i}/{n} — {row['sample']}"),
        )
        bar.empty()
    st.session_state["results"] = df  # survit aux reruns (ex: clic sur download)

df = st.session_state.get("results")
if df is not None:
    # le seuil est réappliqué en direct sur les confidences déjà calculées (pas de relance)
    df = df.copy()
    ok = df["predicted"] != "ERROR"
    df.loc[ok, "predicted"] = df.loc[ok, "best_guess"].where(
        df.loc[ok, "confidence"] >= threshold, "UNKNOWN")
    st.subheader("Results")
    for _, row in df.iterrows():
        st.markdown(card(row), unsafe_allow_html=True)

    if (df["predicted"] == "UNKNOWN").any():
        st.info("UNKNOWN = best guess below the confidence threshold: the species may not be "
                "in the model. Confirm with Kraken2.")
    if (df["qc"] == "LOW_READS").any():
        st.warning(f"Some samples have fewer than {MIN_READS_WARN:,} reads: unreliable prediction.")

    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={
            "confidence": st.column_config.ProgressColumn("confidence", min_value=0, max_value=1, format="%.2f"),
            "second_confidence": st.column_config.ProgressColumn("second_confidence", min_value=0, max_value=1, format="%.2f"),
        },
    )
    st.download_button("Download CSV", df.to_csv(index=False).encode(),
                       "samples_predictions.csv", "text/csv")