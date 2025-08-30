import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="NGSS Practices Map (Grades 4–10)", layout="wide")
st.title("📘 NGSS Practices Map (Grades 4–10)")

DATA_DIR = "data"
GRADE_ORDER = ["4th", "6th", "7th", "9th", "10th"]
UNIT_COL_ORDER = [f"A{i}" for i in range(7)]  # A0..A6

# ---------- Load CSVs ----------
data_files = glob.glob(os.path.join(DATA_DIR, "*_database.csv"))

if not data_files:
    st.error("No CSV files found in the `data/` directory.")
    st.stop()

frames = []
for file in data_files:
    try:
        df = pd.read_csv(file)
        # Ensure correct columns
        required_cols = ["Unit_Number", "Unit_Title", "NGSS_Number", "NGSS_Description", "Grade"]
        for col in required_cols:
            if col not in df.columns:
                st.error(f"{file} is missing required column: {col}")
                st.stop()
        frames.append(df)
    except Exception as e:
        st.error(f"Error reading {file}: {e}")
        st.stop()

df_all = pd.concat(frames, ignore_index=True)

# ---------- Build Practice Selector ----------
df_all["NGSS_Number"] = df_all["NGSS_Number"].astype(str).str.strip()
df_all["NGSS_Description"] = df_all["NGSS_Description"].fillna("").astype(str).str.strip()

practice_options = (
    df_all["NGSS_Number"] + ": " + df_all["NGSS_Description"]
)

# Deduplicate practices (some rows repeat)
practice_options = sorted(practice_options.unique())

selected_practice = st.selectbox("NGSS Practice", practice_options)
selected_number = selected_practice.split(":")[0].strip()

# ---------- Filter by Selected Practice ----------
filtered = df_all[df_all["NGSS_Number"] == selected_number].copy()

# Build content for cells
filtered["Content"] = "**" + filtered["Unit_Title"] + "**<br>" + filtered["NGSS_Description"]

# ---------- Pivot ----------
pivot = (
    filtered
    .pivot_table(index="Grade", columns="Unit_Number", values="Content", aggfunc=lambda x: "<br>".join(x))
    .reindex(columns=UNIT_COL_ORDER)   # Ensure A0–A6 order
    .reindex(GRADE_ORDER)              # Ensure grade order
    .fillna("–")
)

# Ensure all missing columns exist
for col in UNIT_COL_ORDER:
    if col not in pivot.columns:
        pivot[col] = "–"

pivot = pivot.reset_index()[["Grade"] + UNIT_COL_ORDER]

# ---------- Display ----------
st.markdown(f"### Results for {selected_practice}")
st.write(pivot.to_html(escape=False, index=False), unsafe_allow_html=True)
