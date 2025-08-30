import streamlit as st
import pandas as pd
import glob
import re

st.set_page_config(page_title="NGSS Practices Map", layout="wide")

st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")

# --- Load all CSVs ---
all_files = glob.glob("data/*_database.csv")
df_list = []

for file in all_files:
    grade = re.search(r"(\d+)th", file).group(1) + "th"
    df = pd.read_csv(file)
    df["Grade"] = grade
    df_list.append(df)

df_all = pd.concat(df_list, ignore_index=True)

# --- Sidebar filters ---
st.sidebar.header("Filters")

grades = st.sidebar.multiselect(
    "Grade(s)",
    options=sorted(df_all["Grade"].unique(), key=lambda x: int(re.search(r"\d+", x).group())),
    default=sorted(df_all["Grade"].unique(), key=lambda x: int(re.search(r"\d+", x).group()))
)

# Build practice list
unique_practices = sorted(df_all["NGSS Practice"].unique(),
                          key=lambda x: int(re.search(r"NGSS (\d+)", x).group(1)) if re.search(r"NGSS (\d+)", x) else 999)

practice = st.sidebar.selectbox("NGSS Practice", options=unique_practices)

# --- Filter data ---
filtered = df_all[(df_all["Grade"].isin(grades)) & (df_all["NGSS Practice"] == practice)].copy()

# Clean up Unit column (remove A#:)
filtered["Unit_clean"] = filtered["Unit"].str.replace(r"^A\d+:\s*", "", regex=True)

# --- Pivot table ---
pivot = filtered.pivot_table(
    index="Grade",
    columns="Unit",
    values="Activity/Assessment",
    aggfunc=lambda x: "<br>".join(x),
    fill_value=""
)

# --- Format cells ---
def format_cell(unit, activities):
    if isinstance(activities, str) and activities.strip():
        return f"<b><u>{re.sub(r'^A\\d+:\\s*', '', unit)}</u></b><br>{activities}"
    return ""

pivot = pivot.apply(lambda col: [format_cell(col.name, val) for val in col])

# Reset index so Grade shows
pivot.reset_index(inplace=True)

# --- Display ---
st.subheader(f"Results for {practice}")
st.write(
    pivot.to_html(escape=False, index=False),
    unsafe_allow_html=True
)

# --- Download button ---
csv = pivot.to_csv(index=False)
st.download_button("Download table as CSV", csv, "ngss_results.csv", "text/csv")
