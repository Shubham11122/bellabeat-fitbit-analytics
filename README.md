# Bellabeat × Fitbit Activity Analytics

An end-to-end data analytics case study on Bellabeat, using real Fitbit tracker data to uncover
patterns in daily activity, sleep, and BMI — and turn them into marketing recommendations.

**🔗 Live dashboard:** https://bellabeat-fitbit-analytics-l4pkqgagcvx4yjvvv6jdgg.streamlit.app/

---

## Overview

Bellabeat is a wellness-tech company selling health-tracking devices aimed at women. This project
analyzes a public Fitbit dataset (Fitabase) to answer: **how do people actually use their fitness
trackers, and what does that mean for Bellabeat's product and marketing strategy?**

The project covers the full analytics pipeline:

```
Raw CSVs  →  Data Cleaning  →  EDA  →  SQL Analysis  →  Interactive Dashboard  →  Recommendations
```

## Dashboard features

| Page | What it shows |
|---|---|
| **Overview** | Dataset summary, engagement breakdown, and project methodology |
| **Daily Activity** | Steps, calories, intensity minutes, weekday patterns, and user rankings |
| **Sleep** | Sleep duration, efficiency, and weekday vs. weekend comparisons |
| **BMI** | BMI distribution, category breakdown, and weight trends |
| **Hourly Patterns** | What time of day people are most active |
| **SQL Analysis** | 20 saved SQL queries with live results, plus a box to run your own read-only query |
| **Findings & Recommendations** | Data-backed findings and marketing recommendations for Bellabeat |

Every page (except SQL Analysis and Findings) responds to sidebar filters: user selection, date
range, and whether to include days the tracker likely wasn't worn.

## Dataset

- **Source:** [Fitabase Fitbit tracker data](https://www.kaggle.com/datasets/arashnic/fitbit) (public, via Mobius / Kaggle)
- **Period:** 12 April – 12 May 2016 (31 days)
- **Users:** 33 total — 24 with sleep data, 8 with weight/BMI data
- **Scope:** daily and hourly activity, sleep, and weight/BMI. Minute-level and heart-rate data
  were excluded by design to keep the analysis focused.

## Project structure

```
bellabeat-fitbit-analytics/
├── Data/
│   ├── raw/                        # Original Fitabase CSVs (not committed — see .gitignore)
│   └── processed/                  # Cleaned CSVs, exported by the cleaning notebook
├── db/
│   └── fitbit.db                   # SQLite database used by the SQL queries and the app
├── notebooks/
│   ├── data_cleaning.ipynb         # Load, clean, validate, and export the data
│   └── eda.ipynb                   # 20 exploratory charts and findings
├── sql/
│   └── analysis_queries.sql        # 20 documented SQL queries
├── app/
│   └── streamlit_app.py            # The dashboard (single file)
├── assets/                         # Logo/branding images used by the dashboard
├── docs/
│   └── REPORT.md                   # Full written case-study report
├── requirements.txt
└── README.md
```

## Tech stack

- **Python** — pandas, numpy for cleaning and analysis
- **SQLite** — all analysis queries run against a local `.db` file
- **Matplotlib / Seaborn** — static EDA charts (notebook)
- **Plotly** — interactive charts (dashboard)
- **Streamlit** — the dashboard itself

## Running it locally

```bash
# 1. Clone the repo
git clone https://github.com/Shubham11122/bellabeat-fitbit-analytics.git
cd bellabeat-fitbit-analytics

# 2. Set up the environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Place the raw Fitabase CSVs in Data/raw/, then build the cleaned data + database
jupyter notebook notebooks/data_cleaning.ipynb   # run all cells

# 4. Explore the findings
jupyter notebook notebooks/eda.ipynb

# 5. Launch the dashboard
streamlit run app/streamlit_app.py
```

## Key findings (summary)

- **46%** of tracked days fall below 7,500 steps, and **~80%** of tracked time is sedentary.
- Engagement drops sharply beyond step tracking: **33 → 24 → 8** users for activity, sleep, and
  weight logging respectively.
- Sleep duration does **not** meaningfully predict next-day activity (r ≈ -0.16) in this data.
- Activity consistently peaks in the early evening across both weekdays and weekends.
- Lower BMI correlates with higher activity in this small sample (r ≈ -0.47 to -0.58), though the
  8-user sample is too small to generalize.

See [`docs/REPORT.md`](docs/REPORT.md) for the full write-up, methodology, and business
recommendations for Bellabeat.

## Limitations

This is a small, self-selected sample (33 users, 31 days) and is not representative of Bellabeat's
full customer base. Sleep and especially weight/BMI findings rest on a minority of users. See the
Overview page in the dashboard, or the full report, for details.

## Author

Built by [Shubham](https://github.com/Shubham11122) as a data analytics portfolio project.
