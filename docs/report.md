# Bellabeat Fitbit Activity Analysis — Case Study Report

**Live dashboard:** https://bellabeat-fitbit-analytics-l4pkqgagcvx4yjvvv6jdgg.streamlit.app/
**Repository:** https://github.com/Shubham11122/bellabeat-fitbit-analytics

---

## 1. Business Task

Bellabeat is a wellness-technology company that designs health-tracking products for women. This
analysis uses smart-device (Fitbit) usage data from a comparable consumer base to answer:

> **How do people actually use their fitness trackers day to day, and what does that behavior
> imply for Bellabeat's product features and marketing strategy?**

The analysis focuses on three areas: **daily activity, sleep patterns, and BMI** — deliberately
excluding minute-level and heart-rate data to keep the scope focused on patterns that are directly
actionable for marketing and product decisions.

## 2. Data Source

- **Provider:** Fitabase, via a public Kaggle dataset ("FitBit Fitness Tracker Data", Möbius)
- **Collection period:** 12 April 2016 – 12 May 2016 (31 days)
- **Participants:** 33 Fitbit users who consented to share personal tracker data
- **Tables used:**

| Table | Grain | Users covered | Records |
|---|---|---|---|
| Daily activity | 1 user, 1 day | 33 of 33 (100%) | 940 |
| Sleep | 1 user, 1 day | 24 of 33 (73%) | 410 (after removing 3 duplicates) |
| Weight / BMI | 1 user, 1 weigh-in | 8 of 33 (24%) | 67 |
| Hourly activity | 1 user, 1 hour | 33 of 33 (100%) | 22,099 |

Minute-level step/calorie/intensity files and the second-level heart-rate file were excluded from
scope — they cover a subset of users (heart rate: only 14 of 33) and are too granular for the
daily-behavior questions this analysis addresses.

### Data credibility note (ROCCC)

This dataset has known limitations worth stating plainly: it is small (33 users), short
(31 days), self-selected (Fitbit-using volunteers, not a random sample), and roughly a decade old.
It should be treated as **directionally informative**, not statistically representative of
Bellabeat's full customer base.

## 3. Methodology

### 3.1 Data cleaning

Performed in `notebooks/data_cleaning.ipynb`:

- Converted all date/time columns from text to proper datetime types and standardized column names
  across tables to enable joins.
- Removed 3 exact duplicate rows in the sleep table.
- Flagged (not deleted) 72 "not-worn" days — days with 0 steps and 1,440 sedentary minutes
  (a full 24 hours), which almost certainly indicate the tracker was off the wrist rather than the
  user being completely still. All activity-based averages in this report exclude these days
  unless stated otherwise.
- Dropped the `Fat` column from the weight table (65 of 67 values were empty).
- Engineered features used throughout the analysis: `day_of_week`, `is_weekend`,
  `total_active_minutes`, `activity_level` (5-tier step bucket), `hours_asleep`,
  `sleep_efficiency`, `sleep_category`, and `bmi_category` (WHO bands).
- Merged the three hourly files (steps, calories, intensity) into a single `hourly_activity` table,
  since they share the same grain (one user, one hour).
- Exported clean CSVs to `Data/processed/` and loaded all four clean tables into a SQLite database
  (`db/fitbit.db`) for the SQL analysis and dashboard.

### 3.2 Exploratory data analysis

Performed in `notebooks/eda.ipynb` — 20 visualizations spanning histograms, scatter plots, bar and
stacked-bar charts, a donut chart, box and violin plots, line and area charts, and a correlation
heatmap, covering activity, sleep, BMI, and hourly patterns.

### 3.3 SQL analysis

20 documented queries in `sql/analysis_queries.sql`, run against `db/fitbit.db`, covering daily
activity, sleep, BMI/weight, cross-table joins, and hourly patterns. The same queries are available
to run live in the dashboard's **SQL Analysis** page, alongside a read-only box for custom queries.

### 3.4 Dashboard

An interactive Streamlit dashboard (`app/streamlit_app.py`) mirrors and extends the EDA with
filterable, live charts across six pages, plus a dedicated findings and recommendations page.

## 4. Key Findings

### 4.1 Most users fall short of common activity guidelines

- **46%** of tracked days end under 7,500 steps (a commonly used "lightly active" threshold).
- **~80%** of all tracked time is sedentary; fairly-active and very-active minutes combined make up
  only about **3%** of tracked time.
- Activity is lowest on **Sundays** and highest on **Tuesdays/Saturdays** — a modest but consistent
  weekly rhythm, not a flat weekday/weekend split.

### 4.2 Engagement drops sharply beyond step tracking

- **33 of 33** users log daily activity.
- **24 of 33 (73%)** log sleep.
- **8 of 33 (24%)** log weight — and 2 of those 8 users account for the majority of all weigh-in
  records.
- Only about **6 users** have activity, sleep, and weight all logged on overlapping days, which
  limits how much cross-metric analysis the data can support.

### 4.3 Sleep is inconsistent, and does not clearly predict next-day activity

- Median sleep duration sits close to the widely recommended 7–9 hour range, but **100 of 410**
  logged nights (about 24%) were under 6 hours.
- Weekend sleep (≈7.26h) runs modestly longer than weekday sleep (≈6.88h).
- The correlation between a night's sleep duration and the following day's step count is weak
  (**r ≈ -0.16**) — this dataset does not support a "sleep more, move more" narrative.

### 4.4 Activity consistently peaks in the early evening

- Average hourly step counts rise sharply from around 6 AM and peak between **6–7 PM**, on both
  weekdays and weekends. This is the single most consistent time-of-day pattern in the data.

### 4.5 Lower BMI is associated with higher activity, in a very small sample

- Among the 8 users with weight data, BMI correlates with average daily steps at **r ≈ -0.47** and
  with active minutes at **r ≈ -0.58**.
- The direction is consistent with expectations, but a sample of 8 is too small to generalize —
  this finding should be treated as suggestive only.

## 5. Recommendations for Bellabeat

1. **Time activity nudges for the 6–7 PM window.** Since users are already most active during this
   window, a notification or challenge timed here is more likely to reinforce existing behavior
   than to create motivation from a standing start.

2. **Run a Sunday-specific re-engagement challenge.** Sunday shows the lowest average steps of the
   week. A short, named challenge (e.g., a "Sunday reset") could target this specific dip rather
   than relying on a generic daily reminder.

3. **Incentivize sleep and weight logging, not just steps.** The steep drop-off in engagement
   (33 → 24 → 8 users) looks more like underuse of existing features than disinterest. Streaks,
   weekly summary emails, or easier smart-scale syncing could close this gap — and would also
   improve the quality of Bellabeat's own future data.

4. **Market sleep tracking and activity tracking as separate benefits.** The data does not support
   a strong causal link between sleep and next-day activity. Claiming otherwise in marketing
   material risks looking unsubstantiated; each feature is better promoted on its own merits.

5. **Segment marketing messages by baseline activity level.** With a wide spread between the most
   and least active users, a single "get moving" message likely undersells highly active users and
   overwhelms sedentary ones. Tiered messaging (e.g., "keep your streak going" vs. "take the first
   step") would better match both groups.

## 6. Limitations

- **Small, self-selected sample:** 33 users over 31 days, collected in 2016 — not representative of
  Bellabeat's current or full customer base.
- **Uneven data coverage:** sleep findings rest on 73% of users; BMI findings rest on just 24% of
  users, with 2 of those 8 users dominating the weight records.
- **Correlation, not causation:** relationships noted in this report (e.g., sleep vs. activity, BMI
  vs. activity) are observational and should not be read as causal.
- **Scope exclusions:** minute-level and heart-rate data were intentionally excluded to keep the
  analysis focused on daily-level, actionable patterns.

## 7. Tools Used

| Stage | Tools |
|---|---|
| Data cleaning & feature engineering | Python (pandas, numpy) |
| Exploratory data analysis | Python (matplotlib, seaborn) |
| Analysis queries | SQL (SQLite) |
| Interactive dashboard | Streamlit, Plotly |
| Version control | Git / GitHub |

---

*Full code, notebooks, and the interactive dashboard are available in this repository. See the
[README](../README.md) for setup instructions.*
