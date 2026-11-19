"""Garde seulement les N premiers reads de FASTQ(.gz) pour les uploader dans l'app.

Le modèle n'utilise que les `max_reads` premiers reads: avec N >= max_reads, la
prédiction est identique à celle du fichier complet. Aucune dépendance (Python 3 seul).

Usage:
    python trim_reads.py reads_dir/ -n 200000            # tout un dossier -> subset/
    python trim_reads.py S1_R1.fastq.gz S1_R2.fastq.gz -n 200000 -o subset/

Les noms de fichiers sont conservés (R1/R2 intacts) pour que l'appariement fonctionne.
Valeur de max_reads du modèle:
    python -c "import pickle; print(pickle.load(open('strain_model.pkl','rb'))['max_reads'])"
"""
import argparse
import gzip
import sys
from itertools import islice
from pathlib import Path

EXTS = (".fastq", ".fq", ".fastq.gz", ".fq.gz")


def open_text(path, mode):
    if str(path).endswith(".gz"):
        return gzip.open(path, mode + "t", **({"compresslevel": 1} if mode == "w" else {}))
    return open(path, mode + "t")


def trim(src, dst, n_reads):
    """Copie les n_reads premiers reads (4 lignes chacun) et renvoie le nombre copié."""
    written = 0
    with open_text(src, "r") as fin, open_text(dst, "w") as fout:
        for line in islice(fin, 4 * n_reads):  # s'arrête tôt: pas de lecture du fichier entier
            fout.write(line)
            written += 1
    return written // 4


def collect(inputs):
    files = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.name.endswith(EXTS))
        elif p.is_file():
            files.append(p)
        else:
            sys.exit(f"Introuvable: {item}")
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="Fichiers FASTQ(.gz) ou dossier(s)")
    ap.add_argument("-n", "--reads", type=int, default=200_000, help="Nombre de reads à garder (défaut 200000)")
    ap.add_argument("-o", "--output", default="subset", help="Dossier de sortie (défaut: subset/)")
    args = ap.parse_args()

    files = collect(args.inputs)
    if not files:
        sys.exit("Aucun FASTQ trouvé.")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    for src in files:
        dst = out / src.name
        if dst.resolve() == src.resolve():
            sys.exit(f"Le dossier de sortie écraserait {src}: choisis un autre -o.")
        n = trim(src, dst, args.reads)
        print(f"{src.name}: {n:,} reads  {src.stat().st_size / 1e6:.0f} MB -> {dst.stat().st_size / 1e6:.0f} MB")
    print(f"\nFichiers prêts à uploader dans: {out}/")


if __name__ == "__main__":
    main()
