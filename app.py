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

        # Pivot table: columns = Unit_Number, values = Unit_Title + Activity
        pivot_df = df_filtered.pivot_table(
            index="Grade",
            columns="Unit_Number",
            values=["Unit_Title", "Activity"],
            aggfunc=lambda x: " | ".join([str(i) for i in x if pd.notna(i)]),
            fill_value="-"
        )

        # Merge Unit_Title + Activity into one cell, header only A0, A1...
        new_cols = []
        for col in pivot_df.columns.levels[1]:  # iterate over each Unit_Number
            pivot_df[(col)] = pivot_df["Unit_Title"][col] + ": " + pivot_df["Activity"][col]
            new_cols.append(col)

        pivot_df = pivot_df[new_cols].reset_index()

        # Clean up NaNs and formatting
        pivot_df = pivot_df.replace({
            "nan: nan": "-",
            "nan": "-",
            ": -": "-",
            "-:": "-"
        })

        # Display
        st.dataframe(pivot_df, use_container_width=True)
