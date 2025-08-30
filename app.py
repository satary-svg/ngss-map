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

df4, df6, df7, df9, df10 = load_data()
df_all = pd.concat([df4, df6, df7, df9, df10], ignore_index=True)

# --- Normalize NGSS Practice names ---
df_all["NGSS Practice"] = df_all["NGSS Practice"].astype(str).str.extract(r"(NGSS \d+)")

st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")

with st.sidebar:
    st.header("Filters")
    grades = st.multiselect(
        "Grade(s)", 
        ["4th", "6th", "7th", "9th", "10th"], 
        default=["4th", "6th", "7th", "9th", "10th"]
    )
    practices = sorted(df_all["NGSS Practice"].dropna().unique())
    practice = st.selectbox("NGSS Practice", practices, index=0)

# --- Filter dataset ---
mask = (df_all["Grade"].isin(grades)) & (df_all["NGSS Practice"] == practice)
filtered = df_all[mask].copy()

if not filtered.empty:
    # Extract just the unit codes like "A0", "A1", etc.
    filtered["Unit Code"] = filtered["Unit"].str.extract(r"(A\d+)")

    # Pivot into Grades × Unit Codes
    pivot = filtered.pivot_table(
        index="Grade",
        columns="Unit Code",
        values="Activity/Assessment",
        aggfunc=lambda x: ", ".join(sorted(set(x)))
    ).fillna("")

    # Sort columns in natural numeric order
    def sort_key(col):
        match = re.search(r"A(\d+)", str(col))
        return int(match.group(1)) if match else 999
    pivot = pivot[sorted(pivot.columns, key=sort_key)]

    st.subheader("Results (Assignments by Grade and Unit)")
    st.dataframe(pivot, use_container_width=True)

    # Download option
    csv = pivot.to_csv().encode("utf-8")
    st.download_button(
        "Download table as CSV",
        csv,
        file_name="ngss_comparison.csv",
        mime="text/csv"
    )

else:
    st.info("No matches found for this practice in the selected grade(s).")
