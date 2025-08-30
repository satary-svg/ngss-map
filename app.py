import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(page_title="NGSS Practices Map (Grades 4–10)", layout="wide")

st.title("📘 NGSS Practices Map (Grades 4–10)")

# -------------------
# Load CSVs
# -------------------
data_files = glob.glob(os.path.join("data", "*.csv"))

if not data_files:
    st.error("No CSV files found in `data/` directory.")
    st.stop()

df_list = []
for f in data_files:
    try:
        df_temp = pd.read_csv(f)
        df_list.append(df_temp)
    except Exception as e:
        st.warning(f"Could not read {f}: {e}")

df_all = pd.concat(df_list, ignore_index=True)

# -------------------
# Define grade + unit order
# -------------------
GRADE_ORDER = ["4th", "5th", "6th", "7th", "8th", "9th", "10th"]
UNIT_COL_ORDER = ["A0", "A1", "A2", "A3", "A4", "A5", "A6"]

# -------------------
# NGSS Practice Mapping
# -------------------
practice_map = {
    "1": "Asking questions and defining problems",
    "2": "Developing and using models",
    "3": "Planning and carrying out investigations",
    "4": "Analyzing and interpreting data",
    "5": "Using mathematical and computational thinking",
    "6": "Constructing explanations and designing solutions",
    "7": "Engaging in argument from evidence",
    "8": "Obtaining, evaluating, and communicating information",
}

practice_options = [f"{k}: {v}" for k, v in practice_map.items()]

# -------------------
# User Selection
# -------------------
selected_practice = st.selectbox("NGSS Practice", practice_options)
selected_number = selected_practice.split(":")[0].strip()

# -------------------
# Filter and Pivot
# -------------------
filtered = df_all[df_all["NGSS_Number"].astype(str) == selected_number].copy()

# Format content: bold Unit Title, then bullet points
filtered["Content"] = (
    "**" + filtered["Unit_Title"] + "**<br>• " +
    filtered["NGSS_Description"].str.replace(";", "<br>• ")
)

# Build pivot: Grade x Unit_Number
pivot = (
    filtered
    .pivot_table(index="Grade", columns="Unit_Number", values="Content",
                 aggfunc=lambda x: "<br>• ".join(str(i) for i in x))
    .reindex(columns=UNIT_COL_ORDER)   # Force column order
    .reindex(GRADE_ORDER)              # Force grade order
    .fillna("–")
)

# Reset index for display
pivot = pivot.reset_index()[["Grade"] + UNIT_COL_ORDER]

# -------------------
# Display
# -------------------
st.markdown(f"### Results for {selected_practice}")

st.write(
    pivot.to_html(escape=False, index=False).replace("<br>", "<br>"),
    unsafe_allow_html=True
)
