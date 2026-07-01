# UCUCI Bank Loan Repayment Tableau Dashboard Guide

This guide converts the Python redesign notebook into a beginner-to-intermediate Tableau Public dashboard. It uses the same business question, hypotheses, KPIs, and insights, but presents them as an interactive Tableau workbook.

## 1. Data File to Use

Use the original project dataset as the main Tableau data source:

`UCUCI_dataset.csv`

This is the same dataset used in the Python notebook. It has one row per loan and includes the original fields such as:

- `id`
- `loan_amnt`
- `funded_amnt`
- `term`
- `int_rate`
- `installment`
- `grade`
- `sub_grade`
- `annual_inc`
- `issue_d`
- `last_pymnt_d`
- `last_pymnt_amnt`
- `loan_status`
- `purpose`
- `dti`
- `total_pymnt`
- `out_prncp`
- `recoveries`

The files inside `tableau_outputs` are optional reference checks only. Do not use them as the main submitted Tableau data source if your evaluator expects the dashboard to be built on the original dataset.

## 2. Dashboard Objective

Dashboard title:

**UCUCI Loan Repayment and Default Risk Dashboard**

Business question:

**How can UCUCI Bank improve repayment performance, reduce default risk, and recover outstanding money from active risky loans before they become charged off?**

Main metric:

**Loan Repayment Rate (LRR) = SUM(total_pymnt) / SUM(funded_amnt) x 100**

## 3. Tableau Calculated Fields

Create these calculated fields in Tableau on top of `UCUCI_dataset.csv`. They are simple and beginner-friendly.

### Weighted LRR %

```text
SUM([total_pymnt]) / SUM([funded_amnt])
```

Format as Percentage with 1 decimal place.

Important Tableau check:

- When this field is dragged into Rows, Columns, Text, or Label, Tableau should display it as `AGG(Weighted LRR %)`.
- Do not use `AVG([total_pymnt] / [funded_amnt])` for dashboard charts. That creates an average of row-level LRR values and can give misleading results.
- Using the formula directly on the shelf as `SUM([total_pymnt]) / SUM([funded_amnt])` is also correct.
- If you see LRR around 30-40% for closed-loan charts, the worksheet is probably including active/current loans. Add `Portfolio Type = Closed`.

### Portfolio Type

```text
IF [loan_status] IN ("Fully Paid", "Charged Off", "Default") THEN "Closed"
ELSEIF [loan_status] IN ("Current", "In Grace Period", "Late (16-30 days)", "Late (31-120 days)") THEN "Active"
ELSE "Other"
END
```

### Closed Loan Flag

```text
IF [loan_status] IN ("Fully Paid", "Charged Off", "Default") THEN 1 ELSE 0 END
```

### Active Loan Flag

```text
IF [loan_status] IN ("Current", "In Grace Period", "Late (16-30 days)", "Late (31-120 days)") THEN 1 ELSE 0 END
```

### Charged Off Flag

```text
IF [loan_status] = "Charged Off" THEN 1 ELSE 0 END
```

### Bad Loan Flag

```text
IF [loan_status] IN ("Charged Off", "Default") THEN 1 ELSE 0 END
```

### Delinquent Flag

```text
IF [loan_status] IN ("In Grace Period", "Late (16-30 days)", "Late (31-120 days)") THEN 1 ELSE 0 END
```

### Default Rate %

```text
SUM([Charged Off Flag]) / COUNT([id])
```

Format as Percentage with 1 decimal place.

### Bad Loan Rate %

```text
SUM([Bad Loan Flag]) / COUNT([id])
```

Format as Percentage with 1 decimal place.

### Active Delinquency Rate %

```text
SUM([Delinquent Flag]) / SUM([Active Loan Flag])
```

Format as Percentage with 1 decimal place.

### Funded Amount Cr

```text
SUM([funded_amnt]) / 10000000
```

Format as Number with 1 decimal place.

### Outstanding Principal Cr

```text
SUM([out_prncp]) / 10000000
```

Format as Number with 1 decimal place.

### At Risk Outstanding Principal

```text
IF [Delinquent Flag] = 1 THEN [out_prncp] ELSE 0 END
```

### At Risk Outstanding Cr

```text
SUM([At Risk Outstanding Principal]) / 10000000
```

Format as Number with 1 decimal place.

### Loan Count

```text
COUNT([id])
```

Format as whole number.

### Interest Rate Band

```text
IF [int_rate] < 10 THEN "<10%"
ELSEIF [int_rate] < 15 THEN "10-15%"
ELSEIF [int_rate] < 20 THEN "15-20%"
ELSEIF [int_rate] < 25 THEN "20-25%"
ELSEIF [int_rate] < 30 THEN "25-30%"
ELSE "30%+"
END
```

### DTI Band

```text
IF [dti] <= 10 THEN "0-10"
ELSEIF [dti] <= 20 THEN "10-20"
ELSEIF [dti] <= 30 THEN "20-30"
ELSEIF [dti] <= 40 THEN "30-40"
ELSEIF [dti] <= 100 THEN "40-100"
ELSE "100+"
END
```

### Annual Income Band

```text
IF [annual_inc] <= 25000 THEN "<=25K"
ELSEIF [annual_inc] <= 50000 THEN "25K-50K"
ELSEIF [annual_inc] <= 75000 THEN "50K-75K"
ELSEIF [annual_inc] <= 100000 THEN "75K-100K"
ELSEIF [annual_inc] <= 150000 THEN "100K-150K"
ELSEIF [annual_inc] <= 250000 THEN "150K-250K"
ELSE "250K+"
END
```

### Installment Band

```text
IF [installment] <= 200 THEN "<=200"
ELSEIF [installment] <= 400 THEN "200-400"
ELSEIF [installment] <= 600 THEN "400-600"
ELSEIF [installment] <= 800 THEN "600-800"
ELSEIF [installment] <= 1000 THEN "800-1000"
ELSE "1000+"
END
```

### Clean Term

```text
TRIM([term])
```

Use `Clean Term` in charts and filters instead of raw `term`, because the original CSV has a leading space in values such as ` 36 months`.

### Risk Priority

```text
IF [Delinquent Flag] = 1 THEN "Immediate Recovery"
ELSEIF [grade] IN ("D", "E", "F", "G")
    OR [int_rate] > 15
    OR [dti] > 30
    OR [Clean Term] = "60 months"
    OR [purpose] IN ("small_business", "house", "moving", "renewable_energy")
THEN "High Priority"
ELSE "Monitor"
END
```

### Issue Year

```text
YEAR(DATEPARSE("MMM-yyyy", [issue_d]))
```

If Tableau Public does not accept `DATEPARSE`, skip this field and use `issue_d` as a normal filter.

### Last Payment Date

```text
DATEPARSE("MMM-yyyy", [last_pymnt_d])
```

The dataset gives last payment at month level, not exact date-time. Use this as payment recency, not time-of-day behaviour.

### Months Since Last Payment

```text
DATEDIFF('month', [Last Payment Date], { FIXED : MAX([Last Payment Date]) })
```

This compares each loan's last payment month with the latest payment month in the dataset. Do not compare this old dataset to today's date.

### Last Payment Recency Band

```text
IF ISNULL([Last Payment Date]) THEN "No payment date"
ELSEIF [Months Since Last Payment] <= 1 THEN "0-1 month"
ELSEIF [Months Since Last Payment] <= 3 THEN "2-3 months"
ELSEIF [Months Since Last Payment] <= 6 THEN "4-6 months"
ELSEIF [Months Since Last Payment] <= 12 THEN "7-12 months"
ELSEIF [Months Since Last Payment] <= 24 THEN "13-24 months"
ELSE "24+ months"
END
```

Use this on active-loan recovery views to show which accounts have stale payment activity.

## 4. Global Filters

Add these filters where they help stakeholders explore the view:

- `grade`
- `Clean Term`
- `purpose`
- `Interest Rate Band`
- `DTI Band`
- `Annual Income Band`
- `Last Payment Recency Band`
- `Issue Year`
- `sub_grade`
- `Risk Priority`

Use `Portfolio Type` carefully:

- Dashboard 1 mixes closed and active views, so use worksheet-level filters instead of one dashboard-wide `Portfolio Type` filter.
- Dashboard 2 must use `Portfolio Type = Closed` on every worksheet.
- Dashboard 3 must use `Portfolio Type = Active` on every worksheet.
- Leave grade, purpose, Clean Term, DTI, and interest filters as All.

Do not use `Portfolio Type = Active` on Dashboard 2. Active/current loans have not finished repayment, so their LRR will look artificially low.

## 5. Quick Validation Checks

Use these values to check whether the Tableau worksheet is calculating correctly:

| Worksheet | Correct Filter | Expected Result |
|---|---:|---:|
| KPI: Completed Loan LRR | `Portfolio Type = Closed` | about 100.3% |
| LRR by Grade | `Portfolio Type = Closed` | A about 104.2%, G about 89.5% |
| LRR by Interest Rate Band | `Portfolio Type = Closed` | `<10%` about 103.7%, `25-30%` about 82.0% |
| LRR by DTI Band | `Portfolio Type = Closed` | `0-10` about 103.6%, `30-40` about 90.4% |
| LRR by Annual Income Band | `Portfolio Type = Closed` | `<=25K` about 96.2%, `250K+` about 104.4% |
| LRR by Loan Term | `Portfolio Type = Closed` | 36 months about 103.0%, 60 months about 94.6% |
| Active Delinquency by Grade | `Portfolio Type = Active` | A about 1.0%, G about 11.6% |

If `LRR by Interest Rate Band` shows the `<10%` band near 40%, check these two things first:

1. The worksheet filter must be `Portfolio Type = Closed`.
2. The measure must be `Weighted LRR %` or the direct shelf formula `SUM([total_pymnt]) / SUM([funded_amnt])`, not `AVG([total_pymnt] / [funded_amnt])`.

## 6. Workbook Structure

### Design Correction: Fields to Bring Back From Python

The Python notebook uses income, sub-grade, and last payment information. The first Tableau design kept the dashboard simpler, but that made the Tableau story less complete and caused one active exposure insight to appear twice. Use the updated design below:

- Keep `LRR vs Average Interest Rate by Sub-grade` on Dashboard 1 as the granular credit-pricing view.
- Add an income and DTI heatmap on Dashboard 2 so affordability is visible, not only broad credit grade.
- Replace the repeated broad `At-Risk Outstanding by Grade` view on Dashboard 3 with `At-Risk Outstanding by Last Payment Recency`.
- Use sub-grade as a drill-down filter or optional active-risk worksheet instead of repeating the same grade-level bar chart.

Create 3 dashboards and 1 story:

1. **Executive Overview**
2. **Closed Loan LRR Drivers**
3. **Active Risk and Recovery**
4. **Story: Improving Loan Repayment**

Use a simple landscape layout such as `1200 x 800`. Keep the layout clean: KPI cards at the top, charts below, filters on the right.

## 7. How to Build the Dashboards in Tableau

Follow this process after all worksheets are created:

1. Click **New Dashboard** at the bottom of Tableau.
2. In the left panel, set **Size** to `Fixed Size` and use `1200 x 800`. If your laptop screen is smaller, use `Automatic` while editing and switch to fixed before publishing.
3. Drag a **Horizontal Container** to the top for KPI cards.
4. Drag KPI worksheets into that top container.
5. Drag a **Vertical Container** below the KPIs for the main charts.
6. Put two charts side by side using a **Horizontal Container**.
7. Add filters on the right side. Use only useful filters, not every field.
8. Right-click each filter and choose a compact display style such as dropdown, single value dropdown, or multiple values dropdown.
9. Click each chart title and rename it in business language.
10. Use **Dashboard > Actions > Filter** if you want clicking a grade/purpose in one chart to filter other charts.

Recommended dashboard layout:

- Top row: KPI cards.
- Middle row: 2 major charts.
- Bottom row: 1 wide chart or 2 supporting charts.
- Right side: filters.

For Dashboard 1, do not apply one dashboard-wide `Portfolio Type` filter. It contains both closed and active views. Keep `Portfolio Type` as worksheet-level filters.

For Dashboard 2, every worksheet should have `Portfolio Type = Closed`.

For Dashboard 3, every worksheet should have `Portfolio Type = Active`.

### How to Create KPI Cards

Create KPI cards as separate worksheets first, then drag those worksheets into the dashboard. This is easier to format, easier to reuse, and more acceptable for a beginner/intermediate Tableau project than trying to create numbers directly inside the dashboard.

For each KPI card:

1. Click **New Worksheet**.
2. Rename the sheet, for example `KPI - Loan Repayment Rate`.
3. Drag the KPI measure to **Text** on the Marks card.
4. Change Marks type to **Text**.
5. Click **Text** and edit the label.
6. Put the KPI name on the first line and the value on the second line.
7. Increase the value font size to around 20-28.
8. Center align the text.
9. Hide rows/columns/gridlines if any appear.
10. Apply the correct worksheet filter, such as `Portfolio Type = Closed` for LRR.
11. Drag the KPI worksheet into the dashboard top KPI container.

Recommended KPI label format:

```text
Loan Repayment Rate
100.3%
```

Use a clean white or very light grey background. Add a thin border only if the cards need separation.

### Recommended KPI Cards

For this project, include KPI cards that directly match the problem statement first:

1. **Total Loans Issued**
   - Measure: `COUNT([id])`
   - Filter: none
   - Expected value: `887,379`

2. **Loan Repayment Rate**
   - Measure: `Weighted LRR %`
   - Filter: `Portfolio Type = Closed`
   - Expected value: about `100.3%`

3. **Default Rate**
   - Measure: `Default Rate %`
   - Filter: none
   - Expected value: about `5.1%`

4. **Average Interest Rate**
   - Measure: `AVG([int_rate])`
   - Filter: none, or use dashboard filters if shown by grade
   - Expected value: about `13.2%`

5. **Practical Recovery Rate**
   - Measure: create `Practical Recovery Rate %`
   - Filter: `loan_status = Charged Off`
   - Expected value: about `6.1%`

Optional recovery formula:

```text
SUM([recoveries]) / SUM([funded_amnt])
```

The problem statement says recovery rate is `recoveries / out_prncp` for charged-off loans. In this dataset, charged-off loans have `out_prncp = 0`, so that direct formula is not meaningful. Mention this briefly in a tooltip, story caption, or dashboard note. Use practical recovery rate as a readable alternative.

If you have space, add one or two active-risk KPI cards:

6. **Active Delinquency Rate**
   - Measure: `Active Delinquency Rate %`
   - Filter: `Portfolio Type = Active`
   - Expected value: about `3.25%`

7. **At-Risk Outstanding Principal**
   - Measure: `At Risk Outstanding Cr`
   - Filter: `Portfolio Type = Active`
   - Expected value: about `₹23.6 Cr`

For grading, a good top row is:

- Total Loans Issued
- Loan Repayment Rate
- Default Rate
- Average Interest Rate
- Practical Recovery Rate
- At-Risk Outstanding Principal

## 8. Formatting and Grading-Friendly Polish

These improvements are simple enough for beginner/intermediate Tableau but make the dashboard look more presentation-ready.

### Number Formatting

You already made a good choice by formatting crore values with a currency prefix and `Cr` suffix.

Use these formats consistently:

- Amounts in crore: prefix `₹`, suffix ` Cr`, 1 decimal place.
- LRR and delinquency: percentage, 1 decimal place.
- Loan count: whole number, display in K where needed.
- Interest rate: percentage or number with `%` suffix, 1 decimal place.

Suggested aliases:

- `debt_consolidation` → `Debt Consolidation`
- `credit_card` → `Credit Card`
- `small_business` → `Small Business`
- `home_improvement` → `Home Improvement`
- `renewable_energy` → `Renewable Energy`

### Colors

Avoid Tableau's default blue-only look. Use meaning-based colors:

- Good repayment / high LRR: green.
- Warning / medium risk: amber.
- High delinquency / weak repayment: red.
- Neutral exposure amount: deep blue or grey.

Recommended palettes:

- LRR charts: Red-Gold-Green diverging palette.
- Delinquency charts: Green-to-Red sequential palette, where higher delinquency is red.
- Exposure charts: Blue sequential palette, where larger exposure is darker.
- Grade charts: keep A as green, B/C as blue/teal, D as amber, E/F/G as orange/red.

For LRR charts, use color based on `Weighted LRR %`:

- Above 100%: green.
- 95% to 100%: amber.
- Below 95%: red.

For delinquency charts, use color based on delinquency rate:

- Below 3%: green.
- 3% to 6%: amber.
- Above 6%: red.

### Reference Lines

Add reference lines to make the charts easier to interpret:

- LRR charts: add a constant reference line at `100%`.
- Active delinquency charts: add a constant reference line at `3.25%`, the overall active delinquency rate.
- Risk vs Exposure chart: add a vertical reference line at `3.25%` delinquency and a horizontal reference line at the median or average outstanding principal.

In Tableau:

1. Open the worksheet.
2. Go to the **Analytics** pane.
3. Drag **Reference Line** onto the chart.
4. Choose Table or Pane, depending on the chart.
5. Use a dashed grey line and a short label such as `Overall Active Delinquency: 3.25%`.

### Trend Lines

Use trend lines only where they make sense:

- Add a trend line to **LRR vs Average Interest Rate by Sub-grade**.
- Add a trend line to **Risk vs Exposure by Purpose**.
- Do not add trend lines to simple bar charts.

In Tableau:

1. Open the scatter plot worksheet.
2. Go to the **Analytics** pane.
3. Drag **Trend Line** to the view.
4. Use **Linear**.
5. Right-click the trend line and choose **Edit Trend Lines** if you need to show or hide confidence bands.

For this project, a visible linear trend line is enough. Avoid polynomial or advanced model options.

### Labels and Tooltips

Use labels selectively. Too many labels will clutter the dashboard.

Recommended labels:

- Show labels on KPI cards.
- Show labels on highest-risk or highest-exposure bars.
- For scatter plots, label only important points such as `Debt Consolidation`, `Credit Card`, and `Small Business`.

Recommended tooltip for Risk vs Exposure:

```text
Purpose: <purpose>
Outstanding Principal: ₹<Outstanding Principal Cr> Cr
Delinquency Rate: <Active Delinquency Rate %>
Loan Count: <Loan Count>
At-Risk Outstanding: ₹<At Risk Outstanding Cr> Cr
```

### Dashboard Titles

Use titles that state the insight, not only the chart type.

Examples:

- Instead of `LRR by Grade`, use `Repayment Rate Falls for Lower Grades`.
- Instead of `LRR by Interest Rate Band`, use `High Interest Loans Repay Worse`.
- Instead of `At-Risk Outstanding by Grade`, use `C, D, and E Grades Need Recovery Focus`.

## 9. Risk vs Exposure Chart Validation

For the active-loan Risk vs Exposure by Purpose chart, use:

- Columns: `Active Delinquency Rate %`
- Rows: `Outstanding Principal Cr`
- Size: `Loan Count`
- Detail: `purpose`
- Color: `At Risk Outstanding Cr` or `Risk Priority`
- Filter: `Portfolio Type = Active`

Your debt consolidation values are correct if Tableau shows approximately:

- Delinquency rate: `3.5%`
- Outstanding principal: `₹452.8 Cr`
- Loan count: `369K`
- At-risk outstanding: `₹15.6 Cr`

Expected min/max checks:

| Metric | Minimum | Maximum |
|---|---:|---:|
| Loan count | Educational: 1 | Debt Consolidation: 369,166 |
| Outstanding principal | Educational: ₹0.0002 Cr | Debt Consolidation: ₹452.8 Cr |
| Delinquency rate | Educational: 0.0% | Small Business: 6.0% |
| At-risk outstanding | Educational: ₹0.0 Cr | Debt Consolidation: ₹15.6 Cr |

If the Educational point makes the axis look awkward, keep it in the data but do not label it. For presentation, label the main business points: Debt Consolidation, Credit Card, Home Improvement, Small Business, and Other.

## 10. How to Create the Tableau Story

After the dashboards are ready:

1. Click **New Story** at the bottom of Tableau.
2. Set story size to match the dashboards, preferably `1200 x 800`.
3. Drag `Executive Overview` into the first story point.
4. Add a caption at the top using plain business language.
5. Click **Blank** to add the next story point.
6. Drag the next dashboard or worksheet.
7. Repeat until all story points are created.
8. Rename the story points using short titles.

Recommended story point titles:

- `Portfolio Health`
- `Grades Drive Repayment`
- `High Interest and DTI Risk`
- `Long Tenure Weakens LRR`
- `Recovery Focus: C, D, E`
- `Final Recommendation`

Keep each story caption to 1-2 lines. Do not write long paragraphs inside Tableau.

## 11. Presentation Tips

When presenting:

1. Start with the LRR definition.
2. Explain that closed loans are used for repayment behavior.
3. Explain that active loans are used for current delinquency and exposure.
4. Use the reference lines to explain what is above or below the benchmark.
5. End with the recovery recommendation.

The final message should be:

**Improve future lending quality using grade, interest, DTI, and term signals; recover current exposure by prioritizing active delinquent C, D, and E loans.**

## 12. Dashboard 1: Executive Overview

Purpose:

Purpose:

Show top-level portfolio health and the most important risk/recovery indicators.

### KPI Cards

Create 5 text KPI sheets:

- Total Loans: `COUNT([id])`
- Completed Loan LRR: `Weighted LRR %`, filtered to `Portfolio Type = Closed`
- Active Delinquency Rate: `Active Delinquency Rate %`, filtered to `Portfolio Type = Active`
- Active Outstanding Principal: `Outstanding Principal Cr`, filtered to `Portfolio Type = Active`
- At-Risk Outstanding Principal: `At Risk Outstanding Cr`, filtered to `Portfolio Type = Active`

Verified reference values:

- Total loans: 887,379
- Closed loans: 254,190
- Active loans: 621,980
- Completed-loan LRR: 100.3%
- Active-loan delinquency rate: 3.25%
- Active outstanding principal: about 731.3 Cr
- At-risk outstanding principal: about 23.6 Cr

### Charts

1. **Loan Status Distribution**
   - Rows: `loan_status`
   - Columns: `Loan Count`
   - Mark: Horizontal Bar
   - Sort descending by `Loan Count`
   - Filter: keep `Portfolio Type = All`
   - Insight: The portfolio contains both closed and active loans, so closed repayment behavior and active recovery risk must be analyzed separately.

2. **LRR vs Average Interest Rate by Sub-grade**
   - Columns: `AVG(int_rate)`
   - Rows: `Weighted LRR %`
   - Detail: `sub_grade`
   - Color: `grade`
   - Size: `Loan Count`
   - Filter: `Portfolio Type = Closed`
   - Mark: Circle
   - Insight: Higher priced/riskier sub-grades generally show weaker repayment.

3. **Active At-Risk Outstanding by Grade**
   - Columns: `grade`
   - Rows: `At Risk Outstanding Cr`
   - Filter: `Portfolio Type = Active`
   - Mark: Bar
   - Insight: Recovery focus should start with C, D, and E.
   - Design note: Use this as the only broad grade-level at-risk bar chart. Dashboard 3 should use last-payment recency or sub-grade drill-down instead of repeating the same view.

## 13. Dashboard 2: Closed Loan LRR Drivers

Purpose:

Explain the historical repayment drivers behind the LRR hypothesis.

### Charts

1. **LRR by Grade**
   - Columns: `grade`
   - Rows: `Weighted LRR %`
   - Mark: Bar
   - Filter: `Portfolio Type = Closed`
   - Reference: A = 104.2%, B = 104.3%, G = 89.5%

2. **LRR by Interest Rate Band**
   - Columns: `Interest Rate Band`
   - Rows: `Weighted LRR %`
   - Mark: Line or Bar
   - Filter: `Portfolio Type = Closed`
   - Sort by the natural band order
   - Reference: `<10%` = 103.7%, `25-30%` = 82.0%

3. **LRR by DTI Band**
   - Columns: `DTI Band`
   - Rows: `Weighted LRR %`
   - Mark: Bar
   - Filter: `Portfolio Type = Closed`
   - Reference: `0-10` = 103.6%, `30-40` = 90.4%

4. **Affordability Heatmap: LRR by Income and DTI**
   - Rows: `Annual Income Band`
   - Columns: `DTI Band`
   - Color/Text: `Weighted LRR %`
   - Mark: Square
   - Filter: `Portfolio Type = Closed`
   - Sort income bands from lowest to highest
   - Insight: Income should be read with debt burden. Low income plus high DTI is a stronger affordability warning than income alone.

5. **LRR by Loan Term**
   - Rows: `Clean Term`
   - Columns: `Weighted LRR %`
   - Mark: Horizontal Bar
   - Filter: `Portfolio Type = Closed`
   - Reference: 36 months = 103.0%, 60 months = 94.6%

6. **LRR by Grade and Term**
   - Rows: `grade`
   - Columns: `Clean Term`
   - Text/Color: `Weighted LRR %`
   - Mark: Square
   - Filter: `Portfolio Type = Closed`
   - Reference: G + 60 months = 88.9%

7. **LRR by Purpose**
   - Rows: `purpose`
   - Columns: `Weighted LRR %`
   - Mark: Horizontal Bar
   - Filter: `Portfolio Type = Closed`
   - Sort ascending by LRR
   - Reference: small business = 94.8%; wedding, car, and credit card are stronger.

## 14. Dashboard 3: Active Risk and Recovery

Purpose:

Show where current loans are becoming risky and where collections should focus.

Important:

- Every chart on this dashboard should use `Portfolio Type = Active`.
- Do not add closed-loan LRR, default-rate, or recovery-rate charts here. Those are historical/defaulted-loan views and belong in Dashboard 1 KPI cards, Dashboard 2, or the story discussion.
- Do not repeat `LRR vs Average Interest Rate by Sub-grade` here. It is already used in the Executive Overview as the main LRR correlation view.
- Do not repeat the broad `At-Risk Outstanding by Grade` bar from Dashboard 1. Use payment recency or sub-grade drill-down here.

### Charts

1. **Active Delinquency Rate by Grade**
   - Columns: `grade`
   - Rows: `Active Delinquency Rate %`
   - Mark: Line or Bar
   - Filter: `Portfolio Type = Active`
   - Reference: A = 1.0%, G = 11.6%

2. **Active Delinquency by Interest Rate Band**
   - Columns: `Interest Rate Band`
   - Rows: `Active Delinquency Rate %`
   - Mark: Line
   - Filter: `Portfolio Type = Active`
   - Reference: `<10%` = 1.1%, `25-30%` = 11.2%

3. **Top Purposes by Outstanding Principal**
   - Rows: `purpose`
   - Columns: `Outstanding Principal Cr`
   - Filter: `Portfolio Type = Active`
   - Sort descending
   - Keep Top 10 by `Outstanding Principal Cr`
   - Reference: debt consolidation is the largest exposure at about 452.8 Cr.

4. **At-Risk Outstanding by Last Payment Recency**
   - Columns: `Last Payment Recency Band`
   - Rows: `At Risk Outstanding Cr`
   - Filter: `Portfolio Type = Active`
   - Mark: Bar
   - Sort from `0-1 month` to `24+ months`, with `No payment date` at the end
   - Insight: Recovery work becomes more urgent when delinquent exposure also has stale last-payment activity.

5. **Risk vs Exposure by Purpose**
   - Columns: `Active Delinquency Rate %`
   - Rows: `Outstanding Principal Cr`
   - Detail: `purpose`
   - Size: `Loan Count`
   - Color: `purpose`
   - Filter: `Portfolio Type = Active`
   - Insight: Highest delinquency rate is not always the highest money exposure.

6. **Optional Drill-Down: At-Risk Outstanding by Sub-grade**
   - Rows: `sub_grade`
   - Columns: `At Risk Outstanding Cr`
   - Filter: `Portfolio Type = Active`
   - Mark: Horizontal Bar
   - Sort descending by `At Risk Outstanding Cr`
   - Use when the audience wants operational queues below broad grade level.

## 15. Storyboard

Create a Tableau Story named:

**Improving UCUCI Loan Repayment**

Use these story points:

### Story Point 1: Portfolio Health

Dashboard: Executive Overview

Caption:

The portfolio has 887,379 loans. Completed-loan LRR is about 100.3%, but active loans still have 23.6 Cr of at-risk outstanding principal. The dashboard separates historical repayment behavior from current recovery risk.

### Story Point 2: Credit Grade Drives Repayment

Dashboard: Closed Loan LRR Drivers

Caption:

Repayment performance declines as credit grade worsens. A and B loans have LRR above 104%, while G loans fall to about 89.5%. Grade remains one of the clearest risk indicators.

### Story Point 3: Pricing and Affordability Matter

Dashboard: Closed Loan LRR Drivers

Caption:

Higher interest rate loans and higher DTI borrowers show weaker repayment. Loans below 10% interest have LRR around 103.7%, while the 25-30% band drops to about 82.0%. DTI above 30 also shows a major decline.

### Story Point 4: Long-Term Loans Add Risk

Dashboard: Closed Loan LRR Drivers

Caption:

60-month loans repay worse than 36-month loans. The weakest combination is lower grade with longer tenure, especially G-grade 60-month loans at about 88.9% LRR.

### Story Point 5: Recovery Should Prioritize C, D, and E

Dashboard: Active Risk and Recovery

Caption:

The riskiest grades are not always the largest exposure. Active at-risk outstanding principal is highest in grades C, D, and E, making these the best starting point for recovery action.

### Story Point 6: Recommendation

Dashboard: Active Risk and Recovery

Caption:

UCUCI Bank should combine stricter approval checks for high-risk combinations with early recovery action for active delinquent loans. Focus first on delinquent C, D, and E borrowers with high outstanding principal.

## 16. Presentation Flow

Use this 5-minute flow:

1. Start with the business question and LRR definition.
2. Show the Executive Overview KPIs.
3. Explain closed-loan patterns by grade, interest rate, DTI, term, and purpose.
4. Move to active-loan risk and show delinquency plus outstanding exposure.
5. End with the recommendation: prioritize active delinquent C/D/E loans and tighten high-risk lending combinations.

## 17. Tableau Public Publishing Checklist

Before publishing:

- Confirm all LRR charts use `Weighted LRR %` as `SUM(total_pymnt) / SUM(funded_amnt)`, not average row-level LRR.
- Confirm every Dashboard 2 worksheet has `Portfolio Type = Closed`; otherwise interest-rate and DTI LRR charts will look much too low.
- Confirm Dashboard 1, 2, and 3 have filters visible on the right.
- Set dashboard size to fixed `1200 x 800` or automatic if presenting from different screens.
- Add worksheet titles in plain business language.
- Hide unused worksheets after building the dashboards.
- Publish to Tableau Public using a clear title: `UCUCI Loan Repayment and Default Risk Dashboard`.
- In the Tableau Public description, mention that the analysis uses historical closed loans for LRR and active loans for delinquency/exposure monitoring.
