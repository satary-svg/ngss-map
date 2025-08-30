import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="📘 NGSS Practices Map (Grades 4–10)", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# 🔎 Look for CSV files anywhere in repo
csv_files = glob.glob("**/*_database.csv", recursive=True)

if not csv_files:
    st.error("No CSV files found in working directory.")
else:
    # Load all CSVs
    dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df["Grade"] = os.path.basename(file).split("_")[0]  # e.g., "4th"
            dfs.append(df)
        except Exception as e:
            st.error(f"❌ Error reading {file}: {e}")

    if dfs:
        df_all = pd.concat(dfs, ignore_index=True)

        # ✅ Expected columns
        expected_cols = ["NGSS_Number", "NGSS_Description", "Unit_Number", "Unit_Title", "Activity"]
        if not all(c in df_all.columns for c in expected_cols):
            st.error(f"CSV missing required columns. Found: {df_all.columns.tolist()}")
        else:
            # NGSS dropdown
            ngss_practices = (
                df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
            ).unique()
            selected_ngss = st.sidebar.selectbox("NGSS Practice", sorted(ngss_practices))
            selected_number = selected_ngss.split(":")[0].strip()

            # Filter dataframe
            filtered = df_all[df_all["NGSS_Number"].astype(str) == selected_number]

            # Build master unit order (all A0, A1, A2... across all grades)
            unit_order = (
                df_all[["Unit_Number", "Unit_Title"]]
                .drop_duplicates()
                .sort_values("Unit_Number")
            )
            unit_map = dict(zip(unit_order["Unit_Number"], unit_order["Unit_Title"]))

            # Pivot by grade
            pivot = filtered.pivot_table(
                index="Grade",
                columns="Unit_Number",
                values="Activity",
                aggfunc=lambda x: "<br>".join(str(v) for v in x if pd.notna(v)),
                fill_value="-",
            )

            # Ensure all units appear (even if blank)
            pivot = pivot.reindex(columns=unit_order["Unit_Number"], fill_value="-")

            # Rename columns → "A#: Unit_Title"
            pivot.rename(columns=lambda x: f"{x}: {unit_map.get(x, '')}", inplace=True)

            # Sort grades properly
            grade_order = ["4th", "6th", "7th", "9th", "10th"]
            pivot = pivot.reindex(grade_order)

            # Show table
            st.subheader(f"Results for {selected_ngss}")
            st.write(pivot.to_html(escape=False, index=True), unsafe_allow_html=True)
