import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="NGSS Skills Map", layout="wide")

# Title
st.title("📘 NGSS Practices Map (Grades 4–10)")

# Load all CSVs
data_path = "data"
all_files = [
    "4th_database.csv",
    "6th_database.csv",
    "7th_database.csv",
    "9th_database.csv",
    "10th_database.csv"
]

dfs = []
for file in all_files:
    file_path = os.path.join(data_path, file)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        dfs.append(df)
    else:
        st.error(f"Missing file: {file}")

if not dfs:
    st.stop()

data = pd.concat(dfs, ignore_index=True)

# Ensure consistent ordering of grades
grade_order = ["4th", "6th", "7th", "9th", "10th"]
data["Grade"] = pd.Categorical(data["Grade"], categories=grade_order, ordered=True)

# Dropdown for NGSS practices (number + description)
data["NGSS Combined"] = data["NGSS Number"] + " - " + data["NGSS Description"]
skills = sorted(data["NGSS Combined"].unique())
selected_skill = st.selectbox("Select an NGSS Practice:", skills)

if selected_skill:
    # Filter data
    ngss_number, ngss_desc = selected_skill.split(" - ", 1)
    filtered = data[(data["NGSS Number"] == ngss_number) & 
                    (data["NGSS Description"] == ngss_desc)]

    # Pivot into table format
    pivot = filtered.pivot_table(
        index="Grade",
        columns="Unit Number",
        values=["Unit Title", "Activity"],
        aggfunc=lambda x: " | ".join([str(i) for i in x if pd.notna(i) and i != "-"]),
        fill_value="-"
    )

    # Flatten MultiIndex columns
    pivot.columns = [f"{col[1]}" for col in pivot.columns]

    # Format cells: bold+underline for Unit Title, line breaks for activities
    def format_cell(row, unit):
        title = row.get((unit), "-")
        # Look up the unit title from filtered data
        subset = filtered[(filtered["Grade"] == row.name) & (filtered["Unit Number"] == unit)]
        if subset.empty:
            return "-"
        unit_title = subset["Unit Title"].values[0]
        activity = subset["Activity"].values[0]
        if activity == "-" or pd.isna(activity):
            return f"**_{unit_title}_**"
        else:
            acts = [a.strip() for a in str(activity).split(";")]
            acts_str = "<br>".join(acts)
            return f"**<u>{unit_title}</u>**<br>{acts_str}"

    # Build final styled table
    final = pd.DataFrame(index=pivot.index)
    for unit in sorted(filtered["Unit Number"].unique(), key=lambda x: int(x[1:])):
        final[unit] = pivot.index.map(lambda grade: format_cell(filtered[filtered["Grade"] == grade], unit))

    # Show table with markdown rendering
    st.write("### NGSS Practice:", selected_skill)
    st.write("Rows = Grades | Columns = Units | Cells = Unit Title + Activities")

    st.write(final.to_html(escape=False), unsafe_allow_html=True)
