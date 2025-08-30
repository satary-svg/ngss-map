import os
import re
import glob
import pandas as pd
import streamlit as st

st.set_page_config(page_title="NGSS Practices Map (Grades 4–10)", layout="wide")
st.title("📘 NGSS Practices Map (Grades 4–10)")

DATA_DIR = "data"
GRADE_ORDER = ["4th", "6th", "7th", "9th", "10th"]
UNIT_COL_ORDER = [f"A{i}" for i in range(7)]  # A0..A6

# ---------- helpers ----------
def normalize_unit(value: str):
    """
    Make 'A1', 'UA1', 'Unit A1', 'A 1' → 'A1'.
    Return None if we can't recognize it (column will be blank).
    """
    if pd.isna(value):
        return None
    s = str(value).strip()
    # Look for optional 'U' before A, optional spaces, and a single digit 0-6
    m = re.search(r"\bU?\s*A\s*([0-6])\b", s, flags=re.IGNORECASE)
    if m:
        return f"A{m.group(1)}"
    # Fallback: direct 'A0..A6' inside longer text
    m = re.search(r"\bA([0-6])\b", s, flags=re.IGNORECASE)
    if m:
        return f"A{m.group(1)}"
    return None


def bullet_join(items):
    # Turn a sequence into HTML bullet list (clean & compact).
    cleaned = [str(x).strip() for x in items if str(x).strip() and str(x).strip() != "nan"]
    if not cleaned:
        return "–"
    if len(cleaned) == 1:
        return cleaned[0]
    bullets = "".join(f"<li>{c}</li>" for c in cleaned)
    return f"<ul style='margin:0 0 0 1rem;padding:0'>{bullets}</ul>"


# ---------- load ----------
csvs = sorted(glob.glob(os.path.join(DATA_DIR, "*_database.csv")))
if not csvs:
    st.error("No CSV files found in the `data/` directory.")
    st.stop()

frames = []
for path in csvs:
    grade = os.path.basename(path).split("_")[0]  # "4th", "10th", etc.
    try:
        df = pd.read_csv(path)
    except Exception as e:
        st.error(f"Failed to read {path}: {e}")
        st.stop()

    # Required columns check (be forgiving with capitalization)
    cols = {c.lower(): c for c in df.columns}
    required = ["unit_number", "unit_title", "ngss_number", "ngss_description"]
    for r in required:
        if r not in cols:
            st.error(f"Missing column `{r}` in {os.path.basename(path)}.")
            st.stop()

    df = df.rename(columns={cols["unit_number"]: "Unit_Number",
                            cols["unit_title"]: "Unit_Title",
                            cols["ngss_number"]: "NGSS_Number",
                            cols["ngss_description"]: "NGSS_Description"})

    # Normalize unit labels to A0..A6
    df["Unit_Number"] = df["Unit_Number"].apply(normalize_unit)

    # Attach grade
    df["Grade"] = grade

    # A single content string for the chosen practice
    df["Content"] = "**" + df["Unit_Title"].astype(str) + "**<br>" + df["NGSS_Description"].astype(str)
    frames.append(df)

df_all = pd.concat(frames, ignore_index=True)

# ---------- UI: choose practice ----------
practice_options = (
    df_all["NGSS_Number"].astype(str).str.strip() + ": " + df_all["NGSS_Description"].str.strip()
)
# Keep first occurrence text per NGSS_Number to avoid giant duplicates in dropdown
# (many rows share the same practice text)
first_per_number = (
    df_all.drop_duplicates(subset=["NGSS_Number"])  # one row per number
    .assign(option=lambda d: d["NGSS_Number"].astype(str).str.strip() + ": " + d["NGSS_Description"].str.strip())
    .sort_values("NGSS_Number")
)
selected = st.selectbox(
    "NGSS Practice",
    first_per_number["option"].tolist()
)
selected_number = selected.split(":")[0].strip()

# ---------- filter by practice & build table ----------
filtered = df_all[df_all["NGSS_Number"].astype(str).str.strip() == selected_number].copy()

# Keep only valid A0..A6 rows
filtered["Unit_Number"] = filtered["Unit_Number"].where(filtered["Unit_Number"].isin(UNIT_COL_ORDER))
filtered = filtered.dropna(subset=["Unit_Number"])

if filtered.empty:
    st.warning("No matches for this practice.")
    st.stop()

# Aggregate to a single cell per (Grade, Unit_Number)
agg = (
    filtered
    .groupby(["Grade", "Unit_Number"], as_index=False)["Content"]
    .agg(lambda s: bullet_join(s))
)

# Pivot to Grade rows x A0..A6 columns
table = (
    agg.pivot(index="Grade", columns="Unit_Number", values="Content")
    .reindex(UNIT_COL_ORDER, axis=1)  # ensure columns A0..A6
    .reindex(GRADE_ORDER, axis=0)     # ensure grade order 4th→10th
)

# Replace NaN with en-dash for display
table = table.fillna("–")

# Ensure columns exist for any missing A0..A6
for col in UNIT_COL_ORDER:
    if col not in table.columns:
        table[col] = "–"

# Final tidy layout: Grade first, then A0..A6
table = table.reset_index()[["Grade"] + UNIT_COL_ORDER]

st.markdown(f"### Results for {selected}")
st.write(table.to_html(escape=False, index=False), unsafe_allow_html=True)
