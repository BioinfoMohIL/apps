"""
app.py – CSV → Template XLSX converter
Dependencies: streamlit, xlsxwriter
No pandas or openpyxl required.
"""

import csv
import io
from datetime import datetime
import streamlit as st
import xlsxwriter

# ── Column mapping: CSV name → final output name ─────────────────────────────
RENAME_MAP = {
    "WNV No."             : "WNV No.",
    "מיקום מבחנה בקופסה" : "מיקום מבחנה בקופסה",
    "מזהה מבחנה"          : "מזהה מבחנה",
    "תאריך ביקור"         : "תאריך איסוף",
    "שם נקודה"            : "שם נקודת ניטור",
    "שם אתר"              : "שם אתר",
    "רשות שיפוט"          : "רשות שיפוט",
    "מחוז הגנת סביבה"     : "מחוז",
    "מין"                 : "בדיקות נגיף - מין",
    "מספר פרטים"          : "בדיקות נגיף - כמות נקבות",
    "קוד ביקור"           : "מזהה ביקור",
    "Point X ITM"         : "Point X ITM",
    "Point Y ITM"         : "Point Y ITM",
    "מזהה נקודה"          : "מזהה נקודת ניטור",
    "שם פקח"              : "שם דוגם",
}

# ── Final column order (matches template row 1) ──────────────────────────────
OUTPUT_COLUMNS = [
    "WNV No.",
    "מיקום מבחנה בקופסה",
    "מזהה מבחנה",
    "תאריך איסוף",
    "שם נקודת ניטור",
    "שם אתר",
    "רשות שיפוט",
    "מחוז",
    "בדיקות נגיף - מין",
    "בדיקות נגיף - כמות נקבות",
    "מזהה ביקור",
    "Point X ITM",
    "Point Y ITM",
    "שם דוגם",
    "מזהה נקודת ניטור",
    "Sent/ Received at Sheba",
    "Date mosquitoes homogenized",
    "Date RNA extracted",
    "Date of TaqMan",
    "Result RT-PCR (Lin1+2)",
]

# Blue columns: always empty (header only)
BLUE_COLUMNS = {
    "Sent/ Received at Sheba",
    "Date mosquitoes homogenized",
    "Date RNA extracted",
    "Date of TaqMan",
    "Result RT-PCR (Lin1+2)",
}


def read_csv(file_bytes: bytes) -> tuple[list[str], list[dict]]:
    """Read CSV bytes and return (headers, rows_as_dicts)."""
    text = file_bytes.decode("utf-8-sig")  # handles optional BOM
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    headers = reader.fieldnames or []
    return headers, rows


def build_xlsx(rows: list[dict]) -> bytes:
    """Build the XLSX file in memory and return bytes."""
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})
    ws = wb.add_worksheet("Sheet1")

    fmt_yellow = wb.add_format({
        "bold": True, "bg_color": "#FFD700", "font_color": "#000000",
        "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True,
    })
    fmt_blue = wb.add_format({
        "bold": True, "bg_color": "#4472C4", "font_color": "#FFFFFF",
        "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True,
    })
    fmt_cell = wb.add_format({"valign": "vcenter", "border": 1})

    ws.set_row(0, 36)

    for col_idx, col_name in enumerate(OUTPUT_COLUMNS):
        fmt = fmt_blue if col_name in BLUE_COLUMNS else fmt_yellow
        ws.write(0, col_idx, col_name, fmt)
        ws.set_column(col_idx, col_idx, max(len(col_name) * 1.3, 14))

    for row_idx, row in enumerate(rows, start=1):
        mapped = {final: row.get(csv_col, "") for csv_col, final in RENAME_MAP.items()}
        for col_idx, col_name in enumerate(OUTPUT_COLUMNS):
            value = "" if col_name in BLUE_COLUMNS else mapped.get(col_name, "")
            ws.write(row_idx, col_idx, value, fmt_cell)

    wb.close()
    return output.getvalue()


# ── Streamlit UI ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CSV → Template RUN",
    page_icon="🦟",
    layout="centered",
)

st.markdown("""
    <style>
        .block-container { max-width: 720px; }
        h1 { font-size: 1.6rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🦟 CSV → Template RUN")
st.caption("Converts the system CSV export to the TEMPLATE FOR RUN format")

uploaded = st.file_uploader(
    "Drop the CSV file exported from the system",
    type=["csv"],
    help="File of the type SitesVisitsSamples2021_....csv",
)

if uploaded:
    try:
        raw_bytes = uploaded.read()
        headers, rows = read_csv(raw_bytes)

        known   = set(RENAME_MAP.keys())
        found   = known & set(headers)
        missing = known - set(headers)

        col1, col2 = st.columns(2)
        col1.metric("Rows detected", len(rows))
        col2.metric("Columns mapped", f"{len(found)} / {len(RENAME_MAP)}")

        if missing:
            st.warning(f"Expected columns not found in CSV: {', '.join(missing)}")

        with st.spinner("Generating Excel file…"):
            xlsx_bytes = build_xlsx(rows)

        # Output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_name  = f"sending_file_template_{timestamp}.xlsx"

        st.success(f"✅ File ready — {len(rows)} rows, {len(OUTPUT_COLUMNS)} columns")

        st.download_button(
            label="⬇️ Download Excel file",
            data=xlsx_bytes,
            file_name=out_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )

    except Exception as e:
        st.error(f"Error while processing: {e}")
        st.exception(e)
else:
    st.info("👆 Upload a CSV file to get started")

with st.expander("ℹ️ Column mapping"):
    st.markdown("**Renamed columns (yellow)**")
    for src, dst in RENAME_MAP.items():
        if src != dst:
            st.markdown(f"- `{src}` → `{dst}`")
    st.markdown("**Empty columns added (blue)**")
    for col in sorted(BLUE_COLUMNS):
        st.markdown(f"- `{col}`")
    st.markdown("**Columns dropped from CSV**")
    st.markdown("- `OBJECTID`, `GlobalID`, `מזהה קופסה`, `שם בודק`")