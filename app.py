import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="NGSS Practices Map", layout="wide")

st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")

# -------------------
# Load CSVs
# -------------------
data_files = {
    "4th": "data/4th_database.csv",
    "6th": "data/6th_database.csv",
    "7th": "data/7th_database.csv",
    "9th": "data/9th_database.csv",
    "10th": "data/10th_database.csv",
}

dfs = []
for grade, file in data_files.items():
    if os.path.exists(file):
        df = pd.read_csv(file)
        df["Grade"] = grade
        dfs.append(df)
    else:
        st.warning(f"⚠️ Missing file for {grade} (upload or place {file} in working directory)")

if not dfs:
    st.stop()

df_all = pd.concat(dfs, ignore_index=True)

# -------------------
# Sidebar Filters
# -------------------
st.sidebar.header("Filters")

# NGSS Practices dropdown (show full names)
practices = sorted(df_all["NGSS Practice"].dropna().unique())
selected_practice = st.sidebar.selectbox("NGSS Practice", practices, format_func=lambda x: str(x))

# Grades multiselect
all_grades = ["4th", "6th", "7th", "9th", "10th"]
selected_grades = st.sidebar.multiselect("Grade(s)", all_grades, default=all_grades)

# -------------------
# Filter Data
# -------------------
filtered = df_all[
    (df_all["NGSS Practice"] == selected_practice)
    & (df_all["Grade"].isin(selected_grades))
].copy()

# Ensure grades always appear in order
filtered["Grade"] = pd.Categorical(filtered["Grade"], categories=all_grades, ordered=True)

# -------------------
# Pivot Table
# -------------------
pivot = filtered.pivot_table(
    index="Grade",
    columns="Unit",
    values="Activity/Assessment",
    aggfunc=lambda x: "<br>".join(sorted(set(x))),
    fill_value="-"
)

# Reset index to show "Grade" as column
pivot = pivot.reset_index()

# -------------------
# Display Results
# -------------------
st.subheader(f"Results for {selected_practice}")

# Apply styling
def highlight_units(val):
    if val != "-" and isinstance(val, str):
        parts = val.split("<br>", 1)
        unit = f"<b><u>{parts[0]}</u></b>"
        rest = "<br>".join(parts[1:]) if len(parts) > 1 else ""
        return f"{unit}<br>{rest}"
    return "-"

styled = pivot.style.format(highlight_units, escape="html")

st.write(styled.to_html(escape=False), unsafe_allow_html=True)
