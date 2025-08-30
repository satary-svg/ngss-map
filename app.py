import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="📘 NGSS Practices Map (Grades 4–10)", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# -------------------------------
# Load all CSV files
# -------------------------------
csv_files = glob.glob("*.csv")

if not csv_files:
    st.error("No CSV files found in working directory.")
    st.stop()

# Read and combine all CSVs
dfs = []
for file in csv_files:
    try:
        df = pd.read_csv(file)
        df["Grade"] = file.split("_")[0]  # Extract grade from filename
        dfs.append(df)
    except Exception as e:
        st.error(f"Error reading {file}: {e}")

df_all = pd.concat(dfs, ignore_index=True)

# -------------------------------
# Dropdowns for NGSS filter
# -------------------------------
if "NGSS_Number" not in df_all.columns or "NGSS_Description" not in df_all.columns:
    st.error("CSV files must contain 'NGSS_Number' and 'NGSS_Description' columns.")
    st.stop()

ngss_practices = (
    df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
).unique()

selected_practice = st.selectbox("NGSS Practice", sorted(ngss_practices))

selected_grades = st.multiselect(
    "Grade(s)",
    sorted(df_all["Grade"].unique(), key=lambda x: int(x.replace("th", ""))),
    default=sorted(df_all["Grade"].unique(), key=lambda x: int(x.replace("th", ""))),
)

# -------------------------------
# Filter dataset
# -------------------------------
ngss_num = selected_practice.split(":")[0].strip()

filtered = df_all[(df_all["NGSS_Number"].astype(str) == ngss_num) & (df_all["Grade"].isin(selected_grades))]

if filtered.empty:
    st.warning("No data available for this selection.")
    st.stop()

# -------------------------------
# Pivot table
# -------------------------------
pivot = filtered.pivot_table(
    index="Grade",
    columns=["Unit_Number", "Unit_Title"],
    values="Activity",
    aggfunc=lambda x: " | ".join(sorted(set([str(i) for i in x if pd.notna(i)]))),
    fill_value="-",
)

# Clean up headers: remove "U" and format as A0, A1…
pivot.columns = [
    f"{unit.replace('U', '')}: {title}" for unit, title in pivot.columns.to_list()
]

# Sort grade order
pivot = pivot.reindex(sorted(pivot.index, key=lambda x: int(x.replace("th", ""))))

# -------------------------------
# Display table
# -------------------------------
st.subheader(f"Results for {selected_practice}")
st.dataframe(pivot, use_container_width=True)
