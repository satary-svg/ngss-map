import streamlit as st
import pandas as pd

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
    practice = st.selectbox("NGSS Practice", practices, index=practices.index(practices[0]))
    search = st.text_input("Search (unit/activity contains...)", value="")
    show_category = st.checkbox("Show Category column", value=True)
    st.markdown("---")
    st.caption("Tip: Use the search box to filter by unit keywords (e.g., 'Enzymes') or activity names.")

mask = (df_all["Grade"].isin(grades)) & (df_all["NGSS Practice"] == practice)
if search.strip():
    s = search.strip().lower()
    mask &= df_all["Unit"].str.lower().str.contains(s) | df_all["Activity/Assessment"].str.lower().str.contains(s)

filtered = df_all[mask].copy()

st.subheader("Results")
cols = ["Grade", "NGSS Practice", "Unit", "Activity/Assessment"]
if show_category and "Category" in filtered.columns:
    cols.append("Category")

if filtered.empty:
    st.info("No matches. Try changing the practice, grades, or search.")
else:
    st.dataframe(filtered[cols], use_container_width=True, hide_index=True)

# Download
csv = filtered[cols].to_csv(index=False).encode("utf-8")
st.download_button("Download results as CSV", csv, file_name="ngss_results.csv", mime="text/csv")

# Footer
st.markdown("---")
st.caption("Prototype • Built for quick exploration of NGSS practices across 7th & 9th grade.")