# Freeze Bact — Streamlit interface

Web interface for the sample-freezing selection tool, replacing the Tkinter
launcher (`app.py`). The computation (`freeze_bact.py` / `freeze_bact_v2.py`)
is called directly in-process — no `subprocess` — with a **preview of the
table before download**.

## Install

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Run

```bash
venv/bin/streamlit run streamlit_app.py
```

A browser tab opens (default http://localhost:8501).

## Usage

1. Pick the version (**v2 by default**) and the number of samples in the
   sidebar.
2. Drop the Excel file (`.xlsx`) or CSV — a CSV is converted automatically
   to Excel (encoding detected with `chardet`).
3. Pick the sheet to use if the file has several.
4. Click **Run selection**.
5. Check the preview (`ToFreeze` / `TestResults` sheets + processing log),
   then click **Download the Excel file** to get the final file (formatting
   preserved: colors, column widths, etc.).

## Files

- `streamlit_app.py` — Streamlit interface
- `freeze_bact_v2.py` / `freeze_bact.py` — selection engines (v2 / v1),
  identical to the ones used by `app.py`, with one addition: `select_specimens`
  now returns the path of the generated file (CLI usage unchanged)
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — light theme (teal accent)

## v1 / v2 differences

The only logic difference between the two scripts concerns **MRSA
PVL-negative / Blood** samples:
- **v1**: selects a computed proportion (25% of the remaining need),
  distributed by originator.
- **v2** *(default)*: takes **all** available Blood samples.

## Troubleshooting

**`ModuleNotFoundError: No module named 'openpyxl'` even though `pip
install` says "already satisfied"**: `pip` and `streamlit` are pointing to
two different Python installs (e.g. `pip` → miniconda3, `streamlit` → a
separate `~/.local` Python). Check with:

```bash
which python
which streamlit
python -c "import sys; print(sys.executable)"
```

The safest fix is a dedicated venv, run with its own executables directly
(not relying on `PATH` after activation):

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/streamlit run streamlit_app.py
```

## Notes

- `.xls` files (old binary format) aren't supported by the reading engine
  (`openpyxl`) — convert to `.xlsx` first.
- Each Streamlit session works in its own temporary folder; nothing is
  written into the app's folder.
