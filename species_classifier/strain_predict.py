"""Prédiction d'espèce depuis des FASTQ paired-end d'un dossier.

CLI:
    python strain_predict.py --input genomes/ --model strain_model.pkl --output results/

App Streamlit (même code, UI séparée dans app.py):
    python strain_predict.py --app --model strain_model.pkl
"""
import argparse
import pickle
import subprocess
import sys
import warnings
from pathlib import Path

import pandas as pd
import sklearn

from kmer_utils import find_pairs, sample_features

MIN_READS_WARN = 10_000


# --------------------------------------------------------------------------
# Logique réutilisable (utilisée par le CLI ET par app.py)
# --------------------------------------------------------------------------
def load_bundle(model_path):
    """Charge le pickle du modèle et avertit si la version de sklearn diffère."""
    with open(model_path, "rb") as f:
        b = pickle.load(f)
    if b["sklearn_version"] != sklearn.__version__:
        warnings.warn(f"Modèle entraîné avec sklearn {b['sklearn_version']}, version actuelle "
                      f"{sklearn.__version__}: ré-entraîne si les résultats semblent bizarres.")
    return b


def predict_pair(bundle, sample, r1, r2, threshold=None):
    """Prédit une sample (une paire R1/R2) -> dict (une ligne du CSV)."""
    model, k, max_reads = bundle["model"], bundle["k"], bundle["max_reads"]
    threshold = threshold if threshold is not None else bundle["threshold"]
    try:
        # EXACTEMENT la même featurisation que pendant l'entraînement
        x, n_reads = sample_features(r1, r2, k=k, max_reads=max_reads)
        proba = model.predict_proba(x.reshape(1, -1))[0]
    except Exception as e:  # fichier tronqué, gzip corrompu, etc.
        return {"sample": sample, "predicted": "ERROR", "qc": str(e)}

    order = proba.argsort()[::-1]
    best, second = model.classes_[order[0]], model.classes_[order[1]]
    p1, p2 = proba[order[0]], proba[order[1]]
    return {
        "sample": sample,
        "predicted": best if p1 >= threshold else "UNKNOWN",
        "best_guess": best,
        "confidence": round(float(p1), 3),
        "second_guess": second,
        "second_confidence": round(float(p2), 3),
        "n_reads_used": n_reads,
        "qc": "LOW_READS" if n_reads < MIN_READS_WARN else "ok",
    }


def predict_folder(input_dir, bundle, threshold=None, on_sample=None):
    """Prédit toutes les paires d'un dossier -> DataFrame.

    on_sample(i, total, row) est appelé après chaque sample (print en CLI,
    barre de progression dans l'app).
    """
    pairs = find_pairs(str(input_dir))
    if not pairs:
        raise ValueError(f"Aucune paire R1/R2 trouvée dans {input_dir}")
    rows = []
    for i, (sample, r1, r2) in enumerate(pairs, start=1):
        row = predict_pair(bundle, sample, r1, r2, threshold)
        rows.append(row)
        if on_sample:
            on_sample(i, len(pairs), row)
    return pd.DataFrame(rows)


def format_row(row):
    """Ligne de log lisible pour le CLI."""
    if row["predicted"] == "ERROR":
        return f"[ERREUR] {row['sample']}: {row['qc']}"
    return (f"{row['sample']}: {row['predicted']} (best={row['best_guess']}, "
            f"p={row['confidence']:.2f}, 2nd={row['second_guess']} "
            f"p={row['second_confidence']:.2f}) [{row['qc']}]")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="Dossier contenant les FASTQ(.gz) R1/R2")
    ap.add_argument("--model", default="strain_model.pkl")
    ap.add_argument("--output", default=".", help="Dossier de sortie")
    ap.add_argument("--threshold", type=float, help="Écrase le seuil enregistré dans le modèle")
    ap.add_argument("--app", action="store_true", help="Lance l'interface Streamlit (app.py)")
    ap.add_argument("--port", default="8501", help="Port de l'app Streamlit (avec --app)")
    args = ap.parse_args()

    if args.app:
        app_path = Path(__file__).with_name("app.py")
        # tout ce qui suit "--" est lu par app.py (voir get_model_path)
        cmd = [sys.executable, "-m", "streamlit", "run", str(app_path),
               "--server.port", args.port, "--", "--model", args.model]
        if args.threshold is not None:
            cmd += ["--threshold", str(args.threshold)]
        raise SystemExit(subprocess.call(cmd))

    if not args.input:
        ap.error("--input est requis (sauf avec --app)")

    bundle = load_bundle(args.model)
    try:
        df = predict_folder(args.input, bundle, args.threshold,
                            on_sample=lambda i, n, row: print(format_row(row)))
    except ValueError as e:
        raise SystemExit(str(e))

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "samples_predictions.csv", index=False)
    print(f"\nPrédictions sauvegardées: {out / 'samples_predictions.csv'}")


if __name__ == "__main__":
    main()
