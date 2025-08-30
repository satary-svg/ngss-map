# app.py
import re
import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="NGSS Practices Map", layout="wide")

# -----------------------------
# Helpers
# -----------------------------
GRADE_ORDER = ["4th", "6th", "7th", "9th", "10th"]

def load_grade_csv(grade_label: str, path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Grade"] = grade_label

    # Normalize columns
    cols = {c.lower(): c for c in df.columns}

    # Activity column
    activity_col = next((cols[c] for c in ["activity/assessment","activity","assignment","task"] if c in cols), df.columns[-1])

    # Unit column
    unit_col = next((cols[c] for c in ["unit","unit name","unit_title"] if c in cols), df.columns[1])

    # Practice column
    practice_col = next((cols[c] for c in ["ngss practice","ngss","practice"] if c in cols), df.columns[0])

    df = df.rename(columns={practice_col:"NGSS Practice", unit_col:"Unit", activity_col:"Activity"})

    # Clean strings
    for c in ["NGSS Practice","Unit","Activity"]:
        df[c] = df[c].astype(str).fillna("").str.strip()

    # Split Unit into UnitCode + UnitTitle
    unit_code, unit_title = [], []
    for u in df["Unit"]:
        u = u if isinstance(u, str) else ""
        m = re.match(r"^\s*(A\d+)\s*:?\s*(.*)$", u)
        if m:
            unit_code.append(m.group(1))
            unit_title.append(m.group(2).strip())
        else:
            m2 = re.search(r"(A\d+)", u)
            unit_code.append(m2.group(1) if m2 else "")
            title = re.sub(r"^\s*(A\d+)\s*:?\s*", "", u).strip()
            unit_title.append(title)
    df["UnitCode"] = unit_code
    df["UnitTitle"] = unit_title
    return df[["Grade","NGSS Practice","UnitCode","UnitTitle","Activity"]]

def natural_unit_sort(codes):
    def keyfn(x):
        try:
            return int(x[1:])  # A12 -> 12
        except:
            return 10_000
    return sorted(codes, key=keyfn)

def dedupe_keep_order(items):
    seen, out = set(), []
    for i in items:
        i = (i or "").strip()
        if i and i not in seen:
            seen.add(i)
            out.append(i)
    return out

def make_cell_html(title, activities):
    """Show unit title (bold/underlined), then each activity on its own line."""
    acts = "<br>".join(activities) if activities else ""
    if title and acts:
        return f"<div class='unit'><u><b>{title}</b></u></div>{acts}"
    elif title:
        return f"<div class='unit'><u><b>{title}</b></u></div>"
    else:
        return acts

def cell_plaintext(title, activities):
    lines = []
    if title: lines.append(title)
    lines.extend(activities)
    return "\n".join(lines)

# -----------------------------
# Load data
# -----------------------------
dfs = []
files = [
    ("4th","data/4th_database.csv"),
    ("6th","data/6th_database.csv"),
    ("7th","data/7th_database.csv"),
    ("9th","data/9th_database.csv"),
    ("10th","data/10th_database.csv"),
]
for grade_label,path in files:
    try:
        dfs.append(load_grade_csv(grade_label,path))
    except Exception as e:
        st.warning(f"Could not load {path}: {e}")

df_all = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame(columns=["Grade","NGSS Practice","UnitCode","UnitTitle","Activity"])

if df_all.empty:
    st.error("No data loaded. Please check CSV files.")
    st.stop()

df_all["Grade"] = pd.Categorical(df_all["Grade"], categories=GRADE_ORDER, ordered=True)

# -----------------------------
# UI
# -----------------------------
st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")

with st.sidebar:
    st.header("Filters")
    grades = st.multiselect("Grade(s)", options=GRADE_ORDER, default=GRADE_ORDER)
    practices = sorted(df_all["NGSS Practice"].dropna().unique().tolist())
    practice = st.selectbox("NGSS Practice", options=practices, index=0)

if not grades:
    st.info("Select at least one grade.")
    st.stop()

st.subheader(f"Results for {practice}")

# -----------------------------
# Filtered data
# -----------------------------
filtered = df_all[(df_all["Grade"].isin(grades)) & (df_all["NGSS Practice"]==practice)].copy()
unit_codes = natural_unit_sort(filtered["UnitCode"].dropna().unique().tolist())

# Cell mapping per Grade + UnitCode
cell_html_map, cell_plain_map = {}, {}
for (g,uc),grp in filtered.groupby(["Grade","UnitCode"], dropna=False):
    titles = [t for t in grp["UnitTitle"] if t and t.lower()!="nan"]
    unit_title = titles[0] if titles else ""
    acts = dedupe_keep_order([a for a in grp["Activity"] if a and a.lower()!="nan"])
    cell_html_map[(g,uc)] = make_cell_html(unit_title, acts)
    cell_plain_map[(g,uc)] = cell_plaintext(unit_title, acts)

# Build display df
rows_html, rows_plain = [], []
for g in sorted(grades, key=lambda x: GRADE_ORDER.index(x)):
    row_h, row_p = {"Grade": f"**{g}**"}, {"Grade": g}
    for uc in unit_codes:
        row_h[uc] = cell_html_map.get((g,uc),"")
        row_p[uc] = cell_plain_map.get((g,uc),"")
    rows_html.append(row_h)
    rows_plain.append(row_p)

df_display_html = pd.DataFrame(rows_html).set_index("Grade")
df_display_plain = pd.DataFrame(rows_plain).set_index("Grade")

# Style
styler = (
    df_display_html.style
    .format(escape=False)
    .set_properties(**{"white-space":"pre-wrap","vertical-align":"top","line-height":"1.4","font-size":"15px","padding":"10px"})
    .set_table_styles([{"selector":"th","props":[("text-align","center"),("font-size","15px")]}])
)

# Render
st.write(styler)

# -----------------------------
# CSV download
# -----------------------------
csv_buf = io.StringIO()
df_display_plain.to_csv(csv_buf)
st.download_button("Download table as CSV", data=csv_buf.getvalue().encode("utf-8"), file_name="ngss_practices_map.csv", mime="text/csv")
