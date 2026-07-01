from __future__ import annotations

import csv
import re
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


FILE_ID = "1BS8azi6nWEXm0Zvo3nD7t3sWaZWt1Ny8"
RAW_FILE = Path("UCUCI_dataset.csv")
OUTPUT_DIR = Path("tableau_outputs")


COMPLETED_STATUS = ["Fully Paid", "Charged Off", "Default"]
ACTIVE_STATUS = ["Current", "In Grace Period", "Late (16-30 days)", "Late (31-120 days)"]
DELINQUENT_STATUS = ["In Grace Period", "Late (16-30 days)", "Late (31-120 days)"]


def download_google_drive_file(file_id: str, destination: Path) -> None:
    """Download a public Google Drive file without requiring gdown."""
    if destination.exists() and destination.stat().st_size > 0:
        print(f"Using existing raw file: {destination}")
        return

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    params = urllib.parse.urlencode({"export": "download", "id": file_id})
    url = f"https://drive.google.com/uc?{params}"

    with opener.open(url, timeout=60) as response:
        first_chunk = response.read(1024 * 1024)
        content_type = response.headers.get("Content-Type", "")
        text_preview = first_chunk.decode("utf-8", errors="ignore") if "text/html" in content_type else ""

    token = None
    match = re.search(r"confirm=([0-9A-Za-z_]+)", text_preview)
    if match:
        token = match.group(1)

    if token:
        params = urllib.parse.urlencode({"export": "download", "id": file_id, "confirm": token})
        url = f"https://drive.google.com/uc?{params}"
        first_chunk = b""

    with opener.open(url, timeout=60) as response, destination.open("wb") as handle:
        if first_chunk:
            handle.write(first_chunk)
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)

    print(f"Downloaded raw file: {destination} ({destination.stat().st_size:,} bytes)")


def clean_percent(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series
    return pd.to_numeric(series.astype(str).str.replace("%", "", regex=False).str.strip(), errors="coerce")


def clean_term(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.replace(" months", " months", regex=False)


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    result = numerator / denominator.replace({0: pd.NA})
    return result.astype("float64")


def add_bands(df: pd.DataFrame) -> pd.DataFrame:
    df["Interest Rate Band"] = pd.cut(
        df["int_rate"],
        bins=[0, 10, 15, 20, 25, 30, 100],
        labels=["<10%", "10-15%", "15-20%", "20-25%", "25-30%", "30%+"],
        include_lowest=True,
    )
    df["DTI Band"] = pd.cut(
        df["dti"],
        bins=[-0.01, 10, 20, 30, 40, 100, 100000],
        labels=["0-10", "10-20", "20-30", "30-40", "40-100", "100+"],
        include_lowest=True,
    )
    df["Annual Income Band"] = pd.cut(
        df["annual_inc"],
        bins=[-0.01, 25000, 50000, 75000, 100000, 150000, 250000, 1000000000],
        labels=["<=25K", "25K-50K", "50K-75K", "75K-100K", "100K-150K", "150K-250K", "250K+"],
        include_lowest=True,
    )
    df["Installment Band"] = pd.cut(
        df["installment"],
        bins=[-0.01, 200, 400, 600, 800, 1000, 50000],
        labels=["<=200", "200-400", "400-600", "600-800", "800-1000", "1000+"],
        include_lowest=True,
    )
    return df


def weighted_lrr(group: pd.DataFrame) -> float:
    funded = group["funded_amnt"].sum()
    if funded == 0:
        return float("nan")
    return group["total_pymnt"].sum() / funded * 100


def summary_by(df: pd.DataFrame, dimensions: list[str], output_name: str) -> None:
    summary = (
        df.groupby(dimensions, observed=False)
        .agg(
            Loans=("id", "count"),
            Funded_Amount=("funded_amnt", "sum"),
            Total_Repaid=("total_pymnt", "sum"),
            Outstanding_Principal=("out_prncp", "sum"),
            Recoveries=("recoveries", "sum"),
            Charged_Off_Rate=("Charged Off Flag", "mean"),
            Bad_Loan_Rate=("Bad Loan Flag", "mean"),
            Delinquency_Rate=("Delinquent Flag", "mean"),
            At_Risk_Outstanding=("At Risk Outstanding Principal", "sum"),
            Avg_Interest_Rate=("int_rate", "mean"),
        )
        .reset_index()
    )
    summary["LRR"] = summary["Total_Repaid"] / summary["Funded_Amount"].replace({0: pd.NA}) * 100
    for column in ["Charged_Off_Rate", "Bad_Loan_Rate", "Delinquency_Rate"]:
        summary[column] = summary[column] * 100
    summary["Funded_Crores"] = summary["Funded_Amount"] / 10_000_000
    summary["Outstanding_Crores"] = summary["Outstanding_Principal"] / 10_000_000
    summary["At_Risk_Outstanding_Crores"] = summary["At_Risk_Outstanding"] / 10_000_000
    summary.to_csv(OUTPUT_DIR / output_name, index=False, quoting=csv.QUOTE_MINIMAL)


def main() -> None:
    download_google_drive_file(FILE_ID, RAW_FILE)
    OUTPUT_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(RAW_FILE, low_memory=False)
    print(f"Loaded raw data: {df.shape[0]:,} rows, {df.shape[1]:,} columns")

    required_columns = [
        "id",
        "member_id",
        "loan_amnt",
        "funded_amnt",
        "term",
        "int_rate",
        "installment",
        "grade",
        "sub_grade",
        "emp_length",
        "home_ownership",
        "annual_inc",
        "verification_status",
        "issue_d",
        "loan_status",
        "purpose",
        "dti",
        "delinq_2yrs",
        "total_pymnt",
        "out_prncp",
        "recoveries",
        "last_pymnt_d",
        "last_pymnt_amnt",
    ]
    available_columns = [column for column in required_columns if column in df.columns]
    tableau = df[available_columns].copy()

    for column in ["loan_amnt", "funded_amnt", "installment", "annual_inc", "dti", "delinq_2yrs", "total_pymnt", "out_prncp", "recoveries", "last_pymnt_amnt"]:
        if column in tableau.columns:
            tableau[column] = pd.to_numeric(tableau[column], errors="coerce")

    tableau["int_rate"] = clean_percent(tableau["int_rate"])
    tableau["term"] = clean_term(tableau["term"])

    if "issue_d" in tableau.columns:
        tableau["Issue Date"] = pd.to_datetime(tableau["issue_d"], format="%b-%Y", errors="coerce")
        tableau["Issue Year"] = tableau["Issue Date"].dt.year
        tableau["Issue Month"] = tableau["Issue Date"].dt.to_period("M").astype(str)

    if "last_pymnt_d" in tableau.columns:
        tableau["Last Payment Date"] = pd.to_datetime(tableau["last_pymnt_d"], format="%b-%Y", errors="coerce")
        tableau["Last Payment Year"] = tableau["Last Payment Date"].dt.year
        tableau["Last Payment Month"] = tableau["Last Payment Date"].dt.to_period("M").astype(str)
        latest_payment_date = tableau["Last Payment Date"].max()
        month_delta = (
            (latest_payment_date.year - tableau["Last Payment Date"].dt.year) * 12
            + (latest_payment_date.month - tableau["Last Payment Date"].dt.month)
        )
        tableau["Months Since Last Payment"] = month_delta.where(tableau["Last Payment Date"].notna())
        tableau["Last Payment Recency Band"] = pd.cut(
            tableau["Months Since Last Payment"],
            bins=[-0.01, 1, 3, 6, 12, 24, 1200],
            labels=["0-1 month", "2-3 months", "4-6 months", "7-12 months", "13-24 months", "24+ months"],
            include_lowest=True,
        ).astype("object")
        tableau.loc[tableau["Last Payment Date"].isna(), "Last Payment Recency Band"] = "No payment date"

    tableau["LRR"] = safe_divide(tableau["total_pymnt"], tableau["funded_amnt"]) * 100
    tableau["Portfolio Type"] = "Other"
    tableau.loc[tableau["loan_status"].isin(COMPLETED_STATUS), "Portfolio Type"] = "Closed"
    tableau.loc[tableau["loan_status"].isin(ACTIVE_STATUS), "Portfolio Type"] = "Active"
    tableau["Closed Loan Flag"] = tableau["loan_status"].isin(COMPLETED_STATUS).astype(int)
    tableau["Active Loan Flag"] = tableau["loan_status"].isin(ACTIVE_STATUS).astype(int)
    tableau["Charged Off Flag"] = (tableau["loan_status"] == "Charged Off").astype(int)
    tableau["Bad Loan Flag"] = tableau["loan_status"].isin(["Charged Off", "Default"]).astype(int)
    tableau["Delinquent Flag"] = tableau["loan_status"].isin(DELINQUENT_STATUS).astype(int)
    tableau["At Risk Outstanding Principal"] = tableau["out_prncp"].where(tableau["Delinquent Flag"].eq(1), 0)
    tableau["Funded Amount Crores"] = tableau["funded_amnt"] / 10_000_000
    tableau["Outstanding Principal Crores"] = tableau["out_prncp"] / 10_000_000
    tableau["At Risk Outstanding Crores"] = tableau["At Risk Outstanding Principal"] / 10_000_000
    tableau["Practical Recovery Rate"] = safe_divide(tableau["recoveries"], tableau["funded_amnt"]) * 100
    tableau = add_bands(tableau)

    tableau["Risk Priority"] = "Monitor"
    high_risk = (
        (tableau["grade"].isin(["D", "E", "F", "G"]))
        | (tableau["int_rate"] > 15)
        | (tableau["dti"] > 30)
        | (tableau["term"].eq("60 months"))
        | (tableau["purpose"].isin(["small_business", "house", "moving", "renewable_energy"]))
        | (tableau["Delinquent Flag"].eq(1))
    )
    tableau.loc[high_risk, "Risk Priority"] = "High Priority"
    tableau.loc[tableau["Delinquent Flag"].eq(1), "Risk Priority"] = "Immediate Recovery"

    tableau_file = OUTPUT_DIR / "ucuci_tableau_loan_level.csv"
    tableau.to_csv(tableau_file, index=False, quoting=csv.QUOTE_MINIMAL)

    closed = tableau[tableau["Portfolio Type"].eq("Closed")].copy()
    active = tableau[tableau["Portfolio Type"].eq("Active")].copy()
    summary_by(closed, ["grade"], "closed_lrr_by_grade.csv")
    summary_by(closed, ["Interest Rate Band"], "closed_lrr_by_interest_band.csv")
    summary_by(closed, ["DTI Band"], "closed_lrr_by_dti_band.csv")
    summary_by(closed, ["Annual Income Band"], "closed_lrr_by_income_band.csv")
    summary_by(closed, ["Annual Income Band", "DTI Band"], "closed_lrr_by_income_dti.csv")
    summary_by(closed, ["sub_grade"], "closed_lrr_by_sub_grade.csv")
    summary_by(closed, ["term"], "closed_lrr_by_term.csv")
    summary_by(closed, ["purpose"], "closed_lrr_by_purpose.csv")
    summary_by(closed, ["grade", "term"], "closed_lrr_by_grade_term.csv")
    summary_by(active, ["grade"], "active_risk_by_grade.csv")
    summary_by(active, ["sub_grade"], "active_risk_by_sub_grade.csv")
    summary_by(active, ["Interest Rate Band"], "active_risk_by_interest_band.csv")
    summary_by(active, ["Last Payment Recency Band"], "active_risk_by_last_payment_recency.csv")
    summary_by(active, ["purpose"], "active_risk_by_purpose.csv")
    summary_by(active, ["grade", "purpose"], "active_risk_by_grade_purpose.csv")

    kpis = {
        "Total Loans Issued": len(tableau),
        "Closed Loans": int(tableau["Closed Loan Flag"].sum()),
        "Active Loans": int(tableau["Active Loan Flag"].sum()),
        "Overall Completed Loan LRR": weighted_lrr(closed),
        "Active Loan Delinquency Rate": active["Delinquent Flag"].mean() * 100,
        "Default Rate - Charged Off Only": (tableau["loan_status"].eq("Charged Off").mean() * 100),
        "Charged Off + Default Rate": tableau["Bad Loan Flag"].mean() * 100,
        "Average Interest Rate": tableau["int_rate"].mean(),
        "Practical Recovery Rate": (tableau.loc[tableau["loan_status"].eq("Charged Off"), "recoveries"].sum() / tableau.loc[tableau["loan_status"].eq("Charged Off"), "funded_amnt"].sum() * 100),
        "Active Outstanding Principal": active["out_prncp"].sum(),
        "At Risk Outstanding Principal": active["At Risk Outstanding Principal"].sum(),
    }
    pd.DataFrame({"Metric": kpis.keys(), "Value": kpis.values()}).to_csv(OUTPUT_DIR / "dashboard_kpi_reference.csv", index=False)

    print(f"Created Tableau loan-level file: {tableau_file} ({tableau_file.stat().st_size:,} bytes)")
    print(f"Created summary/reference files in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
