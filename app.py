import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="NGSS Practices Map", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# --- Load all CSV files from /data directory ---
data_files = glob.glob(os.path.join("data", "*_database.csv"))

if not data_files:
    st.error("No CSV files found in data/ directory.")
else:
    dfs = []
    for file in data_files:
        grade = os.path.basename(file).split("_")[0]  # e.g. "7th"
        df = pd.read_csv(file)
        df["Grade"] = grade
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)

    # --- Dropdown for NGSS Practices ---
    df_all["NGSS_Practice"] = df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
    practices = df_all["NGSS_Practice"].unique()
    selected_practice = st.selectbox("NGSS Practice", practices)

    # --- Filter data for selection ---
    num = selected_practice.split(":")[0]  # extract NGSS number (e.g. "1")
    df_filtered = df_all[df_all["NGSS_Number"].astype(str) == num]

    # --- Prepare pivot table ---
    # Combine unit number + title + activity
    df_filtered["Unit_Display"] = (
        df_filtered["Unit_Number"].astype(str) + ": " +
        df_filtered["Unit_Title"].fillna("") + "\n" +
        df_filtered["Activity"].fillna("")
    )

    pivot_df = df_filtered.pivot_table(
        index="Grade",
        columns="Unit_Number",
        values="Unit_Display",
        aggfunc=lambda x: " | ".join(x)
    ).fillna("-")

    # --- Ensure all A0–A6 appear ---
    all_units = [f"A{i}" for i in range(7)]
    pivot_df = pivot_df.reindex(columns=all_units, fill_value="-")

    # --- Format table (unit titles bold) ---
    def format_cell(cell):
        if cell == "-" or pd.isna(cell):
            return "-"
        parts = cell.split("\n", 1)
        if len(parts) == 2:
            return f"**{parts[0]}**\n{parts[1]}"
        else:
            return f"**{cell}**"

    formatted_df = pivot_df.applymap(format_cell).reset_index()

    # --- Display ---
    st.subheader(f"Results for {selected_practice}")
    st.dataframe(formatted_df, use_container_width=True)
