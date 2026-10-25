import json
import os

import pandas as pd


def export_dashboard_data(output_file="web/public/benchmark-data.json"):
    sources = {
        "runs": "results/benchmark_runs.csv",
        "seedSummary": "results/benchmark_seed_summary.csv",
        "summary": "results/benchmark_summary.csv",
        "validation": "results/model_validation_by_seed.csv",
    }
    payload = {
        key: json.loads(pd.read_csv(path).to_json(orient="records"))
        for key, path in sources.items()
    }
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
    return output_file


if __name__ == "__main__":
    print(f"Exported dashboard data to {export_dashboard_data()}")
