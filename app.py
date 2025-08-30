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

st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")

with st.sidebar:
    st.header("Filters")
    grades = st.multiselect(
        "Grade(s)", 
        ["4th", "6th", "7th", "9th", "10th"], 
        default=["4th", "6th", "7th", "9th", "10th"]
    )
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
        m
