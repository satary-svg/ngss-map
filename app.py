import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="NGSS Practices Map", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# --- Load all CSVs ---
csv_files = glob.glob("*.csv")
if not csv_files:
    st.error("No CSV files found in working directory.")
    st.stop()

dfs = []
for file in csv_files:
    grade = file.split("_")[0]  # e.g., "4th", "6th"
    df = pd.read_csv(file)
    df["Grade"] = grade
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

# --- Ensure clean column names ---
df_all.columns = [c.strip() for c in df_all.columns]

# --- Dropdown options (NGSS Practice Numbers + Descriptions) ---
ngss_practices = (
    df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
).unique()
ngss_practices = sorted(ngss_practices, key=lambda x: int(x.split(":")[0]))

selected_ngss = st.selectbox("NGSS Practice", ngss_practices)

# Extract selected NGSS number
selected_number = selected_ngss.split(":")[0].strip()

# --- Filter dataframe ---
filtered = df_all[df_all["NGSS_Number"].astype(str) == selected_number]

# --- Map Unit_Number → Unit_Title ---
unit_map = (
    filtered[["Unit_Number", "Unit_Title"]]
    .drop_duplicates()
    .set_index("Unit_Number")["Unit_Title"]
    .to_dict()
)

# --- Ensure consistent unit order ---
unit_order = (
    filtered[["Unit_Number", "Unit_Title"]]
    .drop_duplicates()
    .sort_values("Unit_Number")
)

# --- Pivot table (aggregate multiple activities per grade+unit) ---
pivot = filtered.pivot_table(
    index="Grade",
    columns="Unit_Number",
    values="Activity",
    aggfunc=lambda x: "<br>".join(
        sorted(set(str(v) for v in x if pd.notna(v)))
    ),
    fill_value="-",
)

# Reorder columns to match unit order
pivot = pivot.reindex(columns=unit_order["Unit_Number"], fill_value="-")

# Rename columns → "A#: <b>Unit_Title</b>"
pivot.rename(
    columns=lambda x: f"{x}: <b>{unit_map.get(x, '')}</b>",
    inplace=True,
)

# --- Ensure grade order ---
grade_order = ["4th", "6th", "7th", "9th", "10th"]
pivot = pivot.reindex(grade_order)

# --- Display table ---
st.subheader(f"Results for {selected_ngss}")
st.write(pivot.to_html(escape=False, index=True), unsafe_allow_html=True)
