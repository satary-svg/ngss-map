import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="NGSS Practices Map (7th & 9th)", layout="wide")

@st.cache_data
def load_data():
    df7 = pd.read_csv("data/7th_database.csv")
    df9 = pd.read_csv("data/9th_database.csv")
    return df7, df9

df7, df9 = load_data()
df_all = pd.concat([df7, df9], ignore_index=True)

st.title("NGSS Practices Map (7th & 9th Grade)")

with st.sidebar:
    st.header("Filters")
    grades = st.multiselect("Grade(s)", ["7th", "9th"], default=["7th", "9th"])
    practices = sorted(df_all["NGSS Practice"].unique())
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
    st.download_button("Download table as CSV", csv, file_name="ngss_comparison.csv", mime="text/csv")

else:
    st.info("No matches found for this practice in the selected grade(s).")
