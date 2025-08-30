import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="NGSS Practices Map (Grades 4–10)", layout="wide")

@st.cache_data
def load_data():
    df4 = pd.read_csv("data/4th_database.csv")
    df6 = pd.read_csv("data/6th_database.csv")
    df7 = pd.read_csv("data/7th_database.csv")
    df9 = pd.read_csv("data/9th_database.csv")
    df10 = pd.read_csv("data/10th_database.csv")
    return df4, df6, df7, df9, df10

# Combine all grades into one DataFrame
df4, df6, df7, df9, df10 = load_data()
df_all = pd.concat([df4, df6, df7, df9, df10], ignore_index=True)

# Normalize NGSS practices
df_all["NGSS Practice"] = df_all["NGSS Practice"].astype(str).str.strip()

# Extract just the unit codes (A0, A1, …)
df_all["Unit Code"] = df_all["Unit"].str.extract(r"(A\d+)")

# --- Sort NGSS practices safely ---
def practice_sort_key(x):
    match = re.search(r"NGSS (\d+)", str(x))
    return int(match.group(1)) if match else 999

unique_practices = sorted(
    df_all["NGSS Practice"].dropna().unique(),
    key=practice_sort_key
)

# --- Build unified NGSS practice labels ---
practice_labels = []
for p in unique_practices:
    if ":" in p:
        practice_labels.append(p)
    else:
        match = df_all[df_all["NGSS Practice"].str.startswith(p)].iloc[0]["NGSS Practice"]
        practice_labels.append(match)

# Remove duplicates and sort again
practice_labels = sorted(set(practice_labels), key=practice_sort_key)

# --- UI ---
st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")

with st.sidebar:
    st.header("Filters")
    grades = st.multiselect(
        "Grade(s)",
        ["4th", "6th", "7th", "9th", "10th"],
        default=["4th", "6th", "7th", "9th", "10th"]
    )
    practice = st.selectbox("NGSS Practice", practice_labels, index=0)

# --- Filter dataset ---
mask = (df_all["Grade"].isin(grades)) & (df_all["NGSS Practice"].str.startswith(practice.split(":")[0]))
filtered = df_all[mask].copy()

if not filtered.empty:
    # Group by Grade + Unit so we can attach unit headers only once
    def format_cell(group):
        unit_title = group["Unit"].iloc[0]
        unit_code = group["Unit Code"].iloc[0]
        header = f"<b><u>{unit_code}: {unit_title}</u></b>"
        assignments = "<br>".join(group["Activity/Assessment"].dropna().unique())
        return f"{header}<br>{assignments}" if assignments else header

    formatted = filtered.groupby(["Grade", "Unit Code"]).apply(format_cell).reset_index()
    pivot = formatted.pivot(index="Grade", columns="Unit Code", values=0).fillna("")

    # Sort columns numerically by A#
    def sort_key(col):
        match = re.search(r"A(\d+)", str(col))
        return int(match.group(1)) if match else 999
    pivot = pivot[sorted(pivot.columns, key=sort_key)]

    st.subheader(f"Results for {practice}")

    # Render as HTML table so formatting works
    st.markdown(pivot.to_html(escape=False), unsafe_allow_html=True)

    # Download option (plain text, no HTML formatting)
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download raw data as CSV",
        csv,
        file_name="ngss_comparison_raw.csv",
        mime="text/csv"
    )

else:
    st.info("No matches found for this practice in the selected grade(s).")
