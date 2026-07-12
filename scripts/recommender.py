from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
scheme = pd.read_csv(BASE_DIR / "data" / "processed" / "07_scheme_performance_clean.csv")

print("\nAvailable Risk Grades:")
print("- Low")
print("- Moderate")
print("- Moderately High")
print("- High")
print("- Very High")

risk = input("\nEnter your Risk Appetite: ").strip()

recommendations = (
    scheme[
        scheme["risk_grade"].str.lower() == risk.lower()
    ]
    .sort_values(
        by="sharpe_ratio",
        ascending=False
    )
    .head(3)
)

if recommendations.empty:
    print("\nNo funds found for the selected risk grade.")

else:
    print("\nTop 3 Recommended Funds\n")

    print(
        recommendations[
            [
                "scheme_name",
                "fund_house",
                "risk_grade",
                "sharpe_ratio",
                "return_3yr_pct"
            ]
        ].to_string(index=False)
    )