import argparse
import os

import pandas as pd

from src.dataset import generate_dataset
from src.evaluate import evaluate
from src.export_dashboard_data import export_dashboard_data
from src.generate_programs import generate_corpus
from src.train_model import train_model


def run_benchmarks(seeds=(7, 42, 2026), total_programs=300,
                   train_programs=240):
    all_results = []
    validation_results = []

    for seed in seeds:
        print(f"\n=== Running seed {seed} ===", flush=True)
        run_dir = os.path.join("data", "benchmarks", f"seed_{seed}")
        corpus_dir = os.path.join(run_dir, "generated")
        train_dir, test_dir = generate_corpus(
            seed=seed,
            total_programs=total_programs,
            train_programs=train_programs,
            output_dir=corpus_dir,
        )

        data_file = os.path.join(run_dir, "spill_cost_dataset.csv")
        model_file = os.path.join(run_dir, "spill_cost_model.pkl")
        result_file = os.path.join(run_dir, "evaluation.csv")
        training_files = sorted(
            os.path.join(train_dir, name)
            for name in os.listdir(train_dir)
            if name.endswith(".tac")
        )

        generate_dataset(training_files, data_file)
        validation_results.append(train_model(data_file, model_file, seed))
        all_results.append(evaluate(model_file, test_dir, result_file, seed))

    runs = pd.concat(all_results, ignore_index=True)
    validation = pd.DataFrame(validation_results)
    per_seed = runs.groupby(["Seed", "Registers"]).agg({
        "Classical Spills": "mean",
        "ML Spills": "mean",
        "Classical Added TAC Instructions": "mean",
        "ML Added TAC Instructions": "mean",
        "Classical Time (ms)": "mean",
        "ML Time (ms)": "mean",
        "Classical Valid": "all",
        "ML Valid": "all",
        "Classical Rewrite Semantics Valid": "all",
        "ML Rewrite Semantics Valid": "all",
    }).reset_index()

    comparisons = [
        ("Average spills", "Classical Spills", "ML Spills"),
        ("Added TAC instructions", "Classical Added TAC Instructions", "ML Added TAC Instructions"),
        ("Allocator time (ms)", "Classical Time (ms)", "ML Time (ms)"),
    ]
    summary_rows = []
    for registers in sorted(per_seed["Registers"].unique()):
        subset = per_seed[per_seed["Registers"] == registers]
        for label, classical_col, ml_col in comparisons:
            summary_rows.append({
                "Registers": registers,
                "Measure": label,
                "Classical Mean Across Seeds": subset[classical_col].mean(),
                "Classical SD Across Seeds": subset[classical_col].std(ddof=1),
                "ML Mean Across Seeds": subset[ml_col].mean(),
                "ML SD Across Seeds": subset[ml_col].std(ddof=1),
            })

    summary = pd.DataFrame(summary_rows).round(4)
    os.makedirs("results", exist_ok=True)
    runs.to_csv("results/benchmark_runs.csv", index=False)
    per_seed.to_csv("results/benchmark_seed_summary.csv", index=False)
    summary.to_csv("results/benchmark_summary.csv", index=False)
    validation.to_csv("results/model_validation_by_seed.csv", index=False)
    export_dashboard_data()

    print("\n=== Cross-seed summary (mean and sample SD) ===")
    print(summary.to_string(index=False))
    print("\nAllocation valid across all runs:",
          bool(per_seed[["Classical Valid", "ML Valid"]].all().all()))
    print("Rewritten outputs valid across all runs:",
          bool(per_seed[["Classical Rewrite Semantics Valid",
                         "ML Rewrite Semantics Valid"]].all().all()))
    print("\nSaved benchmark outputs under results/.")
    return runs, per_seed, summary, validation


def main():
    parser = argparse.ArgumentParser(
        description="Run seeded held-out register-allocation benchmarks"
    )
    parser.add_argument(
        "--seeds", nargs="+", type=int, default=[7, 42, 2026]
    )
    parser.add_argument("--total-programs", type=int, default=300)
    parser.add_argument("--train-programs", type=int, default=240)
    args = parser.parse_args()
    run_benchmarks(args.seeds, args.total_programs, args.train_programs)


if __name__ == "__main__":
    main()
