import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")

# -------------------------------
# Load all grade CSVs
# -------------------------------
files = {
    "4th": "4th_database.csv",
    "6th": "6th_database.csv",
    "7th": "7th_database.csv",
    "9th": "9th_database.csv",
    "10th": "10th_database.csv",
}

dfs = []
for grade, file in files.items():
    df = pd.read_csv(file)
    df["Grade"] = grade
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

# -------------------------------
# Clean Unit fields
# -------------------------------
# Split "A1: Thermodynamics" → Unit Code = "A1", Unit Title = "Thermodynamics"
df_all["Unit Code"] = df_all["Unit"].str.extract(r"(A\d+)")
df_all["Unit Title"] = df_all["Unit"].str.replace(r"A\d+:\s*", "", regex=True)

# -------------------------------
# Sidebar Filters
# -------------------------------
grades = sorted(df_all["Grade"].unique(), key=lambda x: int(re.sub(r"\D", "", x)))
selected_grades = st.sidebar.multiselect("Grade(s)", grades, default=grades)

practices = sorted(df_all["NGSS Practice"].unique(), key=lambda x: int(re.search(r"NGSS (\d+)", x).group(1)))
selected_practice = st.sidebar.selectbox("NGSS Practice", practices)

# -------------------------------
# Filter data
# -------------------------------
filtered = df_all[(df_all["Grade"].isin(selected_grades)) & (df_all["NGSS Practice"] == selected_practice)]

# Build formatted content for each cell
filtered["Cell Content"] = (
    "<b><u>" + filtered["Unit Title"] + "</u></b><br>" +
    filtered["Activity/Assessment"].fillna("").str.replace(",", "<br>")
)

# -------------------------------
# Pivot Table
# -------------------------------
pivot = filtered.pivot_table(
    index="Grade",
    columns="Unit Code",
    values="Cell Content",
    aggfunc=lambda x: "<br><br>".join(str(v) for v in x if pd.notna(v)),
    fill_value=""
)

# Ensure chronological grade order in rows
grade_order = ["4th", "6th", "7th", "9th", "10th"]
pivot = pivot.reindex(grade_order)

# Sort unit columns numerically (A0, A1, A2, …)
pivot = pivot.reindex(sorted(pivot.columns, key=lambda x: int(x[1:])), axis=1)

# -------------------------------
# Display Table
# -------------------------------
st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")
st.subheader(f"Results for {selected_practice}")

# Apply formatting
styler = pivot.style.set_properties(**{
    "text-align": "left",
    "vertical-align": "top",
    "white-space": "pre-wrap"
})

# Display HTML-styled table
st.markdown(styler.to_html(), unsafe_allow_html=True)

# -------------------------------
# CSV Download
# -------------------------------
csv = pivot.to_csv().encode("utf-8")
st.download_button("Download table as CSV", csv, "ngss_map.csv", "text/csv")
