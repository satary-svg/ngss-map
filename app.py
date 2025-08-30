import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="NGSS Practices Map", layout="wide")

st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")

# -------- Load all CSVs --------
data_dir = "data"
csv_files = {
    "4th": "4th_database.csv",
    "6th": "6th_database.csv",
    "7th": "7th_database.csv",
    "9th": "9th_database.csv",
    "10th": "10th_database.csv"
}

dfs = []
for grade, file in csv_files.items():
    path = os.path.join(data_dir, file)
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["Grade"] = grade
        dfs.append(df)
    else:
        st.warning(f"⚠️ Missing file for {grade} (upload or place {file} in working directory)")

if not dfs:
    st.stop()

df_all = pd.concat(dfs, ignore_index=True)

# -------- Clean NGSS Practices --------
df_all["NGSS Practice"] = df_all["NGSS Practice"].apply(
    lambda x: x if isinstance(x, str) and ":" in x else None
)
df_all = df_all.dropna(subset=["NGSS Practice"])

# Dropdown options
ngss_practices = sorted(df_all["NGSS Practice"].unique())
selected_practice = st.selectbox("NGSS Practice", ngss_practices)

# -------- Filter Data --------
filtered = df_all[df_all["NGSS Practice"] == selected_practice]

if filtered.empty:
    st.info("No activities found for this practice.")
    st.stop()

# -------- Pivot to Table --------
aggfunc = lambda x: "<br>".join(x.dropna().astype(str))

pivot = filtered.pivot_table(
    index="Grade",
    columns="Unit",
    values="Activity/Assessment",
    aggfunc=aggfunc,
    fill_value=""
)

# Reorder grades chronologically
grade_order = ["4th", "6th", "7th", "9th", "10th"]
pivot = pivot.reindex(grade_order)

# -------- Clean up cells (remove "nan", remove unit names) --------
styled = pivot.copy()

for col in styled.columns:
    styled[col] = styled[col].apply(
        lambda x: x.replace("nan", "").strip() if isinstance(x, str) else ""
    )

# -------- Display --------
st.subheader(f"Results for {selected_practice}")

# Add custom CSS for taller cells
st.markdown(
    
    <style>
    table {
        border-collapse: collapse;
        width: 100%;
    }
    th, td {
        border: 1px solid #ddd
