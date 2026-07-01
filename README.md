# UCUCI Loan Repayment Analysis

## Project Overview

This project analyzes UCUCI Bank loan data to understand repayment behavior, identify borrower segments with weaker repayment performance, and prioritize active loans that may need recovery attention.

The analysis separates closed loans from active loans:

- Closed loans are used to study historical repayment behavior.
- Active loans are used to identify current delinquency risk and outstanding exposure.

The main business question is:

> Which borrower segments repay better, and where should recovery effort be focused for active loans?

## Business Objective

UCUCI Bank wants to improve repayment performance and reduce default risk across its loan book. This project uses borrower and loan attributes such as grade, sub-grade, income, DTI, interest rate, loan term, purpose, repayment amount, and loan status to find practical repayment insights.

## Key Metric

The primary metric used is Loan Repayment Rate (LRR):

```text
LRR = Total Amount Repaid / Total Amount Funded
```

LRR is mainly interpreted for closed loans because active loans are still being repaid. Supporting metrics include charged-off rate, bad-loan rate, active delinquency rate, recovery rate, and outstanding principal exposure.

## Tools Used

- Python
- Jupyter Notebook
- Pandas
- NumPy
- Matplotlib
- Seaborn

## Repository Contents

```text
UCUCI_Loan_Repayment_Analysis_Redesigned.ipynb
```

Main notebook containing the end-to-end analysis, visualizations, findings, and recommendations.

```text
scripts/
```

Supporting Python scripts used for report generation.

```text
requirements.txt
```

Python dependencies required to run the notebook and supporting scripts.

## Dataset

The raw dataset is not committed to this repository because it is large. The notebook downloads the dataset using `gdown`.

Dataset summary used in the analysis:

- Rows: 887,379
- Columns: 57
- Main target field: `loan_status`
- Closed loan statuses: `Fully Paid`, `Charged Off`, `Default`
- Active loan statuses: `Current`, `In Grace Period`, `Late (16-30 days)`, `Late (31-120 days)`

Generated Tableau CSVs, dashboard images, raw data, and report outputs are intentionally excluded from GitHub.

## Analysis Performed

- Loan status distribution and data quality checks
- Repayment rate analysis across borrower grades and sub-grades
- DTI, income, interest rate, term, and purpose-based repayment comparisons
- Closed-loan repayment behavior analysis
- Active-loan delinquency and exposure analysis
- Identification of high-priority recovery segments

## Key Findings

- Repayment performance weakens as borrower grade worsens.
- Higher interest rate loans show weaker repayment behavior.
- High DTI borrowers generally repay worse than lower DTI borrowers.
- 60-month loans perform worse than 36-month loans.
- Small business loans need closer monitoring.
- Exposure is concentrated in grades C, B, and D, especially for debt consolidation and credit card loans.
- Active delinquent loans in grades C, D, and E are the strongest recovery priority.

## Business Recommendations

- Prioritize active delinquent loans in grades C, D, and E.
- Monitor risky combinations such as lower grade, high interest rate, high DTI, and 60-month term.
- Use different collection actions based on delinquency stage.
- Review affordability more carefully for high interest loans.
- Track high-exposure purposes such as debt consolidation and credit card separately.

## How to Run

1. Clone the repository.

```bash
git clone https://github.com/AbhayNataraj/loan-repayment-analysis.git
cd loan-repayment-analysis
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Open the notebook.

```bash
jupyter notebook UCUCI_Loan_Repayment_Analysis_Redesigned.ipynb
```

4. Run the notebook cells from top to bottom.

The notebook downloads the dataset automatically before loading it into Pandas.

## Final Conclusion

The analysis shows that UCUCI Bank should combine historical repayment learning with active-loan monitoring. Closed-loan behavior highlights borrower and loan characteristics linked to repayment performance, while active-loan analysis identifies where current money exposure is most urgent.

The most practical recovery focus is active delinquent loans in grades C, D, and E, especially when combined with high interest rates, high DTI, longer terms, or riskier loan purposes.
