import streamlit as st
import pandas as pd
import re
import glob
import os

st.set_page_config(layout="wide")

st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")

# --- Load all CSVs ---
data_files = glob.glob("data/*_database.csv")
all_dfs = []

for file in data_files:
    grade = os.path.basename(file).split("_")[0]
    df = pd.read_csv(file)
    df["Grade"] = grade
    all_dfs.append(df)

df_all = pd.concat(all_dfs, ignore_index=True)

# --- Unique practices (sorted) ---
unique_practices = sorted(
    df_all["NGSS Practice"].dropna().unique(),
    key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 999
)

# --- Sidebar filters ---
st.sidebar.header("Filters")

grades = st.sidebar.multiselect(
    "Grade(s)",
    options=sorted(df_all["Grade"].unique(), key=lambda x: int(re.sub(r"\D", "", x))),
    default=sorted(df_all["Grade"].unique(), key=lambda x: int(re.sub(r"\D", "", x))),
)

practice = st.sidebar.selectbox("NGSS Practice", unique_practices)

# --- Filtered dataframe ---
mask = (df_all["Grade"].isin(grades)) & (df_all["NGSS Practice"] == practice)
filtered = df_all[mask]

st.subheader(f"Results for {practice}")

if not filtered.empty:
    # Pivot table: rows=Grade, cols=Unit, values=Assignments
    pivot = filtered.pivot_table(
        index="Grade", 
        columns="Unit Code", 
        values="Assignment Title", 
        aggfunc=lambda x: list(x),
        fill_value=""
    )

    # --- Format cells ---
    formatted = pivot.copy()
    for col in formatted.columns:
        new_col = []
        for grade in formatted.index:
            items = formatted.loc[grade, col]
            if isinstance(items, list) and items:
                # Clean unit title (remove A# prefix)
                unit_clean = re.sub(r"^A\d+:\s*", "", str(col))
                unit_header = f"<b><u>{unit_clean}</u></b>"
                cell_text = unit_header + "<br>" + "<br>".join(items)
            else:
                cell_text = ""
            new_col.append(cell_text)
        formatted[col] = new_col

    # --- Ensure chronological order of rows ---
    formatted.index = pd.Categorical(
        formatted.index,
        categories=sorted(df_all["Grade"].unique(), key=lambda x: int(re.sub(r"\D", "", x))),
        ordered=True
    )
    formatted = formatted.sort_index()

    # --- Remove redundant Unit Code col if present ---
    if "Unit Code" in formatted.columns:
        formatted = formatted.drop(columns=["Unit Code"])

    # Reset index for display
    formatted.reset_index(inplace=True)
    formatted.rename(columns={"Grade": "Grade"}, inplace=True)

    # Display HTML table with custom formatting
    st.write(
        formatted.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )

    # CSV download
    csv = formatted.to_csv(index=False)
    st.download_button(
        "Download table as CSV",
        data=csv,
        file_name="ngss_practice_map.csv",
        mime="text/csv"
    )

else:
    st.info("No data available for this selection.")
