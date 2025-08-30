import streamlit as st
import pandas as pd
import glob
import os

# Set page config
st.set_page_config(page_title="📘 NGSS Practices Map (Grades 4–10)", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# --- Load all CSVs from /data ---
csv_files = glob.glob(os.path.join("data", "*.csv"))

if not csv_files:
    st.error("❌ No CSV files found in `data/` directory.")
else:
    dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            st.error(f"Error reading {file}: {e}")

    if dfs:
        # Combine into single dataframe
        df_all = pd.concat(dfs, ignore_index=True)

        # Dropdown: NGSS Practice (Number + Description)
        df_all["NGSS_Full"] = df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
        ngss_options = df_all["NGSS_Full"].unique()

        selected_ngss = st.selectbox("NGSS Practice", sorted(ngss_options))

        # Filter for selected NGSS
        ngss_number = selected_ngss.split(":")[0].strip()
        df_filtered = df_all[df_all["NGSS_Number"].astype(str) == ngss_number]

        if df_filtered.empty:
            st.warning(f"No data found for {selected_ngss}")
        else:
            # Create unique Unit headers: "A1: Skeletal System"
            df_filtered["Unit_Header"] = df_filtered["Unit_Number"].astype(str) + ": " + df_filtered["Unit_Title"]

            # Pivot to wide format
            pivot_df = df_filtered.pivot_table(
                index="Grade",
                columns="Unit_Header",
                values="Activity",
                aggfunc=lambda x: " | ".join([str(i) for i in x if pd.notna(i)]),
                fill_value="-"
            ).reset_index()

            # Sort grades properly (4th, 6th, 7th, 9th, 10th)
            grade_order = ["4th", "6th", "7th", "9th", "10th"]
            pivot_df["Grade"] = pd.Categorical(pivot_df["Grade"], categories=grade_order, ordered=True)
            pivot_df = pivot_df.sort_values("Grade")

            st.subheader(f"Results for {selected_ngss}")
            st.dataframe(pivot_df, use_container_width=True)

    else:
        st.error("❌ No valid CSV data could be loaded.")
