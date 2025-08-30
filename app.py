import streamlit as st
import pandas as pd
import glob
import re

# -------------------------
# Page setup
# -------------------------
st.set_page_config(page_title="NGSS Practices Map", layout="wide")
st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")

# -------------------------
# Load all CSVs
# -------------------------
all_files = glob.glob("data/*_database.csv")
if not all_files:
    st.error("No CSV files found in /data folder.")
    st.stop()

dfs = []
for f in all_files:
    grade_match = re.search(r"(\d+)th", f)
    if grade_match:
        grade = grade_match.group(1) + "th"
    else:
        grade = "Unknown"
    df = pd.read_csv(f)
    df["Grade"] = grade
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

# -------------------------
# Normalize NGSS Practice
# -------------------------
# Ensure dropdown only shows one option per NGSS code (take the longest descriptive version)
practice_map = {}
for p in df_all["NGSS Practice"].dropna().unique():
    code = p.split(":")[0].strip()  # "NGSS 1"
    if code not in practice_map or len(p) > len(practice_map[code]):
        practice_map[code] = p

# Dropdown options: use full description (longest one)
unique_practices = sorted(practice_map.values(), key=lambda x: int(re.search(r"\d+", x).group()))
practice_lookup = {v: k for k, v in practice_map.items()}  # reverse map

# -------------------------
# Sidebar filters
# -------------------------
grades = st.sidebar.multiselect(
    "Grade(s)",
    options=["4th", "6th", "7th", "9th", "10th"],
    default=["4th", "6th", "7th", "9th", "10th"]
)

practice_choice = st.sidebar.selectbox("NGSS Practice", unique_practices)

# -------------------------
# Filter Data
# -------------------------
practice_code = practice_lookup[practice_choice]
filtered = df_all[df_all["NGSS Practice"].str.startswith(practice_code)]

if grades:
    filtered = filtered[filtered["Grade"].isin(grades)]

# -------------------------
# Pivot table by grade/unit
# -------------------------
def clean_unit(unit):
    """Remove A# and return nice title"""
    return re.sub(r"^A\d+:\s*", "", str(unit)).strip()

# Add UnitCode for sorting columns chronologically
filtered["UnitCode"] = filtered["Unit"].str.extract(r"(A\d+)")

# Group activities per grade+unit
grouped = (
    filtered.groupby(["Grade", "UnitCode", "Unit"])
    ["Activity/Assessment"]
    .apply(lambda x: "<br>".join(x.dropna().unique()))
    .reset_index()
)

# Pivot into wide format
pivot = grouped.pivot_table(
    index="Grade",
    columns="UnitCode",
    values="Activity/Assessment",
    aggfunc=lambda x: " | ".join(x),
    fill_value=""
)

# Ensure unit order (A0–A6)
unit_order = sorted(pivot.columns, key=lambda x: int(x[1:]))
pivot = pivot[unit_order]

# Format cells: bold+underline unit title + line breaks
formatted = pd.DataFrame(index=pivot.index)
for col in pivot.columns:
    unit_name = clean_unit(grouped[grouped["UnitCode"] == col]["Unit"].iloc[0])
    formatted[col] = pivot[col].apply(
        lambda v: f"<b><u>{unit_name}</u></b><br>{v.replace('|', '<br>')}" if v else ""
    )

# Sort grades in chronological order
grade_order = {"4th": 4, "6th": 6, "7th": 7, "9th": 9, "10th": 10}
formatted = formatted.loc[sorted(formatted.index, key=lambda g: grade_order.get(g, 99))]

# -------------------------
# Show table
# -------------------------
st.subheader(f"Results for {practice_choice}")

st.write(
    formatted.to_html(escape=False),
    unsafe_allow_html=True
)

# Download option
csv = formatted.to_csv()
st.download_button("Download table as CSV", csv, "ngss_results.csv", "text/csv")
