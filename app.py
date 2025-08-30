import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="📘 NGSS Practices Map (Grades 4–10)", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# 🔎 Look for all grade CSV files anywhere in the repo
csv_files = glob.glob("**/*_database.csv", recursive=True)

if not csv_files:
    st.error("No CSV files found in working directory.")
else:
    # Load all CSVs into one DataFrame
    dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df["Grade"] = os.path.basename(file).split("_")[0]  # e.g., "4th", "6th"
            dfs.append(df)
        except Exception as e:
            st.error(f"❌ Error reading {file}: {e}")

    if dfs:
        df_all = pd.concat(dfs, ignore_index=True)

        # ✅ Ensure consistent column names
        expected_cols = ["NGSS_Number", "NGSS_Description", "Unit_Number", "Unit_Title", "Activity"]
        missing_cols = [c for c in expected_cols if c not in df_all.columns]
        if missing_cols:
            st.error(f"Missing expected columns in CSVs: {missing_cols}")
        else:
            # Build NGSS dropdown list
            ngss_practices = (
                df_all["NGSS_Number"].astype(str) + ": " + df_all["NGSS_Description"]
            ).unique()

            selected_ngss = st.sidebar.selectbox("NGSS Practice", sorted(ngss_practices))

            # Extract number and description
            selected_number = selected_ngss.split(":")[0].strip()

            # Filter dataframe
            filtered = df_all[df_all["NGSS_Number"].astype(str) == selected_number]

            # Pivot: Grades as rows, Units as columns
            pivot = filtered.pivot_table(
                index="Grade",
                columns="Unit_Number",
                values="Activity",
                aggfunc=lambda x: "<br>".join(str(v) for v in x if pd.notna(v)),
                fill_value="-",
            )

            # Sort columns by Unit_Number (A0, A1, etc.)
            pivot = pivot.reindex(sorted(pivot.columns, key=lambda x: (x[0], x[1:])), axis=1)

            # Rename columns to "A#: Unit_Title"
            unit_titles = (
                filtered.drop_duplicates(subset=["Unit_Number", "Unit_Title"])
                .set_index("Unit_Number")["Unit_Title"]
                .to_dict()
            )
            pivot.rename(columns=lambda x: f"{x}: {unit_titles.get(x, '')}", inplace=True)

            # Show results
            st.subheader(f"Results for {selected_ngss}")
            st.write(
                pivot.to_html(escape=False, index=True),
                unsafe_allow_html=True,
            )
