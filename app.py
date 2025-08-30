import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

# -------- Load Data --------
@st.cache_data
def load_data():
    dfs = []
    grade_files = {
        "4th": "data/4th_database.csv",
        "6th": "data/6th_database.csv",
        "7th": "data/7th_database.csv",
        "9th": "data/9th_database.csv",
        "10th": "data/10th_database.csv"
    }

    for grade, file in grade_files.items():
        if os.path.exists(file):
            df = pd.read_csv(file)
            df["Grade"] = grade
            dfs.append(df)
        else:
            st.warning(f"⚠️ Missing file for {grade} (upload or place {file} in working directory)")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df_all = load_data()

# -------- Sidebar --------
st.sidebar.header("Filters")

# NGSS Practice dropdown (unique + sorted)
practices = sorted(df_all["NGSS Practice"].dropna().unique().tolist())
practice_labels = {p.split(":")[0]: p for p in practices}  # Map short NGSS # -> full text
selected_short = st.sidebar.selectbox("NGSS Practice", list(practice_labels.keys()))
selected_practice = practice_labels[selected_short]

# Grade selection
grades = sorted(df_all["Grade"].dropna().unique(), key=lambda x: int(x.replace("th", "").replace("th", "")))
selected_grades = st.sidebar.multiselect("Grade(s)", grades, default=grades)

# -------- Filter Data --------
filtered = df_all[(df_all["NGSS Practice"] == selected_practice) & (df_all["Grade"].isin(selected_grades))]

# -------- Pivot Data --------
if not filtered.empty:
    # Split Unit column into code + name
    filtered[["UnitCode", "UnitName"]] = filtered["Unit"].str.split(": ", n=1, expand=True)

    # Group assignments per Grade + Unit
    grouped = (
        filtered.groupby(["Grade", "UnitCode", "UnitName"])["Activity/Assessment"]
        .apply(lambda x: "<br>".join(x.dropna().astype(str)))
        .reset_index()
    )

    # Pivot so UnitCodes are columns
    pivot = grouped.pivot(index="Grade", columns="UnitCode", values="Activity/Assessment")

    # Attach unit names to column headers
    unit_names = grouped.drop_duplicates(subset=["UnitCode"])[["UnitCode", "UnitName"]].set_index("UnitCode")["UnitName"].to_dict()
    pivot.columns = [f"{u}: {unit_names.get(u, '')}" for u in pivot.columns]

    # Clean up display: bold + underline headers inside cells
    def format_cell(unit_name, content):
        if pd.isna(content) or content.strip() == "":
            return ""
        return f"<b><u>{unit_name}</u></b><br>{content}"

    for col in pivot.columns:
        unit_title = col.split(": ", 1)[1] if ": " in col else col
        pivot[col] = pivot[col].apply(lambda x: format_cell(unit_title, x))

    # Reset index so Grade is a column
    pivot.reset_index(inplace=True)

    # -------- Display --------
    st.subheader(f"Results for {selected_practice}")

    # Custom CSS (taller + wider cells)
    st.markdown(
        """
        <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid #ddd;
            text-align: left;
            padding: 12px;
            vertical-align: top;
            min-width: 180px;
        }
        th {
            background-color: #f4f4f4;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(pivot.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.warning("No data available for the selected filters.")
