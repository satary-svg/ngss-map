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

# Sort NGSS practices by number for dropdown (all in one line now!)
unique_practices = sorted(df_all["NGSS Practice"].dropna().unique(),
                          key=lambda x: int(re.search(r"NGS
