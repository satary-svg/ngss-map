import streamlit as st
import pandas as pd
import os

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="NGSS Practices Map", layout="wide")
st.title("📘 NGSS Practices Map (Grades 4–10)")

# CSVs are now stored inside /data folder
DATA_DIR = "data"

GRADE_FILES = {
    "4th": "4th_database.csv",
    "6th": "6th_database.csv",
    "7th": "7th_database.csv",
    "9th": "9th_database.csv",
    "10th": "10th_database.csv"
}

# -----------------------------
# Load Data
# -----------------------------
all_dfs = []
missing = []

for grade, filename in GRADE_FILES.items():
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df["Grade"] = grade
        all_dfs.append(df)
    else:
        missing.append(grade)

if missing:
    st.warning(f"⚠️ Missing files for: {', '.join(missing)}")

if not all_dfs:
    st.error("❌ No data available. Please upload CSVs into the /data folder.")
    st.stop()

df_all = pd.concat(all_dfs, ignore_index=True)

# -----------------------------
# Filters
# -----------------------------
ngss_practices = df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
ngss_practices = ngss_practices.unique().tolist()

selected_practice = st.selectbox("NGSS Practice", sorted(ngss_practices))

grades = st.multiselect(
    "Grade(s)",
    options=list(GRADE_FILES.keys()),
    default=list(GRADE_FILES.keys())
)

# -----------------------------
# Filtered Data
# -----------------------------
if selected_practice and grades:
    ngss_number = selected_practice.split(":")[0].strip()

    filtered = df_all[
        (df_all["NGSS_Number"].astype(str) == ngss_number)
        & (df_all["Grade"].isin(grades))
    ]

    if filtered.empty:
        st.info("ℹ️ No results for this NGSS practice and selected grades.")
    else:
        # Pivot so Units are columns, Grades are rows
        pivot = filtered.pivot_table(
            index="Grade",
            columns=["Unit_Number", "Unit_Title"],
            values="Activity",
            aggfunc=lambda x: "<br>".join([str(i) for i in x if i != "-"]),
            fill_value="-"
        )

        # Clean column names for display
        pivot.columns = [f"{u}: {t}" for u, t in pivot.columns]

        st.markdown(f"### Results for {selected_practice}")
        st.write(pivot.to_html(escape=False), unsafe_allow_html=True)
