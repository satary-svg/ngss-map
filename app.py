import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="NGSS Practices Map", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# --- Load all CSV files from data/ directory ---
data_files = glob.glob("data/*.csv")

if not data_files:
    st.error("No CSV files found in `data/` directory.")
else:
    # Read and combine all CSVs
    dfs = []
    for file in data_files:
        try:
            df = pd.read_csv(file)
            grade = os.path.basename(file).split("_")[0]  # e.g., "4th"
            df["Grade"] = grade
            dfs.append(df)
        except Exception as e:
            st.error(f"Error reading {file}: {e}")
    if not dfs:
        st.error("No valid CSV data loaded.")
    else:
        df_all = pd.concat(dfs, ignore_index=True)

        # --- Define grade order ---
        grade_order = ["4th", "6th", "7th", "9th", "10th"]
        df_all["Grade"] = pd.Categorical(df_all["Grade"], categories=grade_order, ordered=True)

        # --- Dropdown for NGSS Practice ---
        ngss_practices = df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
        selected_practice = st.selectbox("NGSS Practice", sorted(ngss_practices.unique()))

        # --- Filter Data ---
        practice_number = selected_practice.split(":")[0]
        df_filtered = df_all[df_all["NGSS_Number"].astype(str) == practice_number]

        # Create display text (Unit Title in bold + activity indented)
        df_filtered["Unit_Display"] = df_filtered.apply(
            lambda row: f"**{row['Unit_Title']}**<br>{row['Activity']}" if pd.notna(row['Activity']) else f"**{row['Unit_Title']}**",
            axis=1
        )

        # --- Pivot for table view ---
        pivot_df = df_filtered.pivot_table(
            index="Grade",
            columns="Unit_Number",
            values="Unit_Display",
            aggfunc=lambda x: "<br>".join(x)
        ).fillna("-")

        # --- Ensure all units A0–A6 are present ---
        all_units = [f"A{i}" for i in range(7)]
        pivot_df = pivot_df.reindex(columns=all_units, fill_value="-")

        # --- Reapply grade order ---
        pivot_df = pivot_df.reindex(grade_order)

        # --- Reset index for clean display ---
        formatted_df = pivot_df.reset_index()

        # --- Show results ---
        st.subheader(f"Results for {selected_practice}")
        st.write(formatted_df.to_html(escape=False, index=False), unsafe_allow_html=True)
