import streamlit as st
import pandas as pd
import glob

st.set_page_config(page_title="NGSS Practices Map", layout="wide")

# Load all CSVs
files = glob.glob("data/*.csv")
dfs = []
for f in files:
    df = pd.read_csv(f)
    grade = f.split("/")[-1].split(".")[0]  # e.g., "10th"
    df["Grade"] = grade
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

# --- Clean Unit column ---
# Separate unit code (A1, A2...) and title
df_all[["Unit Code", "Unit Title"]] = df_all["Unit"].str.split(":", n=1, expand=True)
df_all["Unit Title"] = df_all["Unit Title"].str.strip()

# --- Sidebar filters ---
grades = sorted(df_all["Grade"].unique(), key=lambda x: int(x.replace("th", "").replace("th", "").replace("th", "")))
selected_grades = st.sidebar.multiselect("Grade(s)", grades, default=grades)

practices = sorted(df_all["NGSS Practice"].unique())
selected_practice = st.sidebar.selectbox("NGSS Practice", practices)

# --- Filter ---
filtered = df_all[
    (df_all["Grade"].isin(selected_grades)) &
    (df_all["NGSS Practice"] == selected_practice)
]

# --- Build pivot table ---
filtered["Cell Content"] = (
    "<b><u>" + filtered["Unit Title"] + "</u></b><br>" +
    filtered["Activity/Assessment"].fillna("")
)

pivot = filtered.pivot_table(
    index="Grade",
    columns="Unit Code",
    values="Cell Content",
    aggfunc=lambda x: "<br><br>".join(x),
    fill_value=""
)

# Ensure consistent column order (A0–A6)
ordered_cols = [f"A{i}" for i in range(7)]
pivot = pivot.reindex(columns=ordered_cols, fill_value="")

# Reset index for display
df_display_html = pivot.reset_index()

# --- Style ---
styler = (
    df_display_html.style
    .format(escape=False)
    .set_properties(**{
        "white-space": "pre-wrap",
        "vertical-align": "top",
        "line-height": "1.5",
        "font-size": "15px",
        "padding": "10px"
    })
    .set_table_styles([
        {"selector": "th",
         "props": [("text-align", "center"),
                   ("font-size", "15px"),
                   ("font-weight", "bold")]}
    ])
)

# --- Page ---
st.title("NGSS Practices Map (Grades 4, 6, 7, 9, 10)")
st.subheader(f"Results for {selected_practice}")

# Render as HTML
html_table = styler.to_html()
st.markdown(html_table, unsafe_allow_html=True)
