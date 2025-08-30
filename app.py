import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="📘 NGSS Practices Map (Grades 4–10)", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# Load all CSVs from /data
csv_files = glob.glob("data/*.csv")

if not csv_files:
    st.error("No CSV files found in working directory.")
else:
    dfs = []
    for file in csv_files:
        grade = os.path.basename(file).split("_")[0]  # e.g. "7th"
        df = pd.read_csv(file)
        df["Grade"] = grade
        dfs.append(df)

    # Combine all grade DataFrames
    df_all = pd.concat(dfs, ignore_index=True)

    # NGSS Practices list
    df_all["NGSS"] = df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
    ngss_practices = df_all["NGSS"].unique()

    # Sidebar filter
    selected_ngss = st.sidebar.selectbox("NGSS Practice", sorted(ngss_practices))

    # Filter data for the selected NGSS Practice
    ngss_number = selected_ngss.split(":")[0]
    df_filtered = df_all[df_all["NGSS_Number"].astype(str) == ngss_number]

    if df_filtered.empty:
        st.warning("No data found for this NGSS practice.")
    else:
        st.subheader(f"Results for {selected_ngss}")

        # 🔹 Get ALL possible Unit_Numbers across all grades (A0, A1, A2, etc.)
        all_units = sorted(df_all["Unit_Number"].unique(), key=lambda x: int(x[1:]))

        # Pivot only current filter, but keep all units
        pivot_df = df_filtered.pivot_table(
            index="Grade",
            columns="Unit_Number",
            values=["Unit_Title", "Activity"],
            aggfunc=lambda x: " | ".join([str(i) for i in x if pd.notna(i)]),
            fill_value="-"
        )

        # Build merged table with bold Unit_Title + Activity on new line
        merged = {}
        for unit in all_units:
            if unit in pivot_df["Unit_Title"].columns:
                merged[unit] = (
                    "<b>" + pivot_df["Unit_Title"][unit].replace("-", "").fillna("-") + "</b>"
                    + "<br><span style='font-size:12px;'>" 
                    + pivot_df["Activity"][unit].fillna("-") + "</span>"
                )
            else:
                merged[unit] = "-"

        result_df = pd.DataFrame(merged, index=pivot_df.index).reset_index()

        # 🔹 Order grades correctly
        grade_order = ["4th", "5th", "6th", "7th", "8th", "9th", "10th"]
        result_df["Grade"] = pd.Categorical(result_df["Grade"], categories=grade_order, ordered=True)
        result_df = result_df.sort_values("Grade")

        # Display with HTML rendering
        st.write(
            result_df.to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
