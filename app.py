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

    # --- Create Unit Display (Unit Title bold + Activities bulleted) ---
    def make_display(unit_title, activity):
        if pd.isna(unit_title) and pd.isna(activity):
            return "-"
        title = f"**{unit_title}**" if pd.notna(unit_title) else ""
        if pd.notna(activity):
            acts = [a.strip() for a in str(activity).split(",")]
            acts_fmt = "<br>".join([f"• {a}" for a in acts])
            return f"{title}<br>{acts_fmt}"
        return title

    df_filtered["Unit_Display"] = df_filtered.apply(
        lambda row: make_display(row["Unit_Title"], row["Activity"]), axis=1
    )

    # --- Pivot ---
    pivot_df = df_filtered.pivot_table(
        index="Grade",
        columns="Unit_Number",
        values="Unit_Display",
        aggfunc=lambda x: "<br>".join(x)
    ).fillna("-")

    # --- Ensure all units A0–A6 are present ---
    all_units = [f"A{i}" for i in range(7)]
    pivot_df = pivot_df.reindex(columns=all_units, fill_value="-")

    formatted_df = pivot_df.reset_index()

    # --- Display ---
    st.subheader(f"Results for {selected_practice}")
    st.write(
        formatted_df.to_html(escape=False, index=False),
        unsafe_allow_html=True
    )
