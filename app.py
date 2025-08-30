import streamlit as st
import pandas as pd
import glob
import os
import re

st.set_page_config(page_title="NGSS Practices Map (Grades 4–10)", layout="wide")
st.title("📘 NGSS Practices Map (Grades 4–10)")

DATA_DIR = "data"
GRADE_ORDER = ["4th", "6th", "7th", "9th", "10th"]
UNIT_COLUMNS = [f"A{i}" for i in range(7)]  # A0..A6

# ---------- helpers ----------
def normalize_unit_number(x: str) -> str | None:
    """Coerce anything like 'a2', 'A 02', '2' → 'A2' (only 0–6 kept)."""
    if pd.isna(x):
        return None
    s = str(x).strip().upper()
    m = re.search(r"(\d+)", s)
    if not m:
        return None
    n = int(m.group(1))
    if 0 <= n <= 6:
        return f"A{n}"
    return None

def normalize_ngss_number(x: str) -> str | None:
    """Coerce '2', 'Practice 2', 'NGSS 2' → '2'."""
    if pd.isna(x):
        return None
    s = str(x)
    m = re.search(r"(\d+)", s)
    return m.group(1) if m else None

def pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find a column by relaxed matching among candidates."""
    norm = {re.sub(r"[^a-z0-9]+", "", c.lower()): c for c in df.columns}
    for c in candidates:
        key = re.sub(r"[^a-z0-9]+", "", c.lower())
        if key in norm:
            return norm[key]
    return None

# ---------- load all CSVs ----------
files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
if not files:
    st.error(f"No CSV files found in `{DATA_DIR}/`.")
    st.stop()

all_rows = []
for path in files:
    try:
        df = pd.read_csv(path)

        # Try to map flexible column names to canonical ones
        col_unitnum = pick_col(df, ["Unit_Number", "Unit #", "UnitNumber", "Unit"])
        col_unittitle = pick_col(df, ["Unit_Title", "Unit Title", "UnitName", "Unit_Name"])
        col_activity = pick_col(df, ["Activity", "Activities", "Task", "Tasks", "Notes"])
        col_ngssnum = pick_col(df, ["NGSS_Number", "NGSS Practice", "NGSS_Practice", "NGSS"])
        col_ngssdesc = pick_col(df, ["NGSS_Description", "NGSS Description", "Practice_Description"])

        # Minimal required: Unit_Number, Unit_Title, NGSS_Number
        for need, col in {
            "Unit_Number": col_unitnum,
            "Unit_Title": col_unittitle,
            "NGSS_Number": col_ngssnum,
        }.items():
            if col is None:
                st.error(f"{os.path.basename(path)} is missing a '{need}' column (or recognizable variant).")
                st.stop()

        df_out = pd.DataFrame({
            "Grade": os.path.basename(path).split("_")[0],  # e.g., 4th_database.csv
            "Unit_Number": df[col_unitnum],
            "Unit_Title": df[col_unittitle],
            "NGSS_Number": df[col_ngssnum],
            "NGSS_Description": df[col_ngssdesc] if col_ngssdesc else "",
            "Activity": df[col_activity] if col_activity else "",
        })

        all_rows.append(df_out)

    except Exception as e:
        st.error(f"Error reading {os.path.basename(path)}: {e}")
        st.stop()

df_all = pd.concat(all_rows, ignore_index=True)

# Grade order
df_all["Grade"] = pd.Categorical(df_all["Grade"], categories=GRADE_ORDER, ordered=True)

# Normalize keys
df_all["Unit_Number"] = df_all["Unit_Number"].apply(normalize_unit_number)
df_all["NGSS_Number"] = df_all["NGSS_Number"].apply(normalize_ngss_number)

# Build practice selector text
df_all["NGSS_Description"] = df_all["NGSS_Description"].fillna("")
practice_labels = (
    df_all["NGSS_Number"].fillna("").astype(str).str.strip() + ": " +
    df_all["NGSS_Description"].fillna("").astype(str).str.strip()
)
# Keep unique, sorted by numeric NGSS_Number then description
unique_practices = (
    df_all.assign(_label=practice_labels)
          .dropna(subset=["NGSS_Number"])
          .sort_values(by=["NGSS_Number", "NGSS_Description"])
          [["_label"]]
          .drop_duplicates()
          ["_label"]
          .tolist()
)

selected = st.selectbox("NGSS Practice", unique_practices)
sel_num = re.search(r"^(\d+)", selected).group(1)

df_sel = df_all[df_all["NGSS_Number"] == sel_num].copy()

# Display text: **Unit Title** + Activity (if present)
def make_cell(row):
    title = (row["Unit_Title"] or "").strip()
    act = (row["Activity"] or "").strip()
    if title and act:
        return f"**{title}**<br>{act}"
    elif title:
        return f"**{title}**"
    elif act:
        return act
    return "-"

df_sel["Cell"] = df_sel.apply(make_cell, axis=1)

# Pivot to A0..A6 columns
pivot = (
    df_sel.pivot_table(
        index="Grade",
        columns="Unit_Number",
        values="Cell",
        aggfunc=lambda s: "<br>".join([str(x) for x in s if pd.notna(x) and str(x).strip() != ""])
    )
    .reindex(columns=UNIT_COLUMNS)  # keep A0..A6 only and in order
    .fillna("-")
)

pivot = pivot.reindex(GRADE_ORDER)  # grade order
pivot = pivot.reset_index()

st.subheader(f"Results for {selected}")
st.write(pivot.to_html(escape=False, index=False), unsafe_allow_html=True)
