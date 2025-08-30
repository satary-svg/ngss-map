# NGSS Practices Map (7th & 9th Grade)

A Streamlit app to browse NGSS practices across 7th and 9th grade, filter by practice and grade, and search by unit/activity.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud
1. Create a free account at https://streamlit.io/cloud and click **New app**.
2. Push this folder to a GitHub repo (e.g., `username/ngss-map`).
3. In Streamlit Cloud, select your repo, branch, and set **Main file path** to `app.py`.
4. Click **Deploy**. That's it!

The app reads data from the CSVs in `data/` so you can update them without changing code.
