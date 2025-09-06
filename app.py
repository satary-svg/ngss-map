import os
import pandas as pd
import streamlit as st

# ---------- App config ----------
st.set_page_config(page_title="NGSS Map (Practices 1–5)", layout="wide")

st.markdown(
    "<h1 style='margin-bottom:0.25rem;'>NGSS Practices Map (K–12 Prototype)</h1>"
    "<div style='color:#6b7280;margin-bottom:1rem;'>Select a practice and see which assignments address it, by grade.</div>",
    unsafe_allow_html=True,
)

# ---------- Paths / Practice metadata ----------
DATA_DIR = "data"

PRACTICES = {
    "NGSS 1 — Asking questions & defining problems": {
        "key": "ngss1",
        "file": "NGSS1_Asking_Questions.csv",
        "desc": "Practice 1"
    },
    "NGSS 2 — Developing & using models": {
        "key": "ngss2",
        "file": "NGSS_2_Developing_and_Using_Models.csv",
        "desc": "Practice 2"
    },
    "NGSS 3 — Planning & carrying out investigations": {
        "key": "ngss3",
        "file": "NGSS3_Planning_Investigations.csv",
        "desc": "Practice 3"
    },
    "NGSS 4 — Analyzing & interpreting data": {
        "key": "ngss4",
        "file": "NGSS_4_Analyzing_and_Interpreting_Data.csv",
        "desc": "Practice 4"
    },
    "NGSS 5 — Using mathematical & computational thinking": {
        "key": "ngss5",
        "file": "NGSS_5_Using_Mathematical_and_Computational_Thinking.csv",
        "desc": "Practice 5"
    },
}

ASSIGNMENT_COLUMNS = ["A0", "A1", "A2", "A3", "A4", "A5", "A6"]
GRADE_ORDER = ["4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th"]


# ---------- Helpers ----------
@st.cache_data(show_spinner=False)
def load_practice_df(filename: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path, dtype=str).fillna("-")
    # Keep only expected columns in the intended order if present
    cols = ["Grade"] + [c for c in ASSIGNMENT_COLUMNS if c in df.columns]
    df = df[[c for c in cols if c in df.columns]]
    # sort grades by our natural order (missing grades go to bottom)
    df["__order"] = df["Grade"].apply(lambda g: GRADE_ORDER.index(g) if g in GRADE_ORDER else 999)
    df = df.sort_values("__order").drop(columns="__order")
    return df

def md_cell(text: str) -> str:
    """
    Format a cell: keep bold titles, convert bullets/newlines to <br>,
    render '-' as an en dash, and escape nothing else (assuming CSV already safe).
    """
    if not isinstance(text, str) or text.strip() == "" or text.strip() == "-":
        return "<span style='color:#9ca3af;'>–</span>"
    # Replace newline or \n with <br> for wrapping
    html = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    html = html.replace("\n", "<br>")
    return html

def render_table_html(df: pd.DataFrame) -> str:
    """
    Build an HTML table with sticky headers and nice wrapping. 
    Rows = Grades, Cols = A0..A6.
    """
    # Ensure we have all columns; if not, add empties
    for col in ASSIGNMENT_COLUMNS:
        if col not in df.columns:
            df[col] = "-"

    # Reorder columns
    df = df[["Grade"] + ASSIGNMENT_COLUMNS]

    # Build header
    thead = (
        "<thead>"
        "<tr>"
        "<th style='position:sticky;left:0;z-index:2;background:#f9fafb;border-right:1px solid #e5e7eb;'>Grade</th>"
        + "".join(
            f"<th>{col}</th>" for col in ASSIGNMENT_COLUMNS
        )
        + "</tr>"
        "</thead>"
    )

    # Build body
    body_rows = []
    for _, row in df.iterrows():
        cells = []
        # sticky first column
        grade_html = f"<td style='position:sticky;left:0;z-index:1;background:#fff;border-right:1px solid #e5e7eb;font-weight:600;'>{row['Grade']}</td>"
        cells.append(grade_html)
        for col in ASSIGNMENT_COLUMNS:
            content = md_cell(row[col])
            # Unit title already bolded in CSV with **...**; make sure Markdown-like ** is rendered as bold.
            # Convert **bold** to <u><b>bold</b></u> for extra emphasis per earlier preference
            content = content.replace("**", "")  # strip markdown stars
            # Add a little top padding to look like "title on top, bullets below"
            cell_html = (
                "<div style='line-height:1.25;'>"
                f"<div style='font-weight:600;text-decoration:underline;margin-bottom:0.25rem;'>"
                f"{content.split('<br>')[0] if '<br>' in content else content}"
                f"</div>"
            )
            # Remainder lines as bullet list (if any)
            if "<br>" in content:
                parts = content.split("<br>")
                title = parts[0]
                rest = parts[1:]
                # Make bullets for lines that already begin with • or "-"
                bullet_items = []
                for ln in rest:
                    ln_stripped = ln.strip()
                    if ln_stripped in ["", "–"]:
                        continue
                    # ensure bullet dot
                    if ln_stripped.startswith("•"):
                        bullet_items.append(f"<li>{ln_stripped[1:].strip()}</li>")
                    elif ln_stripped.startswith("- "):
                        bullet_items.append(f"<li>{ln_stripped[2:].strip()}</li>")
                    else:
                        bullet_items.append(f"<li>{ln_stripped}</li>")
                if bullet_items:
                    cell_html += f"<ul style='margin:0 0 0.25rem 1rem;padding:0;'>{''.join(bullet_items)}</ul>"
            cell_html += "</div>"
            cells.append(f"<td>{cell_html}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    tbody = "<tbody>" + "".join(body_rows) + "</tbody>"

    # Full table
    table_html = f"""
    <div style="overflow:auto;border:1px solid #e5e7eb;border-radius:12px;">
      <table style="
            border-collapse:separate;
            border-spacing:0;
            width:100%;
            min-width:900px;
            table-layout:fixed;
      ">
        <style>
          table th, table td {{
            border-bottom:1px solid #e5e7eb;
            vertical-align:top;
            padding:10px 12px;
            word-wrap:break-word;
            overflow-wrap:break-word;
            white-space:normal;
          }}
          thead th {{
            position:sticky; top:0; z-index:1;
            background:#f9fafb;
            font-weight:600;
            text-align:left;
          }}
        </style>
        {thead}
        {tbody}
      </table>
    </div>
    """
    return table_html


# ---------- Sidebar controls ----------
with st.sidebar:
    st.markdown("### Choose NGSS Practice")
    practice_label = st.selectbox(
        "Practice",
        list(PRACTICES.keys()),
        index=0,
    )
    st.markdown("---")
    st.markdown("### Filter Grades")
    selected_grades = st.multiselect(
        "Grades to include",
        options=GRADE_ORDER,
        default=GRADE_ORDER,  # show all by default, 4th first
    )
    st.markdown("---")
    st.markdown("### About")
    st.caption(
        "This prototype displays which **assignments (A0–A6)** address each NGSS practice.\n"
        "Cells show the **unit title** (bold/underlined) and **activities** as bullets."
    )

# ---------- Load & filter ----------
meta = PRACTICES[practice_label]
df = load_practice_df(meta["file"])

if selected_grades:
    df = df[df["Grade"].isin(selected_grades)]
else:
    st.info("No grades selected. Choose at least one grade in the sidebar to view the table.")

# ---------- Render table ----------
if not df.empty and selected_grades:
    st.markdown(
        f"<h3 style='margin:0.25rem 0 0.5rem 0;'>{practice_label}</h3>",
        unsafe_allow_html=True,
    )
    html = render_table_html(df)
    st.markdown(html, unsafe_allow_html=True)

    # ---------- Download current view ----------
    # Provide a clean CSV of the filtered view (no HTML)
    export_df = df.copy()
    st.download_button(
        label="Download this view as CSV",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{meta['key']}_filtered_view.csv",
        mime="text/csv",
        help="Exports the current table (selected grades) as CSV."
    )
else:
    st.warning("No data to display for the current selection.")
