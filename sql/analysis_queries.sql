-- =====================================================================
-- Bellabeat / Fitbit SQL Analysis
-- Run against: db/fitbit.db
-- Tables: daily_activity, sleep_daily, weight_log, hourly_activity
-- =====================================================================

-- ---------------------------------------------------------------------
-- DAILY ACTIVITY
-- ---------------------------------------------------------------------

-- Q1: Overall steps range (worn days only)
SELECT ROUND(AVG(TotalSteps),0) AS avg_steps, MIN(TotalSteps) AS min_steps, MAX(TotalSteps) AS max_steps
FROM daily_activity WHERE is_worn = 1;
-- Result: avg 8,271 | min 0 | max 36,019

-- Q2: Top 5 most active users by average steps
SELECT Id, ROUND(AVG(TotalSteps),0) AS avg_steps
FROM daily_activity WHERE is_worn = 1
GROUP BY Id ORDER BY avg_steps DESC LIMIT 5;
-- Top user averages 16,040 steps/day

-- Q3: Average steps & calories by day of week
SELECT day_of_week, ROUND(AVG(TotalSteps),0) AS avg_steps, ROUND(AVG(Calories),0) AS avg_calories
FROM daily_activity WHERE is_worn = 1
GROUP BY day_of_week ORDER BY avg_steps DESC;
-- Tuesday highest (8,885), Sunday lowest

-- Q4: % of days below 7,500 steps (a common "lightly active" threshold)
SELECT ROUND(100.0 * SUM(CASE WHEN TotalSteps < 7500 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_below_7500_steps
FROM daily_activity WHERE is_worn = 1;
-- Result: 46.3% of days fall below 7,500 steps

-- Q5: Share of total time by intensity category
SELECT
  ROUND(SUM(SedentaryMinutes)*100.0/SUM(SedentaryMinutes+LightlyActiveMinutes+FairlyActiveMinutes+VeryActiveMinutes),1) AS pct_sedentary,
  ROUND(SUM(LightlyActiveMinutes)*100.0/SUM(SedentaryMinutes+LightlyActiveMinutes+FairlyActiveMinutes+VeryActiveMinutes),1) AS pct_light,
  ROUND(SUM(FairlyActiveMinutes)*100.0/SUM(SedentaryMinutes+LightlyActiveMinutes+FairlyActiveMinutes+VeryActiveMinutes),1) AS pct_fair,
  ROUND(SUM(VeryActiveMinutes)*100.0/SUM(SedentaryMinutes+LightlyActiveMinutes+FairlyActiveMinutes+VeryActiveMinutes),1) AS pct_very
FROM daily_activity WHERE is_worn = 1;
-- Result: 79.5% sedentary, 17.4% light, 1.2% fairly active, 1.9% very active

-- Q6: Users with the fewest logged days (lowest engagement)
SELECT Id, COUNT(*) AS days_logged FROM daily_activity GROUP BY Id ORDER BY days_logged ASC LIMIT 5;
-- Lowest user logged only 4 of 31 days

-- ---------------------------------------------------------------------
-- SLEEP
-- ---------------------------------------------------------------------

-- Q7: Average sleep duration and time in bed
SELECT ROUND(AVG(hours_asleep),2) AS avg_sleep_hours, ROUND(AVG(hours_in_bed),2) AS avg_in_bed_hours
FROM sleep_daily;
-- Result: 6.99h asleep, 7.64h in bed

-- Q8: Users with the lowest sleep efficiency
SELECT Id, ROUND(AVG(sleep_efficiency),3) AS avg_efficiency FROM sleep_daily GROUP BY Id ORDER BY avg_efficiency ASC LIMIT 5;
-- Lowest user: 0.634 (63% of time in bed actually asleep)

-- Q9: Engagement gap — sleep vs total users
SELECT COUNT(DISTINCT Id) AS users_with_sleep FROM sleep_daily;
SELECT COUNT(DISTINCT Id) AS users_total FROM daily_activity;
-- 24 of 33 users log sleep (73%)

-- Q10: Weekday vs weekend average sleep
SELECT is_weekend, ROUND(AVG(hours_asleep),2) AS avg_hours FROM sleep_daily GROUP BY is_weekend;
-- Weekday 6.88h, Weekend 7.26h

-- Q11: Users who consistently under- or over-sleep
SELECT Id, ROUND(AVG(hours_asleep),2) AS avg_sleep, COUNT(*) AS nights
FROM sleep_daily GROUP BY Id HAVING avg_sleep < 6 OR avg_sleep > 9 ORDER BY avg_sleep;
-- Several users average under 5 hours across many nights

-- ---------------------------------------------------------------------
-- BMI / WEIGHT
-- ---------------------------------------------------------------------

-- Q12: Average weight, BMI and category per user
SELECT Id, ROUND(AVG(WeightKg),1) AS avg_weight_kg, ROUND(AVG(BMI),1) AS avg_bmi,
  CASE WHEN AVG(BMI) < 18.5 THEN 'Underweight'
       WHEN AVG(BMI) < 25 THEN 'Normal'
       WHEN AVG(BMI) < 30 THEN 'Overweight'
       ELSE 'Obese' END AS bmi_category
FROM weight_log GROUP BY Id ORDER BY avg_bmi;
-- 3 Normal, 4 Overweight, 1 Obese (n=8 users)

-- Q13: Engagement gap — weight vs total users
SELECT COUNT(DISTINCT Id) AS users_with_weight FROM weight_log;
-- Only 8 of 33 users (24%)

-- Q14: Weight trend — first vs last logged weight per user
WITH first_last AS (
  SELECT Id,
    FIRST_VALUE(WeightKg) OVER (PARTITION BY Id ORDER BY date) AS first_w,
    FIRST_VALUE(WeightKg) OVER (PARTITION BY Id ORDER BY date DESC) AS last_w
  FROM weight_log
)
SELECT DISTINCT Id, first_w, last_w, ROUND(last_w-first_w,1) AS change_kg FROM first_last ORDER BY change_kg;
-- Most users show near-zero net change over the month

-- Q15: Manual vs automatic weight entries
SELECT IsManualReport, COUNT(*) AS n FROM weight_log GROUP BY IsManualReport;
-- Manual (1): 41 entries, Automatic (0): 26 entries

-- ---------------------------------------------------------------------
-- CROSS-TABLE (JOINS)
-- ---------------------------------------------------------------------

-- Q16: Does last night's sleep predict next-day activity?
-- NOTE: date() strips the time part, so both sides must use date() or they won't match.
SELECT ROUND(AVG(s.hours_asleep),2) AS avg_prev_sleep, ROUND(AVG(a.TotalSteps),0) AS avg_next_day_steps, COUNT(*) AS matched_days
FROM sleep_daily s
JOIN daily_activity a ON a.Id = s.Id AND date(a.date) = date(s.date, '+1 day')
WHERE a.is_worn = 1;
-- 390 matched day-pairs; avg prev sleep 6.98h -> avg next-day steps 8,527

-- Q17: BMI vs. activity level per user
SELECT w.Id, ROUND(AVG(w.BMI),1) AS avg_bmi, ROUND(AVG(a.TotalSteps),0) AS avg_steps
FROM weight_log w JOIN daily_activity a ON a.Id = w.Id AND a.is_worn = 1
GROUP BY w.Id ORDER BY avg_bmi;
-- Lower BMI users tend toward higher step counts in this sample

-- Q18: Combined profile for users with activity + sleep + weight all three
SELECT a.Id, ROUND(AVG(a.TotalSteps),0) AS avg_steps, ROUND(AVG(s.hours_asleep),2) AS avg_sleep, ROUND(AVG(w.BMI),1) AS avg_bmi
FROM daily_activity a
JOIN sleep_daily s ON s.Id = a.Id AND date(s.date) = date(a.date)
JOIN weight_log w ON w.Id = a.Id
WHERE a.is_worn = 1
GROUP BY a.Id;
-- Only 6 users have all three data types logged on overlapping days

-- ---------------------------------------------------------------------
-- HOURLY
-- ---------------------------------------------------------------------

-- Q19: Top 5 peak hours by average steps
SELECT hour, ROUND(AVG(StepTotal),0) AS avg_steps FROM hourly_activity GROUP BY hour ORDER BY avg_steps DESC LIMIT 5;
-- Peak: 6 PM (599), 7 PM (583), 5 PM (550)

-- Q20: Weekday vs weekend hourly intensity (first 10 hours shown)
SELECT is_weekend, hour, ROUND(AVG(TotalIntensity),1) AS avg_intensity
FROM hourly_activity GROUP BY is_weekend, hour ORDER BY hour;