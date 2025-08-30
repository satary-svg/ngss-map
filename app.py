import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="NGSS Practices Map (Grades 4–10)", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# --- Load all CSVs ---
data_files = glob.glob("data/*_database.csv")

if not data_files:
    st.error("No CSV files found in the `data/` directory.")
else:
    dfs = []
    for file in data_files:
        grade = os.path.basename(file).split("_")[0]  # e.g. "4th", "10th"
        df = pd.read_csv(file)

        # Normalize Unit_Number (strip titles, keep A0–A6 only)
        df["Unit_Number"] = df["Unit_Number"].str.extract(r"(A\d+)")

        # Combine Unit_Title + NGSS_Description
        df["Content"] = "**" + df["Unit_Title"].astype(str) + "**<br>" + df["NGSS_Description"].astype(str)

        # Add grade column
        df["Grade"] = grade
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)

    # Dropdown for NGSS practices
    practices = df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
    unique_practices = practices.unique()
    selected_practice = st.selectbox("NGSS Practice", sorted(unique_practices))

    # Filter
    ngss_number = selected_practice.split(":")[0]
    filtered = df_all[df_all["NGSS_Number"].astype(str) == ngss_number]

    if filtered.empty:
        st.warning("No data available for this practice.")
    else:
        # Pivot: rows = Grade, cols = A0–A6, values = Content
        pivot = filtered.pivot_table(
            index="Grade", columns="Unit_Number", values="Content", 
            aggfunc=lambda x: "<br>".join(x)
        ).fillna("-")

        # Reorder grades
        grade_order = ["4th", "6th", "7th", "9th", "10th"]
        pivot = pivot.reindex(grade_order)

        # Reorder columns A0–A6
        unit_order = [f"A{i}" for i in range(7)]
        pivot = pivot.reindex(columns=unit_order)

        # Reset index to show Grade as column
        pivot.reset_index(inplace=True)

        st.markdown(f"### Results for {selected_practice}")
        st.write(
            pivot.to_html(escape=False, index=False), 
            unsafe_allow_html=True
        )
