import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="NGSS Practices Map (Grades 4–10)", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# --- Load all CSV files ---
csv_files = glob.glob("data/*_database.csv")  # Looks inside /data directory
if not csv_files:
    st.error("No CSV files found in the `data/` directory. Please upload them.")
    st.stop()

df_list = []
for file_path in csv_files:
    try:
        df = pd.read_csv(file_path)
        df_list.append(df)
    except Exception as e:
        st.error(f"Error reading {file_path}: {e}")

# Merge all data
df_all = pd.concat(df_list, ignore_index=True)

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# NGSS Practices dropdown
if "NGSS_Number" not in df_all.columns or "NGSS_Description" not in df_all.columns:
    st.error("CSV files must include columns: NGSS_Number and NGSS_Description")
    st.stop()

ngss_practices = (
    df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
).unique()
selected_practice = st.sidebar.selectbox("NGSS Practice", sorted(ngss_practices))

# Grades multiselect
grades = sorted(df_all["Grade"].unique())
selected_grades = st.sidebar.multiselect("Grade(s)", grades, default=grades)

# --- Filter Data ---
if selected_practice and selected_grades:
    # Separate practice into Number and Description
    selected_number = selected_practice.split(":")[0]

    filtered = df_all[
        (df_all["NGSS_Number"].astype(str) == selected_number)
        & (df_all["Grade"].isin(selected_grades))
    ]

    if filtered.empty:
        st.warning("No data available for this selection.")
    else:
        pivot = filtered.pivot_table(
            index="Grade",
            columns=["Unit_Number", "Unit_Title"],
            values="Activity",
            aggfunc=lambda x: "<br>".join([str(i) for i in x if pd.notna(i)]),
            fill_value="-",
        )

        # Make multiindex headers more readable
        pivot.columns = [
            f"U{unit}: {title}" for unit, title in pivot.columns.to_list()
        ]

        # Display table
        st.subheader(f"Results for {selected_practice}")
        st.write(
            pivot.to_html(escape=False).replace("\\n", "<br>"),
            unsafe_allow_html=True,
        )
else:
    st.info("Please select at least one NGSS Practice and one Grade.")
